#!/usr/bin/env bash
set -Eeuo pipefail

# Deploy the backend from the tracked main branch on the EC2 instance.
APP_DIR="${APP_DIR:-/var/www/Sector/sector-backend}"
BRANCH="${BRANCH:-main}"
SERVICE_NAME="${SERVICE_NAME:-sector-rocprompt-backend}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8000/health}"

cd "${APP_DIR}"

if [[ ! -d .git ]]; then
  echo "${APP_DIR} is not a Git repository."
  exit 1
fi

if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
  echo "Deployment stopped: tracked changes exist in ${APP_DIR}."
  echo "Commit or discard server-side changes before deploying."
  exit 1
fi

git fetch origin "${BRANCH}"
git checkout "${BRANCH}"
git reset --hard "origin/${BRANCH}"

if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv
fi

.venv/bin/python -m pip install --disable-pip-version-check --upgrade pip
.venv/bin/python -m pip install --disable-pip-version-check -r requirements.txt
.venv/bin/alembic upgrade head

sudo systemctl restart "${SERVICE_NAME}"
sudo systemctl is-active --quiet "${SERVICE_NAME}"
curl --fail --silent --show-error "${HEALTH_URL}"
echo
echo "Backend deployment complete."
