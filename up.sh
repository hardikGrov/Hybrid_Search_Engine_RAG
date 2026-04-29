#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

VENV_DIR=".venv"
API_HOST="0.0.0.0"
API_PORT="8000"
STREAMLIT_PORT="8501"
api_pid=""
streamlit_pid=""

cleanup() {
  if [[ -n "${api_pid}" ]] && kill -0 "${api_pid}" 2>/dev/null; then
    kill "${api_pid}" 2>/dev/null || true
    wait "${api_pid}" 2>/dev/null || true
  fi

  if [[ -n "${streamlit_pid}" ]] && kill -0 "${streamlit_pid}" 2>/dev/null; then
    kill "${streamlit_pid}" 2>/dev/null || true
    wait "${streamlit_pid}" 2>/dev/null || true
  fi
}

trap cleanup INT TERM EXIT

echo -e "${BLUE}🚀 Starting Hybrid Search System...${NC}"
echo -e "${YELLOW}🔧 Setting up environment...${NC}"

cd "${ROOT_DIR}"
mkdir -p logs

if [[ ! -d "${VENV_DIR}" ]]; then
  python3 -m venv "${VENV_DIR}"
fi

source "${VENV_DIR}/bin/activate"

python -m pip install --upgrade pip
pip install -e .

echo -e "${YELLOW}🧠 Starting FastAPI backend...${NC}"
python -m uvicorn backend.app.api.main:app \
  --host "${API_HOST}" \
  --port "${API_PORT}" \
  > logs/api.log 2>&1 &
api_pid=$!

echo -e "${YELLOW}🖥️ Starting Streamlit frontend...${NC}"
PYTHONPATH="${ROOT_DIR}" python -m streamlit run frontend/app.py \
  --server.headless true \
  --browser.gatherUsageStats false \
  --server.address 0.0.0.0 \
  --server.port "${STREAMLIT_PORT}" \
  > logs/frontend.log 2>&1 &
streamlit_pid=$!

echo -e "${GREEN}✔ FastAPI running at: http://localhost:${API_PORT}${NC}"
echo -e "${GREEN}✔ Streamlit running at: http://localhost:${STREAMLIT_PORT}${NC}"
echo -e "${BLUE}📄 Logs:${NC}"
echo -e "${NC}  - API: logs/api.log${NC}"
echo -e "${NC}  - Frontend: logs/frontend.log${NC}"
echo -e "${BLUE}👉 Next steps:${NC}"
echo -e "${NC}  1. Open UI: http://localhost:${STREAMLIT_PORT}${NC}"
echo -e "${NC}  2. Test API: curl http://localhost:${API_PORT}/docs${NC}"
echo -e "${NC}  3. Tail logs: tail -f logs/api.log${NC}"

while true; do
  if ! kill -0 "${api_pid}" 2>/dev/null; then
    echo -e "${RED}❌ FastAPI process crashed.${NC}"
    echo -e "${YELLOW}Check logs: logs/api.log${NC}"
    exit 1
  fi

  if ! kill -0 "${streamlit_pid}" 2>/dev/null; then
    echo -e "${RED}❌ Streamlit process crashed.${NC}"
    echo -e "${YELLOW}Check logs: logs/frontend.log${NC}"
    exit 1
  fi

  sleep 1
done
