#!/usr/bin/env bash
set -euo pipefail
# start-waf.sh - create venv, install requirements, and start the WAF
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Using project root: ${ROOT_DIR}"

if command -v python3 >/dev/null 2>&1; then
    PY=python3
elif command -v python >/dev/null 2>&1; then
    PY=python
else
    echo "No python interpreter found. Install Python 3 and retry." >&2
    exit 1
fi

VENV_DIR="${ROOT_DIR}/.venv"
if [ ! -d "${VENV_DIR}" ]; then
    echo "Creating virtual environment..."
    "$PY" -m venv "${VENV_DIR}"
fi

echo "Activating virtual environment..."
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

echo "Upgrading pip and installing requirements (if present)..."
python -m pip install --upgrade pip
if [ -f "${ROOT_DIR}/requirements.txt" ]; then
    pip install -r "${ROOT_DIR}/requirements.txt"
fi

echo "Starting WAF (main.py) on port 8082..."
exec python "${ROOT_DIR}/main.py" --port 8082
