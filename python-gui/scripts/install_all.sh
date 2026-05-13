#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-.venv}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Erro: Python 3 não encontrado. Instale Python 3.11+ para macOS Apple Silicon." >&2
  exit 1
fi

if ! command -v node >/dev/null 2>&1; then
  echo "Erro: Node.js não encontrado. Instale Node.js LTS para macOS Apple Silicon." >&2
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "Erro: npm não encontrado. Reinstale o Node.js LTS, que inclui o npm." >&2
  exit 1
fi

echo "==> Criando/atualizando ambiente virtual Python em ${VENV_DIR}"
"$PYTHON_BIN" -m venv "$VENV_DIR"

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "==> Atualizando pip"
python -m pip install --upgrade pip

echo "==> Instalando bibliotecas Python"
python -m pip install -r requirements.txt

echo "==> Instalando bibliotecas Node.js"
npm install

cat <<'MSG'

Instalação concluída.

Para abrir a aplicação, execute:
  cd python-gui
  source .venv/bin/activate
  python app.py

Ou, se estiver dentro da pasta python-gui:
  source .venv/bin/activate
  python app.py
MSG
