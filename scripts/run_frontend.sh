#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=dev_lib.sh
source "${SCRIPT_DIR}/dev_lib.sh"
init_dev_env

FRONTEND_DIR="${FRONTEND_DIR:-frontend}"

cd "${REPO_ROOT}/${FRONTEND_DIR}"
echo "Starting frontend from ${FRONTEND_DIR}"
exec npm run dev
