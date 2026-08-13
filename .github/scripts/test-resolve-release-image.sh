#!/usr/bin/env bash
set -euo pipefail

script_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
test_root=$(mktemp -d /tmp/ailtir-mcp-release-test.XXXXXX)
mkdir -p "$test_root/bin"
release_tag=v9999.0.0
git tag "$release_tag" HEAD
trap 'git tag -d "$release_tag" >/dev/null 2>&1 || true; rm -rf -- "$test_root"' EXIT INT TERM HUP
cat >"$test_root/bin/gh" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "${RELEASE_JSON:?}"
EOF
chmod 0755 "$test_root/bin/gh"

run() {
	PATH="$test_root/bin:$PATH" GITHUB_REPOSITORY=Team-Ailtir/ailtir-mcp \
		MAIN_REF=HEAD RELEASE_JSON=$1 "$script_dir/resolve-release-image.sh" "$2"
}

published='{"draft":false,"prerelease":false,"published_at":"2026-08-12T00:00:00Z"}'
[[ $(run "$published" "$release_tag") == "$(git rev-list -n 1 "${release_tag}^{commit}")" ]]

for invalid in 0123456789abcdef0123456789abcdef01234567 v1.2.3-rc.1 latest; do
	! run "$published" "$invalid" >/dev/null 2>&1
done
! run '{"draft":false,"prerelease":true,"published_at":"2026-08-12T00:00:00Z"}' "$release_tag" >/dev/null 2>&1
! run '{"draft":true,"prerelease":false,"published_at":null}' "$release_tag" >/dev/null 2>&1

echo 'release resolution tests passed'
