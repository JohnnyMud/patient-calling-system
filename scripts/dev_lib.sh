#!/usr/bin/env bash
# Shared helpers for local dev scripts. Sourced, not executed.

_DEV_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${_DEV_LIB_DIR}/.." && pwd)"
RUNTIME_DIR="${REPO_ROOT}/.runtime"

load_dotenv() {
  local env_file="${REPO_ROOT}/.env"
  if [[ -f "${env_file}" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "${env_file}"
    set +a
  fi
}

prepend_venv_path() {
  export PATH="${REPO_ROOT}/.venv/bin:${PATH}"
}

init_dev_env() {
  load_dotenv
  prepend_venv_path
  cd "${REPO_ROOT}"
}
