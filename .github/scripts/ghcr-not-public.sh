#!/usr/bin/env bash
# Refuses when a GHCR package is anonymously pullable, and refuses when that cannot be established.
#
# It measures anonymous pullability rather than the packages REST API's `visibility` field: that is
# the property that actually matters (nobody without credentials may pull an internal service
# image), it is what an attacker would run, and it needs no token scope at all, unlike
# GET /orgs/{org}/packages/container/{name}, which is documented for read:packages and not for
# GITHUB_TOKEN.
#
# Measured against ghcr.io on 2026-08-12, across the first publish of ghcr.io/team-ailtir/ailtir-mcp
# and of ghcr.io/team-ailtir/api-mcp. The anonymous token endpoint answers:
#   200  publicly pullable                     homebrew/core/git, actions/actions-runner
#   401  exists, not anonymously pullable      both packages AFTER their first publish
#   403  no such package                       both packages BEFORE it, and a made-up name
# An earlier header read 403 as "private or does not exist". It was written when no team-ailtir
# package existed, so it only ever observed ABSENT, and it is now known false: a private package
# answers 401. Verified at the same time that 401 really is private and not a broken read: no
# anonymous token can be minted for either package, and the control's anonymous token is refused
# against both, while it fetches the control's own tag list.
#
# 401 and 403 are both accepted, and the positive control below is the whole reason that is safe.
# An earlier version accepted 401 with no control, and a review blocked it correctly: anything that
# answers every request alike (an intercepting proxy, an egress throttle, a change at ghcr.io)
# would turn this into an unconditional pass that still printed ok. The control answering 200 first
# is what rules that out. What that reasoning got wrong was the further inference that 401 carries
# no information. It means "exists, not anonymously pullable", which is the normal and safe state
# of every package published here, so refusing it reds the publish job on every run after the
# first, which is what it did.
#
# Two caps, stated rather than implied. The accepted statuses differ from each other and both are
# echoed, so the log says which one arrived, but neither is refused: this is NOT a test of
# existence, so it cannot notice that it has been aimed at the wrong package, because an absent one
# answers 403 and reads as ok. The caller is responsible for passing the same name it publishes.
# And it says nothing about who inside the org can pull.
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
	exit 1
	;;
esac
