#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Ensure virtual environment exists
if [ ! -d "$DIR/.venv" ]; then
    echo "⚡ Criando ambiente virtual Python..."
    python3 -m venv "$DIR/.venv"
    "$DIR/.venv/bin/pip" install --upgrade pip
    "$DIR/.venv/bin/pip" install -r "$DIR/requirements.txt"
fi

# Run application
exec "$DIR/.venv/bin/python3" "$DIR/app.py" "$@"
