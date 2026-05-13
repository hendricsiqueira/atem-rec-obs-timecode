#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python 3 não encontrado. Instale Python 3.11+ antes de continuar." >&2
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "==> Ambiente .venv não encontrado. Executando instalação completa."
  "$PYTHON_BIN" -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

pyinstaller \
  --name "ATEM REC OBS Timecode" \
  --windowed \
  --clean \
  --collect-all pyatem \
  app.py

cat <<'MSG'

Build concluído.

O app estará em:
  dist/ATEM REC OBS Timecode.app

Esta versão é totalmente Python. O operador final não precisa instalar Node.js
nem bibliotecas Python separadamente para executar o .app gerado pelo PyInstaller.
MSG
