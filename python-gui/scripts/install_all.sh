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

pip_install() {
  local description="$1"
  shift

  echo "==> ${description}"
  if "$PYTHON_BIN" -m pip install --disable-pip-version-check "$@"; then
    return 0
  fi

  cat <<'MSG'

O pip recusou a instalação normal. Em macOS com Python instalado pelo Homebrew,
isso costuma acontecer por causa do erro "externally-managed-environment".

Tentando novamente com instalação no usuário, sem criar .venv:
  --user --break-system-packages

MSG

  "$PYTHON_BIN" -m pip install --disable-pip-version-check --user --break-system-packages "$@"
}

# Mantém a instalação simples e direta, sem .venv.
# Se quiser atualizar pip/setuptools/wheel explicitamente, execute:
#   UPDATE_PIP=1 ./scripts/install_all.sh
if [ "${UPDATE_PIP:-0}" = "1" ]; then
  pip_install "Atualizando pip/setuptools/wheel" --upgrade pip setuptools wheel
else
  echo "==> Pulando upgrade do pip; use UPDATE_PIP=1 para atualizar explicitamente"
fi

pip_install "Instalando bibliotecas Python" -r requirements.txt

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
