#!/usr/bin/env bash
set -euo pipefail

config=${1:?usage: write-deploy-ssh-config.sh <config> <known-hosts> <bastion-key> <deploy-key>}
known_hosts=${2:?usage: write-deploy-ssh-config.sh <config> <known-hosts> <bastion-key> <deploy-key>}
bastion_key=${3:?usage: write-deploy-ssh-config.sh <config> <known-hosts> <bastion-key> <deploy-key>}
deploy_key=${4:?usage: write-deploy-ssh-config.sh <config> <known-hosts> <bastion-key> <deploy-key>}

: "${BASTION_HOST:?BASTION_HOST must be set}"
: "${BASTION_USER:?BASTION_USER must be set}"
: "${DEPLOY_HOST:?DEPLOY_HOST must be set}"

cat >"$config" <<EOF
Host ailtir-bastion
  HostName $BASTION_HOST
  User $BASTION_USER
  IdentityFile $bastion_key
  IdentitiesOnly yes
  StrictHostKeyChecking yes
  UserKnownHostsFile $known_hosts

Host ailtir-box
  HostName $DEPLOY_HOST
  User root
  IdentityFile $deploy_key
  IdentitiesOnly yes
  StrictHostKeyChecking yes
  UserKnownHostsFile $known_hosts
  ProxyJump ailtir-bastion
EOF

chmod 0600 "$config"
