#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Erro: Python 3 não encontrado. Instale Python 3.11+ antes de continuar." >&2
  exit 1
fi

echo "==> Usando Python do sistema: $($PYTHON_BIN --version)"

if ! "$PYTHON_BIN" -m pip --version >/dev/null 2>&1; then
  echo "==> pip não encontrado. Tentando habilitar com ensurepip."
  "$PYTHON_BIN" -m ensurepip --upgrade
fi

# Mantém a instalação simples e direta, sem .venv.
# Se quiser atualizar pip/setuptools/wheel explicitamente, execute:
#   UPDATE_PIP=1 ./scripts/install_all.sh
if [ "${UPDATE_PIP:-0}" = "1" ]; then
  echo "==> Atualizando pip/setuptools/wheel no Python do sistema"
  "$PYTHON_BIN" -m pip install --disable-pip-version-check --upgrade pip setuptools wheel
else
  echo "==> Pulando upgrade do pip; use UPDATE_PIP=1 para atualizar explicitamente"
fi

echo "==> Instalando bibliotecas Python diretamente no Python do sistema"
"$PYTHON_BIN" -m pip install --disable-pip-version-check -r requirements.txt

echo "==> Validando imports principais"
"$PYTHON_BIN" - <<'PY'
import PySide6
import pyatem
import usb
print("Imports OK: PySide6, pyatem e usb")
PY

cat <<'MSG'

Instalação concluída.

Esta versão usa comunicação ATEM nativa em Python com pyatem.
Node.js não é necessário para instalar, executar ou empacotar esta GUI.
Nenhum ambiente virtual .venv foi criado ou usado.

Para abrir a aplicação dentro da pasta python-gui, execute:
  python3 app.py
MSG
