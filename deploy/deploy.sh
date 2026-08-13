#!/usr/bin/env bash
# Installs one immutable ailtir-mcp image and restores the complete prior release on failure.
set -euo pipefail

image="${1:?usage: deploy.sh <image> <deployment-id> <staged-bundle>}"
deployment_id="${2:?usage: deploy.sh <image> <deployment-id> <staged-bundle>}"
bundle_dir="${3:?usage: deploy.sh <image> <deployment-id> <staged-bundle>}"
app_dir=${APP_DIR:-/opt/ailtir-mcp}
core_dir=${CORE_DIR:-/opt/ailtir}
env_file="$app_dir/.env"
releases_dir="$app_dir/releases"
current_link="$app_dir/current"
live_caddy="$core_dir/caddy.d/ailtir-mcp.caddy"
health_url=${HEALTH_URL:-https://mcp.62.238.51.124.sslip.io/ailtir-mcp/health}
public_health_timeout=${PUBLIC_HEALTH_TIMEOUT_SECONDS:-45}
public_health_delay=${PUBLIC_HEALTH_RETRY_DELAY_SECONDS:-2}
public_health_attempts=${PUBLIC_HEALTH_ATTEMPTS:-21}

if [[ ! "$image" =~ ^ghcr\.io/team-ailtir/ailtir-mcp:([0-9a-f]{40})$ ]]; then
	echo "refusing non-immutable ailtir-mcp image: $image" >&2
	exit 1
fi
sha=${BASH_REMATCH[1]}
if [[ ! "$deployment_id" =~ ^[0-9]+-[0-9]+$ ]]; then
	echo "refusing invalid deployment id: $deployment_id" >&2
	exit 1
fi
for file in docker-compose.yml ailtir-mcp.caddy deploy.sh authenticated-deploy.sh; do
	[[ -f "$bundle_dir/$file" ]] || {
		echo "staged deployment is missing $file" >&2
		exit 1
	}
done
bash -n "$bundle_dir/deploy.sh" "$bundle_dir/authenticated-deploy.sh"
if ! docker network inspect ailtir-ingress >/dev/null 2>&1; then
	echo "ailtir-ingress does not exist; deploy the ailtir-core ingress bridge first" >&2
	exit 1
fi
if [[ ! -f "$env_file" ]]; then
	install -m 0600 /dev/null "$env_file"
fi
[[ -d "$core_dir/caddy.d" ]] || {
	echo "the shared Caddy import directory is missing" >&2
	exit 1
}

release="$releases_dir/$sha-$deployment_id"
release_temp=$(mktemp -d "$releases_dir/.release.XXXXXX")
env_backup=$(mktemp "$app_dir/.env.backup.XXXXXX")
caddy_backup=$(mktemp "$app_dir/.caddy.backup.XXXXXX")
cleanup() {
	if [[ -n "$release_temp" ]]; then
		rm -rf -- "$release_temp"
	fi
	rm -f "$env_backup" "$caddy_backup"
}
trap cleanup EXIT INT TERM HUP
install -m 0644 "$bundle_dir/docker-compose.yml" "$release_temp/docker-compose.yml"
install -m 0644 "$bundle_dir/ailtir-mcp.caddy" "$release_temp/ailtir-mcp.caddy"
install -m 0755 "$bundle_dir/deploy.sh" "$release_temp/deploy.sh"
install -m 0755 "$bundle_dir/authenticated-deploy.sh" "$release_temp/authenticated-deploy.sh"

previous_release=
if [[ -L "$current_link" ]]; then
	previous_release=$(readlink -f "$current_link")
	[[ -f "$previous_release/docker-compose.yml" ]] || {
		echo "current release link has no Compose definition" >&2
		exit 1
	}
fi
previous_image=$(sed -n 's/^AILTIR_MCP_IMAGE=//p' "$env_file" | tail -1)
if [[ -n "$previous_image" && -z "$previous_release" ]]; then
	echo "an image is pinned but no versioned current release exists; refusing unsafe upgrade" >&2
	exit 1
fi

cp "$env_file" "$env_backup"
chmod 0600 "$env_backup"
had_caddy=false
if [[ -f "$live_caddy" ]]; then
	cp "$live_caddy" "$caddy_backup"
	had_caddy=true
fi

candidate_compose=(docker compose --project-directory "$app_dir" --env-file "$env_file" -f "$release_temp/docker-compose.yml")
AILTIR_MCP_IMAGE="$image" "${candidate_compose[@]}" config --quiet
mv "$release_temp" "$release"
release_temp=
candidate_compose=(docker compose --project-directory "$app_dir" --env-file "$env_file" -f "$release/docker-compose.yml")

write_image_pin() {
	local selected=$1 temp
	temp=$(mktemp "$app_dir/.env.new.XXXXXX")
	awk -v image="$selected" '
		BEGIN { replaced = 0 }
		/^AILTIR_MCP_IMAGE=/ {
			if (!replaced) print "AILTIR_MCP_IMAGE=" image
			replaced = 1
			next
		}
		{ print }
		END { if (!replaced) print "AILTIR_MCP_IMAGE=" image }
	' "$env_file" >"$temp"
	chmod 0600 "$temp"
	mv "$temp" "$env_file"
}

wait_healthy() {
	local compose_name=$1 container status
	shift
	container=$("$@" ps -q ailtir-mcp)
	[[ -n "$container" ]] || return 1
	for _ in $(seq 1 45); do
		status=$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$container")
		[[ "$status" == healthy ]] && return 0
		[[ "$status" == unhealthy ]] && return 1
		sleep 2
	done
	echo "$compose_name did not become healthy" >&2
	return 1
}

remove_failed_first_deploy() {
	local -a containers
	mapfile -t containers < <(docker ps -aq \
		--filter label=com.docker.compose.project=ailtir-mcp \
		--filter label=com.docker.compose.service=ailtir-mcp)
	if ((${#containers[@]})); then
		docker rm -f "${containers[@]}"
	fi
}

restore_service() {
	cp "$env_backup" "$env_file"
	chmod 0600 "$env_file"
	if [[ -n "$previous_release" ]]; then
		local previous_compose=(docker compose --project-directory "$app_dir" --env-file "$env_file" -f "$previous_release/docker-compose.yml")
		docker pull "$previous_image"
		"${previous_compose[@]}" up -d --no-deps ailtir-mcp
		wait_healthy previous "${previous_compose[@]}" || echo "warning: previous ailtir-mcp release did not recover healthy" >&2
	else
		# Compose cannot interpolate a pin that did not exist before the first deploy.
		remove_failed_first_deploy
	fi
}

restore_caddy() {
	if $had_caddy; then
		install -m 0644 "$caddy_backup" "$live_caddy"
	else
		rm -f "$live_caddy"
	fi
	(
		cd "$core_dir"
		docker compose exec -T caddy caddy reload --config /etc/caddy/Caddyfile
	) || echo "warning: Caddy did not reload the restored configuration" >&2
}

activate_release() {
	local link_temp="$app_dir/.current.$deployment_id"
	ln -s "$release" "$link_temp"
	mv -Tf "$link_temp" "$current_link"
}

wait_public_health() {
	local attempt deadline remaining request_timeout
	deadline=$((SECONDS + public_health_timeout))
	for ((attempt = 1; attempt <= public_health_attempts && SECONDS < deadline; attempt++)); do
		remaining=$((deadline - SECONDS))
		request_timeout=$((remaining < 5 ? remaining : 5))
		if curl --fail --silent --show-error --connect-timeout 3 --max-time "$request_timeout" \
			"$health_url" >/dev/null; then
			return 0
		fi
		((SECONDS >= deadline)) && break
		sleep "$public_health_delay"
	done
	return 1
}

docker pull "$image"
write_image_pin "$image"
if ! "${candidate_compose[@]}" up -d --no-deps ailtir-mcp || ! wait_healthy candidate "${candidate_compose[@]}"; then
	echo "ailtir-mcp failed to become healthy; restoring the previous release" >&2
	restore_service
	exit 1
fi

install -m 0644 "$release/ailtir-mcp.caddy" "$live_caddy"
if ! (
	cd "$core_dir"
	docker compose exec -T caddy caddy validate --config /etc/caddy/Caddyfile
	docker compose exec -T caddy caddy reload --config /etc/caddy/Caddyfile
); then
	echo "Caddy rejected the ailtir-mcp route; restoring the previous release" >&2
	restore_caddy
	restore_service
	exit 1
fi

if ! wait_public_health; then
	echo "public ailtir-mcp health check failed; restoring the previous release" >&2
	restore_caddy
	restore_service
	exit 1
fi

activate_release
echo "deployed $image from $release"
