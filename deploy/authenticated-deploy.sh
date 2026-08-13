#!/usr/bin/env bash
# Reads a short-lived GHCR token from stdin and never stores it in Docker's persistent config.
set -euo pipefail

image="${1:?usage: authenticated-deploy.sh <image> <ghcr-user> <deployment-id>}"
ghcr_user="${2:?usage: authenticated-deploy.sh <image> <ghcr-user> <deployment-id>}"
deployment_id="${3:?usage: authenticated-deploy.sh <image> <ghcr-user> <deployment-id>}"
bundle_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
IFS= read -r token
[[ -n "$token" ]] || {
	echo "no GHCR token received" >&2
	exit 1
}

docker_config=$(mktemp -d /tmp/ailtir-mcp-docker.XXXXXX)
trap 'rm -rf -- "$docker_config"' EXIT INT TERM HUP
printf '%s\n' "$token" | docker --config "$docker_config" login ghcr.io \
	--username "$ghcr_user" --password-stdin >/dev/null
unset token

DOCKER_CONFIG="$docker_config" "$bundle_dir/deploy.sh" "$image" "$deployment_id" "$bundle_dir"
