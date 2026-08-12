#!/usr/bin/env bash
# Refuses when a GHCR package is anonymously pullable, and refuses when that cannot be established.
#
# It measures anonymous pullability rather than the packages REST API's `visibility` field: that is
# the property that actually matters (nobody without credentials may pull an internal service
# image), it is what an attacker would run, and it needs no token scope at all, unlike
# GET /orgs/{org}/packages/container/{name}, which is documented for read:packages and not for
# GITHUB_TOKEN.
#
# Measured against ghcr.io on 2026-08-12: the anonymous token endpoint answers 200 with a token for
# a publicly pullable package (actions/actions-runner, homebrew/core/git) and 403 DENIED for one
# that is private or does not exist (team-ailtir/api-mcp, team-ailtir/ailtir-mcp, and a name made
# up on the spot). 401 has never been observed and is NOT accepted: a uniform "authentication
# required" answer is what an intercepting proxy, an egress throttle, or a change at ghcr.io looks
# like, and accepting it would report every package as safe.
#
# Two caps, stated rather than implied. It does not distinguish private from absent, which is
# correct for this question (nothing that does not exist is exposed) but is NOT a test of
# existence, so it cannot notice that it has been aimed at the wrong package: the caller is
# responsible for passing the same name it publishes. And it says nothing about who inside the org
# can pull.
set -euo pipefail

pkg="${1:?usage: ghcr-not-public.sh <owner>/<package>}"

# A package known to be public, asked FIRST. Without it, anything that makes the endpoint answer
# every request the same way turns this script into an unconditional pass that still prints ok.
control='homebrew/core/git'

# The response body is discarded rather than kept: on a 200 it carries a bearer token, which
# Actions has no way to mask, and every branch below is actionable from the status alone.
status_for() {
	curl -sS --connect-timeout 10 --max-time 30 -o /dev/null -w '%{http_code}' \
		"https://ghcr.io/token?service=ghcr.io&scope=repository:${1}:pull"
}

if ! control_status="$(status_for "$control")" || [ "$control_status" != 200 ]; then
	echo "could not establish visibility of ghcr.io/${pkg}: the public control package ${control}" >&2
	echo "answered HTTP ${control_status:-<request failed>} rather than 200, so a refusal from this" >&2
	echo "endpoint no longer means what this script reads it to mean." >&2
	exit 1
fi

if ! status="$(status_for "$pkg")"; then
	echo "could not establish visibility of ghcr.io/${pkg}: the request to ghcr.io failed" >&2
	exit 1
fi

case "$status" in
403)
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
	exit 1
	;;
esac
