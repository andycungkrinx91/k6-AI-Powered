#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
VENV_DIR="${BACKEND_DIR}/venv"
ENV_FILE="${BACKEND_DIR}/.env"
CONFIG_ENV_FILE="${SCRIPT_DIR}/.env"
LEGACY_CONFIG_ENV_FILE="${SCRIPT_DIR}/run-backend-ubuntu.env"

load_config_env_file() {
  local env_path="${CONFIG_ENV_FILE}"
  if [[ ! -f "${env_path}" && -f "${LEGACY_CONFIG_ENV_FILE}" ]]; then
    env_path="${LEGACY_CONFIG_ENV_FILE}"
  fi

  if [[ ! -f "${env_path}" ]]; then
    return
  fi

  local owner_uid current_uid mode
  current_uid="$(id -u)"
  owner_uid="$(stat -c '%u' "${env_path}")"
  mode="$(stat -c '%a' "${env_path}")"

  if [[ "${owner_uid}" != "${current_uid}" && "${owner_uid}" != "0" ]]; then
    echo "Warning: skipping ${env_path} (owner must be current user or root)" >&2
    return
  fi

  if (( (8#${mode} & 0002) != 0 )); then
    echo "Warning: skipping ${env_path} (file is world-writable)" >&2
    return
  fi

  echo "Loading environment overrides from ${env_path}"
  set -a
  # shellcheck disable=SC1090
  source "${env_path}"
  set +a
}

load_config_env_file

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

SKIP_DB_INIT="${SKIP_DB_INIT:-0}"
INSTALL_LIGHTHOUSE="${INSTALL_LIGHTHOUSE:-0}"

DB_NAME="${DB_NAME:-k6ai}"
DB_USER="${DB_USER:-k6user}"
DB_PASSWORD="${DB_PASSWORD:-k6password}"
DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-3306}"
DB_ROOT_USER="${DB_ROOT_USER:-root}"
DB_ROOT_PASSWORD="${DB_ROOT_PASSWORD:-}"

AUTH_SECRET="${AUTH_SECRET:-change_me_to_a_long_random_secret}"
ACCESS_TOKEN_EXPIRE_MINUTES="${ACCESS_TOKEN_EXPIRE_MINUTES:-1440}"
INITIAL_ADMIN_USERNAME="${INITIAL_ADMIN_USERNAME:-admin}"
INITIAL_ADMIN_EMAIL="${INITIAL_ADMIN_EMAIL:-admin@example.com}"
INITIAL_ADMIN_PASSWORD="${INITIAL_ADMIN_PASSWORD:-change_me}"

if [[ ! -d "${BACKEND_DIR}" ]]; then
  echo "Error: backend directory not found at ${BACKEND_DIR}" >&2
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
  ${SUDO} apt-get install -y python3-venv python3-pip nodejs npm curl ca-certificates gnupg
}

install_k6() {
  if command -v k6 >/dev/null 2>&1; then
    echo "k6 already installed"
    return
  fi

  ${SUDO} mkdir -p /etc/apt/keyrings

  if [[ ! -f /etc/apt/keyrings/k6-archive-keyring.gpg ]]; then
    curl -fsSL https://dl.k6.io/key.gpg | ${SUDO} gpg --dearmor -o /etc/apt/keyrings/k6-archive-keyring.gpg
  fi

  if [[ ! -f /etc/apt/sources.list.d/k6.list ]]; then
    echo "deb [signed-by=/etc/apt/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | ${SUDO} tee /etc/apt/sources.list.d/k6.list >/dev/null
  fi

  APT_UPDATED=0
  apt_update
  ${SUDO} apt-get install -y k6
}

install_lighthouse() {
  if [[ "${INSTALL_LIGHTHOUSE}" != "1" ]]; then
    echo "Skipping lighthouse install (set INSTALL_LIGHTHOUSE=1 to enable)"
    return
  fi

  if command -v lighthouse >/dev/null 2>&1; then
    echo "lighthouse already installed"
    return
  fi

  ${SUDO} npm install -g lighthouse
}

mysql_exec() {
  local sql="$1"

  if [[ -n "${DB_ROOT_PASSWORD}" ]]; then
    mysql --protocol=TCP -h "${DB_HOST}" -P "${DB_PORT}" -u "${DB_ROOT_USER}" -p"${DB_ROOT_PASSWORD}" -e "${sql}"
  else
    ${SUDO} mysql -u "${DB_ROOT_USER}" -e "${sql}"
  fi
}

init_database() {
  if [[ "${SKIP_DB_INIT}" == "1" ]]; then
    echo "Skipping DB initialization (SKIP_DB_INIT=1)"
    return
  fi

  mysql_exec "CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\`;"
  mysql_exec "CREATE USER IF NOT EXISTS '${DB_USER}'@'%' IDENTIFIED BY '${DB_PASSWORD}';"
  mysql_exec "ALTER USER '${DB_USER}'@'%' IDENTIFIED BY '${DB_PASSWORD}';"
  mysql_exec "GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'%'; FLUSH PRIVILEGES;"
}

ensure_env_file() {
  if [[ -f "${ENV_FILE}" ]]; then
    echo "Using existing ${ENV_FILE}"
    return
  fi

  cat >"${ENV_FILE}" <<EOF
# Replace values before exposing publicly
DATABASE_URL=mysql+aiomysql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}
BACKEND_API_KEY=change_me
BACKEND_ADMIN_KEY=change_me
LLM_PROVIDER=gemini
GEMINI_API_KEYS=comma_separated_keys
OPENAI_API_KEY=
OPENAI_BASE_URL=
RESULT_DIR=./results
CAPTCHA_SECRET=change_me
CORS_ORIGINS=http://localhost:3000

# Auth (JWT)
AUTH_SECRET=${AUTH_SECRET}
ACCESS_TOKEN_EXPIRE_MINUTES=${ACCESS_TOKEN_EXPIRE_MINUTES}

# Initial admin bootstrap (kept in sync on backend startup)
INITIAL_ADMIN_USERNAME=${INITIAL_ADMIN_USERNAME}
INITIAL_ADMIN_EMAIL=${INITIAL_ADMIN_EMAIL}
INITIAL_ADMIN_PASSWORD=${INITIAL_ADMIN_PASSWORD}
EOF

  echo "Created ${ENV_FILE}"
}

setup_python_env() {
  if [[ ! -d "${VENV_DIR}" ]]; then
    python3 -m venv "${VENV_DIR}"
  fi

  # shellcheck disable=SC1091
  source "${VENV_DIR}/bin/activate"

  python -m pip install --upgrade pip
  python -m pip install -r "${BACKEND_DIR}/requirements.txt"
}

install_playwright() {
  if ! python -c "import playwright" >/dev/null 2>&1; then
    python -m pip install playwright
  fi

  python -m playwright install --with-deps chromium
}

run_backend() {
  cd "${BACKEND_DIR}"
  exec "${VENV_DIR}/bin/uvicorn" app.main:app --host "${HOST}" --port "${PORT}"
}

install_prerequisites
install_k6
install_lighthouse
init_database
ensure_env_file
setup_python_env
install_playwright
run_backend
