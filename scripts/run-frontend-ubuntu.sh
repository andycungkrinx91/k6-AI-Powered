#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
FRONTEND_DIR="${ROOT_DIR}/frontend"
FRONTEND_ENV_FILE="${FRONTEND_DIR}/.env"

CONFIG_ENV_FILE="${SCRIPT_DIR}/.env"

load_config_env_file() {
  if [[ ! -f "${CONFIG_ENV_FILE}" ]]; then
    return
  fi

  local owner_uid current_uid mode
  current_uid="$(id -u)"
  owner_uid="$(stat -c '%u' "${CONFIG_ENV_FILE}")"
  mode="$(stat -c '%a' "${CONFIG_ENV_FILE}")"

  if [[ "${owner_uid}" != "${current_uid}" && "${owner_uid}" != "0" ]]; then
    echo "Warning: skipping ${CONFIG_ENV_FILE} (owner must be current user or root)" >&2
    return
  fi

  if (( (8#${mode} & 0002) != 0 )); then
    echo "Warning: skipping ${CONFIG_ENV_FILE} (file is world-writable)" >&2
    return
  fi

  echo "Loading environment overrides from ${CONFIG_ENV_FILE}"
  set -a
  # shellcheck disable=SC1090
  source "${CONFIG_ENV_FILE}"
  set +a
}

load_config_env_file

FRONTEND_HOST="${FRONTEND_HOST:-0.0.0.0}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
FRONTEND_MODE="${FRONTEND_MODE:-start}" # dev|start

BACKEND_API_URL="${BACKEND_API_URL:-http://127.0.0.1:8000}"
BACKEND_API_KEY="${BACKEND_API_KEY:-}"

INSTALL_NODE_24="${INSTALL_NODE_24:-0}"

if [[ ! -d "${FRONTEND_DIR}" ]]; then
  echo "Error: frontend directory not found at ${FRONTEND_DIR}" >&2
  exit 1
fi

if [[ "$(id -u)" -eq 0 ]]; then
  SUDO=""
else
  SUDO="sudo"
fi

APT_UPDATED=0
apt_update() {
  if [[ "${APT_UPDATED}" -eq 0 ]]; then
    ${SUDO} apt-get update
    APT_UPDATED=1
  fi
}

install_prerequisites() {
  apt_update
  ${SUDO} apt-get install -y ca-certificates curl
}

node_major() {
  if ! command -v node >/dev/null 2>&1; then
    echo ""
    return
  fi
  node -p "process.versions.node.split('.')[0]" 2>/dev/null || true
}

install_node_24() {
  local major
  major="$(node_major)"
  if [[ "${major}" == "24" ]]; then
    echo "Node.js 24 already installed"
    return
  fi

  if [[ "${INSTALL_NODE_24}" != "1" ]]; then
    echo "Warning: Node.js 24.x is required by frontend/package.json (engines)." >&2
    echo "Install Node 24 yourself, or re-run with INSTALL_NODE_24=1." >&2
    return
  fi

  echo "Installing Node.js 24.x via NodeSource..."
  curl -fsSL https://deb.nodesource.com/setup_24.x | ${SUDO} -E bash -
  ${SUDO} apt-get install -y nodejs
}

ensure_pnpm() {
  if command -v pnpm >/dev/null 2>&1; then
    return
  fi

  if command -v corepack >/dev/null 2>&1; then
    corepack enable
    corepack prepare pnpm@9.0.0 --activate
    return
  fi

  echo "Error: pnpm not found and corepack not available." >&2
  echo "Install pnpm 9.x or install Node 24 (includes corepack)." >&2
  exit 1
}

ensure_frontend_env_file() {
  if [[ -f "${FRONTEND_ENV_FILE}" ]]; then
    echo "Using existing ${FRONTEND_ENV_FILE}"
    return
  fi

  cat >"${FRONTEND_ENV_FILE}" <<EOF
BACKEND_API_URL=${BACKEND_API_URL}
BACKEND_API_KEY=${BACKEND_API_KEY}
EOF

  echo "Created ${FRONTEND_ENV_FILE}"
}

run_frontend() {
  cd "${FRONTEND_DIR}"
  ensure_pnpm

  pnpm install

  if [[ "${FRONTEND_MODE}" == "dev" ]]; then
    exec pnpm dev -- --hostname "${FRONTEND_HOST}" --port "${FRONTEND_PORT}"
  fi

  pnpm build
  exec pnpm exec next start -H "${FRONTEND_HOST}" -p "${FRONTEND_PORT}"
}

install_prerequisites
install_node_24
ensure_frontend_env_file
run_frontend
