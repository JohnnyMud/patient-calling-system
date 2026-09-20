#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=dev_lib.sh
source "${SCRIPT_DIR}/dev_lib.sh"
init_dev_env

BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
BACKEND_APP="${BACKEND_APP:-main:app}"

echo "Starting backend on ${BACKEND_HOST}:${BACKEND_PORT} (${BACKEND_APP})"
exec uvicorn "${BACKEND_APP}" --host "${BACKEND_HOST}" --port "${BACKEND_PORT}" --reload
