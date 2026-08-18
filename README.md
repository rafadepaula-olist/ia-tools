# ⚡ IA Tools Manager

Gerenciador visual (GUI) em Python para administração centralizada de **MCPs (Model Context Protocol)**, **Plugins** e **Skills** dos seus agentes de IA locais:

- 🚀 **Antigravity CLI** (`agy` / `gemini`)
- 🟣 **Claude Code** (`claude`)
- ⚡ **OpenCode** (`opencode`)

---

## 🚀 Como Executar

Basta executar o script de inicialização:

```bash
cd /home/rafael.paula/ia-tools
./launcher.sh
```

Ou diretamente pelo Python do ambiente virtual:

```bash
/home/rafael.paula/ia-tools/.venv/bin/python3 /home/rafael.paula/ia-tools/app.py
```

---

## ✨ Funcionalidades Principais

### 1. 🔌 Gestão Completa de MCPs (Model Context Protocol)
- **Ativação / Desativação Instantânea**: Toggle switch visual com 1 clique para habilitar/desabilitar qualquer MCP sem perder a configuração.
- **Instalação / Adição com Presets Prontos**:
  - *Mercado Livre Remote MCP*
  - *ClickUp Remote MCP*
  - *GitHub Copilot / Remote MCP*
  - *Amazon SP-API Dev Assistant*
  - *PostgreSQL / SQLite MCP*
  - *Filesystem MCP*
  - *Memory MCP (Knowledge Graph)*
  - *Brave Search, Puppeteer, Git, Fetch, Docker, Python UVX*
- **Edição Completa**: Edite comandos, argumentos, variáveis de ambiente (KEY-VALUE) e headers HTTP.
- **Edição em JSON Bruto**: Aba com editor JSON para ajustes manuais diretos.
- **Sincronização entre Agentes**: Copie/importe servidores MCP de um agente para outro com 1 clique (ex: Claude ➔ Antigravity ➔ OpenCode).

### 2. 🧩 Gestão de Plugins & Skills
- **Habilitar / Desabilitar**: Alterne o estado de plugins (ex: `superpowers`, `caveman`, `i-have-adhd`, `olist-erp-plugins`) e skills locais.
- **Instalar Plugins**:
  - A partir de repositórios GitHub (`owner/repo`), URLs Git (`git@...` ou `https://...`), pastas locais ou pacotes NPM.
- **Criador / Editor de Skills**:
  - Crie novas skills com frontmatter YAML padronizado e editor Markdown integrado para o `SKILL.md`.
- **Atalho de Pasta**: Abra diretamente o diretório local do plugin/skill no gerenciador de arquivos do sistema.

### 3. 🛡️ Segurança e Backups Automáticos
- Toda e qualquer alteração salva nos arquivos (`settings.json`, `.claude.json`, `opencode.jsonc`, etc.) gera um backup automático com data/hora em `~/.ia-tools-backups/` e uma cópia `.bak`.
- Botão **"Backup Geral"** no topo para criar snapshot instantâneo de todas as configurações.
- Botão **"Pasta Backups"** para inspecionar os arquivos de segurança a qualquer momento.

---

## 📂 Arquivos de Configuração Monitorados

| Agente | Arquivo de Configuração Principal | Diretório de Skills / Plugins |
|---|---|---|
| **Antigravity CLI** | `~/.gemini/settings.json`<br>`~/.gemini/mcp_servers.json`<br>`~/.gemini/extensions/extension-enablement.json` | `~/.gemini/skills/`<br>`~/.gemini/config/skills/`<br>`~/.gemini/extensions/` |
| **Claude Code** | `~/.claude.json`<br>`~/.claude/settings.json` | `~/.claude/plugins/`<br>`~/.claude/skills/` |
| **OpenCode** | `~/.config/opencode/opencode.jsonc` (ou `.json`) | `~/.config/opencode/plugins/`<br>`~/.config/opencode/skills/` |

---

## 🛠️ Tecnologias Utilizadas
- **Python 3.12**
- **PyQt6** (Interface desktop moderna com tema dark personalizado)
- **QtAwesome** (Ícones FontAwesome integrados)
- **JSON5** (Suporte a comentários e vírgulas em JSONC)
