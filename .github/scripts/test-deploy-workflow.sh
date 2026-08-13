#!/usr/bin/env bash
set -euo pipefail

workflow=.github/workflows/deploy.yml

# Keep these as executable trust-boundary regressions, independent of display
# names and comments. The first checkout must be main; the second must be the
# SHA emitted by the trusted resolver, which is also the image tag.
grep -qF 'ref: refs/heads/main' "$workflow"
grep -qF 'ref: ${{ steps.image.outputs.sha }}' "$workflow"
grep -qF 'EXPECTED_SHA: ${{ steps.image.outputs.sha }}' "$workflow"
grep -qF 'IMAGE: ${{ steps.image.outputs.image }}' "$workflow"
grep -qF 'BASTION_HOST: ${{ secrets.BASTION_HOST }}' "$workflow"
grep -qF 'BASTION_KNOWN_HOSTS: ${{ secrets.BASTION_KNOWN_HOSTS }}' "$workflow"
grep -qF 'BASTION_SSH_KEY: ${{ secrets.BASTION_SSH_KEY }}' "$workflow"
grep -qF 'DEPLOY_KNOWN_HOSTS: ${{ secrets.DEPLOY_KNOWN_HOSTS }}' "$workflow"
! grep -q 'ssh-keyscan' "$workflow"

test_root=$(mktemp -d /tmp/ailtir-mcp-ssh-config-test.XXXXXX)
trap 'rm -rf -- "$test_root"' EXIT INT TERM HUP
touch "$test_root/known_hosts" "$test_root/bastion_key" "$test_root/deploy_key"
BASTION_HOST=192.0.2.10 BASTION_USER=runner DEPLOY_HOST=192.0.2.20 \
	.github/scripts/write-deploy-ssh-config.sh "$test_root/config" "$test_root/known_hosts" \
	"$test_root/bastion_key" "$test_root/deploy_key"

bastion=$(ssh -G -F "$test_root/config" ailtir-bastion 2>/dev/null)
target=$(ssh -G -F "$test_root/config" ailtir-box 2>/dev/null)
grep -qFx 'hostname 192.0.2.10' <<<"$bastion"
grep -qFx 'user runner' <<<"$bastion"
grep -qFx 'identitiesonly yes' <<<"$bastion"
grep -qFx 'stricthostkeychecking true' <<<"$bastion"
grep -qFx "identityfile $test_root/bastion_key" <<<"$bastion"
! grep -qFx "identityfile $test_root/deploy_key" <<<"$bastion"
grep -qFx "userknownhostsfile $test_root/known_hosts" <<<"$bastion"
grep -qFx 'hostname 192.0.2.20' <<<"$target"
grep -qFx 'user root' <<<"$target"
grep -qFx 'identitiesonly yes' <<<"$target"
grep -qFx 'stricthostkeychecking true' <<<"$target"
grep -qFx "identityfile $test_root/deploy_key" <<<"$target"
! grep -qFx "identityfile $test_root/bastion_key" <<<"$target"
grep -qFx 'proxyjump ailtir-bastion' <<<"$target"
grep -qFx "userknownhostsfile $test_root/known_hosts" <<<"$target"

main_line=$(grep -nF 'ref: refs/heads/main' "$workflow" | cut -d: -f1)
resolved_line=$(grep -nF 'ref: ${{ steps.image.outputs.sha }}' "$workflow" | cut -d: -f1)
preserve_line=$(grep -nF 'name: Preserve trusted SSH helper' "$workflow" | cut -d: -f1)
sync_line=$(grep -nF 'name: Sync production definition and deploy exact image' "$workflow" | cut -d: -f1)
((main_line < preserve_line && preserve_line < resolved_line && resolved_line < sync_line))
grep -qF '"$RUNNER_TEMP/write-deploy-ssh-config.sh" "$config"' "$workflow"

echo 'deployment workflow trust-boundary tests passed'
