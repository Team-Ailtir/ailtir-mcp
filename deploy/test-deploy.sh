#!/usr/bin/env bash
set -euo pipefail

repo_dir=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
test_root=$(mktemp -d /tmp/ailtir-mcp-deploy-test.XXXXXX)
trap 'rm -rf -- "$test_root"' EXIT INT TERM HUP

make_fixture() {
	local name=$1 root
	root="$test_root/$name"
	mkdir -p "$root/app/releases" "$root/core/caddy.d" "$root/bundle" "$root/bin"
	cp "$repo_dir/deploy/"{docker-compose.yml,ailtir-mcp.caddy,deploy.sh,authenticated-deploy.sh} "$root/bundle/"
	install -m 0600 /dev/null "$root/app/.env"
	cat >"$root/bin/docker" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >>"$DOCKER_LOG"
case "$1" in
	network|pull|rm) exit 0 ;;
	inspect)
		if [[ "${TEST_HEALTHY:-}" == true ]]; then printf 'healthy\n'; else printf 'unhealthy\n'; fi
		exit 0
		;;
	ps) printf 'failed-container\n'; exit 0 ;;
	compose)
		if [[ " $* " == *" config "* ]]; then exit 0; fi
		if [[ " $* " == *" ps -q ailtir-mcp "* ]]; then printf 'candidate-container\n'; exit 0; fi
		if [[ " $* " == *" up -d --no-deps ailtir-mcp "* ]]; then
			if [[ " $* " == *"/old/docker-compose.yml"* ]]; then exit 0; fi
			if [[ "${TEST_UP_SUCCEEDS:-}" == true ]]; then exit 0; fi
			exit 1
		fi
		;;
esac
exit 0
EOF
	chmod 0755 "$root/bin/docker"
	cat >"$root/bin/curl" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
count=0
[[ ! -f "$CURL_COUNT" ]] || count=$(<"$CURL_COUNT")
count=$((count + 1))
printf '%s\n' "$count" >"$CURL_COUNT"
printf '%s\n' "$*" >>"$CURL_LOG"
failures=${CURL_FAILURES_BEFORE_SUCCESS:--1}
((failures >= 0 && count > failures))
EOF
	chmod 0755 "$root/bin/curl"
	printf '%s\n' "$root"
}

run_failure() {
	local root=$1 id=$2
	set +e
	PATH="$root/bin:$PATH" DOCKER_LOG="$root/docker.log" CURL_COUNT="$root/curl.count" \
		CURL_LOG="$root/curl.log" APP_DIR="$root/app" CORE_DIR="$root/core" \
		PUBLIC_HEALTH_TIMEOUT_SECONDS=2 PUBLIC_HEALTH_RETRY_DELAY_SECONDS=0 PUBLIC_HEALTH_ATTEMPTS=3 \
		"$root/bundle/deploy.sh" \
		ghcr.io/team-ailtir/ailtir-mcp:0123456789abcdef0123456789abcdef01234567 "$id" "$root/bundle" \
		>"$root/output.log" 2>&1
	local status=$?
	set -e
	[[ $status -ne 0 ]]
}

run_success() {
	local root=$1 id=$2
	PATH="$root/bin:$PATH" DOCKER_LOG="$root/docker.log" CURL_COUNT="$root/curl.count" \
		CURL_LOG="$root/curl.log" APP_DIR="$root/app" CORE_DIR="$root/core" \
		TEST_UP_SUCCEEDS=true TEST_HEALTHY=true CURL_FAILURES_BEFORE_SUCCESS=1 \
		PUBLIC_HEALTH_TIMEOUT_SECONDS=5 PUBLIC_HEALTH_RETRY_DELAY_SECONDS=0 PUBLIC_HEALTH_ATTEMPTS=3 \
		"$root/bundle/deploy.sh" \
		ghcr.io/team-ailtir/ailtir-mcp:0123456789abcdef0123456789abcdef01234567 "$id" "$root/bundle" \
		>"$root/output.log" 2>&1
}

first=$(make_fixture first)
run_failure "$first" 100-1
! grep -q '^AILTIR_MCP_IMAGE=' "$first/app/.env"
grep -q '^rm -f failed-container$' "$first/docker.log"
[[ ! -e "$first/app/current" ]]

upgrade=$(make_fixture upgrade)
mkdir -p "$upgrade/app/releases/old"
cp "$upgrade/bundle/docker-compose.yml" "$upgrade/app/releases/old/docker-compose.yml"
printf 'old helper\n' >"$upgrade/app/releases/old/deploy.sh"
ln -s "$upgrade/app/releases/old" "$upgrade/app/current"
printf 'AILTIR_MCP_IMAGE=ghcr.io/team-ailtir/ailtir-mcp:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n' >>"$upgrade/app/.env"
run_failure "$upgrade" 101-1
[[ $(readlink -f "$upgrade/app/current") == "$upgrade/app/releases/old" ]]
grep -q '^old helper$' "$upgrade/app/releases/old/deploy.sh"
grep -q '^AILTIR_MCP_IMAGE=ghcr.io/team-ailtir/ailtir-mcp:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa$' "$upgrade/app/.env"
grep -q "$upgrade/app/releases/old/docker-compose.yml.*up -d --no-deps ailtir-mcp" "$upgrade/docker.log"

transient=$(make_fixture transient)
run_success "$transient" 102-1
[[ $(<"$transient/curl.count") == 2 ]]
grep -q -- '--connect-timeout 3 --max-time' "$transient/curl.log"
[[ -L "$transient/app/current" ]]

exhausted=$(make_fixture exhausted)
mkdir -p "$exhausted/app/releases/old"
cp "$exhausted/bundle/docker-compose.yml" "$exhausted/app/releases/old/docker-compose.yml"
ln -s "$exhausted/app/releases/old" "$exhausted/app/current"
printf 'AILTIR_MCP_IMAGE=ghcr.io/team-ailtir/ailtir-mcp:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n' >>"$exhausted/app/.env"
TEST_UP_SUCCEEDS=true TEST_HEALTHY=true run_failure "$exhausted" 103-1
[[ $(<"$exhausted/curl.count") == 3 ]]
[[ $(readlink -f "$exhausted/app/current") == "$exhausted/app/releases/old" ]]
grep -q "$exhausted/app/releases/old/docker-compose.yml.*up -d --no-deps ailtir-mcp" "$exhausted/docker.log"

echo 'deployment rollback tests passed'
