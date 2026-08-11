#!/usr/bin/env bash
# Refuses when a GHCR package is anonymously pullable, and refuses when that cannot be established.
#
# It measures anonymous pullability rather than the packages REST API's `visibility` field: that is
# the property that actually matters (nobody without credentials may pull an internal service
# image), it is what an attacker would run, and it needs no token scope at all, unlike
# GET /orgs/{org}/packages/container/{name}, which is documented for read:packages and not for
# GITHUB_TOKEN.
#
# Measured against ghcr.io on 2026-08-11: the anonymous token endpoint answers 200 with a token for
# a publicly pullable package (actions/actions-runner, homebrew/core/git) and 403 DENIED for one
# that is private or does not exist (team-ailtir/api-mcp, team-ailtir/ailtir-mcp, and a name made
# up on the spot).
#
# Two caps, stated rather than implied. It does not distinguish private from absent, which is
# correct for this question (nothing that does not exist is exposed) but is NOT a test of
# existence. And it says nothing about who inside the org can pull.
set -euo pipefail

pkg="${1:?usage: ghcr-not-public.sh <owner>/<package>}"
body="$(mktemp)"
trap 'rm -f "$body"' EXIT

if ! status="$(curl -sS -o "$body" -w '%{http_code}' \
	"https://ghcr.io/token?service=ghcr.io&scope=repository:${pkg}:pull")"; then
	echo "could not establish visibility of ghcr.io/${pkg}: the request to ghcr.io failed" >&2
	exit 1
fi

case "$status" in
401 | 403)
	echo "ok: ghcr.io/${pkg} is not anonymously pullable (token endpoint HTTP ${status})"
	;;
200)
	echo "REFUSED: ghcr.io/${pkg} is PUBLIC. Anyone can pull this image." >&2
	echo "Remedy: an org owner sets the package private at" >&2
	echo "  https://github.com/orgs/Team-Ailtir/packages/container/${pkg##*/}/settings" >&2
	exit 1
	;;
*)
	echo "could not establish visibility of ghcr.io/${pkg}: token endpoint HTTP ${status}" >&2
	cat "$body" >&2
	exit 1
	;;
esac
