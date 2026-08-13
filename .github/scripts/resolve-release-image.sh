#!/usr/bin/env bash
set -euo pipefail

release_tag="${1:?usage: resolve-release-image.sh <published-vX.Y.Z-tag>}"
repository="${GITHUB_REPOSITORY:?GITHUB_REPOSITORY must be set}"
main_ref=${MAIN_REF:-origin/main}

if [[ ! "$release_tag" =~ ^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$ ]]; then
	echo "refusing non-stable-semver release tag: $release_tag" >&2
	exit 1
fi
release=$(gh api "repos/${repository}/releases/tags/${release_tag}")
if [[ "$(jq -r '.draft or .prerelease or (.published_at == null)' <<<"$release")" != false ]]; then
	echo "release $release_tag is not a published, stable release" >&2
	exit 1
fi

sha=$(git rev-list -n 1 "${release_tag}^{commit}")
git cat-file -e "${sha}^{commit}"
git merge-base --is-ancestor "$sha" "$main_ref" || {
	echo "$sha is not part of main" >&2
	exit 1
}

printf '%s\n' "$sha"
