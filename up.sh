#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
API_HOST="${API_HOST:-0.0.0.0}"
API_PORT="${API_PORT:-8000}"
STREAMLIT_PORT="${STREAMLIT_PORT:-8501}"

api_pid=""
streamlit_pid=""

cleanup() {
  trap - INT TERM EXIT

  if [[ -n "${api_pid}" ]] && kill -0 "${api_pid}" 2>/dev/null; then
    kill "${api_pid}" 2>/dev/null || true
  fi

  if [[ -n "${streamlit_pid}" ]] && kill -0 "${streamlit_pid}" 2>/dev/null; then
    kill "${streamlit_pid}" 2>/dev/null || true
  fi

  wait 2>/dev/null || true
}

trap cleanup INT TERM EXIT

cd "${ROOT_DIR}"

if [[ ! -d "${VENV_DIR}" ]]; then
  python3 -m venv "${VENV_DIR}"
fi

source "${VENV_DIR}/bin/activate"

python -m pip install --upgrade pip
python -m pip install -e .

python -m uvicorn backend.app.api.main:app --host "${API_HOST}" --port "${API_PORT}" &
api_pid="$!"

python -m streamlit run frontend/app.py \
  --server.address 0.0.0.0 \
  --server.port "${STREAMLIT_PORT}" &
streamlit_pid="$!"

echo "FastAPI running at http://${API_HOST}:${API_PORT}"
echo "Streamlit running at http://0.0.0.0:${STREAMLIT_PORT}"
echo "Press Ctrl+C to stop both processes."

while true; do
  if ! kill -0 "${api_pid}" 2>/dev/null; then
    wait "${api_pid}" 2>/dev/null || true
    exit 1
  fi

  if ! kill -0 "${streamlit_pid}" 2>/dev/null; then
    wait "${streamlit_pid}" 2>/dev/null || true
    exit 1
  fi

  sleep 1
done
