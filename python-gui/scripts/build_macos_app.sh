#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python 3 não encontrado. Instale Python 3.11+ antes de continuar." >&2
  exit 1
fi

echo "==> Usando Python do sistema: $($PYTHON_BIN --version)"

pip_install_requirements() {
  echo "==> Instalando/validando dependências no Python do sistema"
  if "$PYTHON_BIN" -m pip install --disable-pip-version-check -r requirements.txt; then
    return 0
  fi

  cat <<'MSG'

O pip recusou a instalação normal. Em macOS com Python instalado pelo Homebrew,
isso costuma acontecer por causa do erro "externally-managed-environment".

Tentando novamente com instalação no usuário, sem criar .venv:
  --user --break-system-packages

MSG

  "$PYTHON_BIN" -m pip install --disable-pip-version-check --user --break-system-packages -r requirements.txt
}

pip_install_requirements

echo "==> Validando imports antes do build"
"$PYTHON_BIN" - <<'PY'
import PySide6
import pyatem
import usb
print("Imports OK: PySide6, pyatem e usb")
PY

echo "==> Gerando .app com PyInstaller"
"$PYTHON_BIN" -m PyInstaller \
  --name "ATEM REC OBS Timecode" \
  --windowed \
  --clean \
  --collect-all pyatem \
  --hidden-import usb \
  --hidden-import usb.core \
  --hidden-import usb.util \
  app.py

cat <<'MSG'

Build concluído.

O app estará em:
  dist/ATEM REC OBS Timecode.app

Esta versão é totalmente Python. O operador final não precisa instalar Node.js
nem bibliotecas Python separadamente para executar o .app gerado pelo PyInstaller.
MSG
