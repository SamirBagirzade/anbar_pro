#!/usr/bin/env bash
set -euo pipefail

# Override via env vars if needed.
DEPLOY_HOST="${DEPLOY_HOST:-helind.ddns.net}"
DEPLOY_ROOT_USER="${DEPLOY_ROOT_USER:-root}"
DEPLOY_APP_USER="${DEPLOY_APP_USER:-anbar}"
DEPLOY_APP_DIR="${DEPLOY_APP_DIR:-anbar_pro}"

# Runs the same sequence you do manually:
#   ssh root@host
#   su - anbar
#   cd anbar_pro
#   ./deploy.sh
ssh -tt "${DEPLOY_ROOT_USER}@${DEPLOY_HOST}" \
  "su - ${DEPLOY_APP_USER} -c 'cd ~/${DEPLOY_APP_DIR} && ./deploy.sh'"
