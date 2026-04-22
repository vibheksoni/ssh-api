#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="$REPO_ROOT/.venv"
VENV_PYTHON="$VENV_PATH/bin/python"
CONFIG_PATH="$REPO_ROOT/config.json"
CONFIG_EXAMPLE_PATH="$REPO_ROOT/config.example.json"
REQUIREMENTS_PATH="$REPO_ROOT/requirements.txt"

if command -v python3 >/dev/null 2>&1; then
  HOST_PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
  HOST_PYTHON="python"
else
  echo "Python 3.10+ is required but no python3/python executable was found in PATH." >&2
  exit 1
fi

if [ ! -x "$VENV_PYTHON" ]; then
  echo "Creating virtual environment in $VENV_PATH"
  "$HOST_PYTHON" -m venv "$VENV_PATH"
fi

echo "Installing dependencies"
"$VENV_PYTHON" -m pip install --upgrade pip
"$VENV_PYTHON" -m pip install -r "$REQUIREMENTS_PATH"

if [ ! -f "$CONFIG_PATH" ]; then
  cp "$CONFIG_EXAMPLE_PATH" "$CONFIG_PATH"
  echo "Created config.json from config.example.json"
else
  echo "config.json already exists"
fi

echo
echo "Bootstrap complete."
echo "Next steps:"
echo "1. Edit config.json if you want local default SSH settings."
echo "2. Start the API with:"
echo "   $VENV_PYTHON run.py"
echo "3. Open http://localhost:8754/docs once it is running."
