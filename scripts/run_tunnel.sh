#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=dev_lib.sh
source "${SCRIPT_DIR}/dev_lib.sh"
init_dev_env

BACKEND_PORT="${BACKEND_PORT:-8000}"
TUNNEL_TARGET_URL="${TUNNEL_TARGET_URL:-http://localhost:${BACKEND_PORT}}"

echo "Starting Cloudflare tunnel -> ${TUNNEL_TARGET_URL}"
exec cloudflared tunnel --url "${TUNNEL_TARGET_URL}"
