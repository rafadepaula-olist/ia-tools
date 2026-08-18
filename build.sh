#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "⚡ Preparando ambiente para compilação..."
if [ ! -d "$DIR/.venv" ]; then
    python3 -m venv "$DIR/.venv"
fi

"$DIR/.venv/bin/pip" install --upgrade pip
"$DIR/.venv/bin/pip" install -r "$DIR/requirements.txt"
"$DIR/.venv/bin/pip" install pyinstaller

echo "🔨 Compilando binário standalone './dist/ia-tools'..."
"$DIR/.venv/bin/pyinstaller" --noconfirm --onefile --windowed --name ia-tools \
    --collect-all qtawesome \
    --collect-all json5 \
    --add-data "$DIR/config_managers:config_managers" \
    --add-data "$DIR/models:models" \
    --add-data "$DIR/ui:ui" \
    app.py

ln -sf dist/ia-tools ia-tools
chmod +x ia-tools dist/ia-tools

# Auto-update ~/.local/bin/ia-tools
mkdir -p "$HOME/.local/bin"
cp dist/ia-tools "$HOME/.local/bin/ia-tools"
chmod +x "$HOME/.local/bin/ia-tools"

# Update desktop database
update-desktop-database "$HOME/.local/share/applications/" 2>/dev/null || true

echo "✅ Binário compilado e instalado com sucesso!"
echo "   - Local: ./ia-tools"
echo "   - Global ($PATH): ~/.local/bin/ia-tools"
