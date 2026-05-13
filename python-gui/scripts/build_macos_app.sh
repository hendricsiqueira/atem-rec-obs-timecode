#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 não encontrado. Instale Python 3.11+ antes de continuar." >&2
  exit 1
fi

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js não encontrado. Instale Node.js LTS antes de continuar." >&2
  exit 1
fi

python3 -m pip install -r requirements.txt
npm install

pyinstaller \
  --name "ATEM REC OBS Timecode" \
  --windowed \
  --clean \
  --add-data "backend/atem_node_bridge.js:backend" \
  --add-data "package.json:." \
  app.py

cat <<'MSG'

Build concluído.

O app estará em:
  dist/ATEM REC OBS Timecode.app

Observação: esta primeira versão empacota a GUI Python e o helper JavaScript, mas ainda espera que Node.js esteja instalado no macOS para executar o backend ATEM. Para distribuição sem dependência externa, o próximo passo é embutir um binário Node ARM64 dentro do .app.
MSG
