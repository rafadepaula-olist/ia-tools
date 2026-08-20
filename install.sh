#!/usr/bin/env bash
# ==============================================================================
#  ⚡ IA Tools Manager - One-line Installer (curl | bash)
# ==============================================================================
set -e

REPO="rafadepaula-olist/ia-tools"
GITHUB_RAW="https://raw.githubusercontent.com/${REPO}/main"
INSTALL_DIR="${HOME}/.local/bin"
BINARY_PATH="${INSTALL_DIR}/ia-tools"

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${CYAN}${BOLD}"
echo "============================================================"
echo "   ⚡ IA Tools Manager - Instalador Automático"
echo "============================================================"
echo -e "${NC}"

# Detect OS & Architecture
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

case "${OS}" in
    linux*)
        case "${ARCH}" in
            x86_64|amd64)
                ASSET_NAME="ia-tools-linux-x86_64"
                ;;
            *)
                echo -e "${RED}Erro: Arquitetura '${ARCH}' no Linux não possui binário pré-compilado oficial.${NC}"
                echo "Por favor, clone o repositório e execute ./build.sh localmente."
                exit 1
                ;;
        esac
        ;;
    darwin*)
        ASSET_NAME="ia-tools-macos"
        ;;
    *)
        echo -e "${RED}Erro: Sistema operacional '${OS}' não suportado automaticamente por este script.${NC}"
        exit 1
        ;;
esac

DOWNLOAD_URL="https://github.com/${REPO}/releases/latest/download/${ASSET_NAME}"
CHECKSUMS_URL="https://github.com/${REPO}/releases/latest/download/SHA256SUMS"

echo -e "📦 Detectado: ${BOLD}${OS} (${ARCH})${NC}"
echo -e "⬇️  Baixando versão mais recente de ${CYAN}${DOWNLOAD_URL}${NC}..."

# Ensure target bin directory exists
mkdir -p "${INSTALL_DIR}"

TMP_DOWNLOAD="${BINARY_PATH}.tmp.$$"
TMP_CHECKSUMS="${INSTALL_DIR}/SHA256SUMS.tmp.$$"

# Download binary and checksums
if command -v curl >/dev/null 2>&1; then
    curl -fsSL "${DOWNLOAD_URL}" -o "${TMP_DOWNLOAD}"
    curl -fsSL "${CHECKSUMS_URL}" -o "${TMP_CHECKSUMS}" || true
elif command -v wget >/dev/null 2>&1; then
    wget -qO "${TMP_DOWNLOAD}" "${DOWNLOAD_URL}"
    wget -qO "${TMP_CHECKSUMS}" "${CHECKSUMS_URL}" || true
else
    echo -e "${RED}Erro: 'curl' ou 'wget' é necessário para realizar o download.${NC}"
    exit 1
fi

# Verify SHA256 checksum if SHA256SUMS is available
if [ -f "${TMP_CHECKSUMS}" ] && [ -s "${TMP_CHECKSUMS}" ]; then
    echo -e "🔒 Verificando integridade criptográfica (SHA-256)..."
    EXPECTED_SHA=$(grep -E "${ASSET_NAME}$" "${TMP_CHECKSUMS}" | awk '{print $1}' || true)
    if [ -n "${EXPECTED_SHA}" ]; then
        if command -v sha256sum >/dev/null 2>&1; then
            ACTUAL_SHA=$(sha256sum "${TMP_DOWNLOAD}" | awk '{print $1}')
        elif command -v shasum >/dev/null 2>&1; then
            ACTUAL_SHA=$(shasum -a 256 "${TMP_DOWNLOAD}" | awk '{print $1}')
        else
            ACTUAL_SHA=""
        fi

        if [ -n "${ACTUAL_SHA}" ]; then
            if [ "${EXPECTED_SHA}" != "${ACTUAL_SHA}" ]; then
                echo -e "${RED}❌ Erro de segurança: Checksum SHA-256 não confere!${NC}"
                echo -e "Esperado: ${EXPECTED_SHA}"
                echo -e "Obtido:   ${ACTUAL_SHA}"
                rm -f "${TMP_DOWNLOAD}" "${TMP_CHECKSUMS}"
                exit 1
            fi
            echo -e "✅ Checksum verificado: ${GREEN}${ACTUAL_SHA}${NC}"
        fi
    fi
    rm -f "${TMP_CHECKSUMS}"
fi

mv -f "${TMP_DOWNLOAD}" "${BINARY_PATH}"
chmod +x "${BINARY_PATH}"
echo -e "✅ Binário instalado em: ${GREEN}${BINARY_PATH}${NC}"

# Desktop Entry & Icon Integration (Linux only)
if [ "${OS}" = "linux" ]; then
    ICON_DIR="${HOME}/.local/share/icons/hicolor/128x128/apps"
    DESKTOP_DIR="${HOME}/.local/share/applications"
    mkdir -p "${ICON_DIR}" "${DESKTOP_DIR}"

    echo "🖼️  Configurando atalho no menu de aplicativos..."
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL "${GITHUB_RAW}/assets/ia-tools.png" -o "${ICON_DIR}/ia-tools.png" || true
    fi

    cat <<EOF > "${DESKTOP_DIR}/ia-tools.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=IA Tools Manager
GenericName=AI Agent Tools & MCP Manager
Comment=Gestão centralizada de MCPs, Plugins & Skills para Antigravity, Claude, OpenCode, Codex, Windsurf e Cursor
Exec=${BINARY_PATH}
Icon=ia-tools
Terminal=false
Categories=Development;Utility;
Keywords=ai;mcp;claude;gemini;antigravity;opencode;codex;windsurf;cursor;tools;
StartupWMClass=ia-tools
StartupNotify=true
EOF
    chmod +x "${DESKTOP_DIR}/ia-tools.desktop"

    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database "${DESKTOP_DIR}" >/dev/null 2>&1 || true
    fi
fi

echo ""
echo -e "${GREEN}${BOLD}🎉 Instalação concluída com sucesso!${NC}"
echo ""

# Check PATH
case ":$PATH:" in
    *":${INSTALL_DIR}:"*)
        echo -e "Para iniciar o app agora, execute: ${CYAN}${BOLD}ia-tools${NC}"
        ;;
    *)
        echo -e "${YELLOW}${BOLD}⚠️  Atenção:${NC} O diretório ${BOLD}${INSTALL_DIR}${NC} não está no seu PATH."
        echo "Adicione ao seu arquivo de configuração do shell (~/.bashrc ou ~/.zshrc):"
        echo ""
        echo -e "  ${CYAN}export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
        echo ""
        echo -e "Ou execute diretamente com: ${CYAN}${BOLD}${BINARY_PATH}${NC}"
        ;;
esac
echo ""
