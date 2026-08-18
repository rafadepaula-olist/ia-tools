# ⚡ IA Tools Manager

> **Gerenciador visual (GUI) em Python para administração centralizada de MCPs (Model Context Protocol), Plugins e Skills dos seus agentes de IA locais.**

Compatível nativamente com:
- 🚀 **Antigravity CLI** (`agy` / `gemini`)
- 🟣 **Claude Code** (`claude`) — *com suporte a escopos Globais, por Projeto e integrações Cloud Claude.ai*
- ⚡ **OpenCode** (`opencode`)

---

## 📥 Instalação & Execução

### Opção 1: Rodar a partir do Repositório (Desenvolvimento Rápido)

Não é necessário instalar nada manualmente. O script `launcher.sh` cria o ambiente virtual `.venv`, instala as dependências e abre o app automaticamente:

```bash
git clone https://github.com/rafadepaula-olist/ia-tools.git
cd ia-tools
./launcher.sh
```

---

### Opção 2: Compilar o Binário Standalone e Instalar no Sistema

Você pode gerar um **único executável binário independente** (que não precisa de Python ou pip para rodar) e instalá-lo no menu de aplicativos do Linux (`$PATH` e Application Drawer):

```bash
cd ia-tools
./build.sh
```

O script `./build.sh` realiza automaticamente:
1. Criação/atualização do ambiente virtual com `PyInstaller`, `PyQt6`, `qtawesome` e `json5`.
2. Compilação do binário standalone em `./dist/ia-tools`.
3. Criação do atalho local `./ia-tools`.
4. Instalação atômica em `~/.local/bin/ia-tools` (acessível globalmente no terminal).
5. Instalação do ícone em `~/.local/share/icons/hicolor/` e do atalho `ia-tools.desktop` no menu de aplicativos do sistema operacional.

Depois disso, você pode abrir o app de três formas:
* **Pelo Menu de Aplicativos / Drawer**: Pressionando a tecla `Super` (Windows) e buscando por **"IA Tools Manager"**
* **Pelo Terminal (em qualquer pasta)**: Digitando `ia-tools`
* **Na pasta do projeto**: Executando `./ia-tools`

---

### Opção 3: Baixar os Binários Pré-Compilados

Binários pré-compilados para **Linux (x86_64)**, **macOS** e **Windows (.exe)** são gerados automaticamente via GitHub Actions em cada release:

👉 [Acessar a Página de Releases](https://github.com/rafadepaula-olist/ia-tools/releases)

---

## ✨ Funcionalidades Principais

### 1. 🔌 Gestão Completa de MCPs (Model Context Protocol)
* **Toggle Switch Visual Instantâneo**: Ative ou desative qualquer servidor MCP com 1 clique (sem perder credenciais, argumentos ou tokens).
* **Suporte a Múltiplos Escopos no Claude**: Visualização e edição de MCPs Globais, específicos de cada projeto local (`[PROJ: ~]`, `[PROJ: tinyerp]`) e integrações OAuth da nuvem (`[CLAUDE.AI]`).
* **Presets Prontos de 1 Clique**:
  * *Mercado Livre Remote MCP*
  * *ClickUp Remote MCP*
  * *GitHub Copilot / Remote MCP*
  * *Amazon SP-API Dev Assistant*
  * *PostgreSQL / SQLite MCP*
  * *Filesystem MCP & Memory MCP (Knowledge Graph)*
  * *Brave Search, Puppeteer, Git, Fetch, Docker, Python UVX*
* **Editor Visual & Editor JSON Bruto**: Edição tanto por formulário (comando, argumentos, tabela chave-valor de variáveis de ambiente e headers) quanto por código JSON com formatação e validação sintática em tempo real.
* **Sincronização entre Agentes**: Copie servidores MCP de um agente para outro com 1 clique (ex: Claude ➔ Antigravity ➔ OpenCode).

### 2. 🧩 Gestão de Plugins, Skills & Extensões
* **Habilitar / Desabilitar**: Alterne o estado de plugins (ex: `superpowers`, `caveman`, `i-have-adhd`, `olist-erp-plugins`, `agy-delegate`) e skills locais.
* **Instalador de Plugins**: Suporte a repositórios GitHub (`owner/repo`), URLs Git (`git@...`), diretórios locais e pacotes NPM.
* **Criador e Editor de Skills**: Crie novas skills com frontmatter YAML padronizado e editor Markdown integrado para o arquivo `SKILL.md`.
* **Atalho de Pasta**: Botão para abrir o diretório local de qualquer skill/plugin no seu gerenciador de arquivos padrão do Linux (`xdg-open`).

### 3. 🛡️ Segurança e Backups Automáticos
* Toda alteração salva gera automaticamente um snapshot com data/hora em `~/.ia-tools-backups/` e uma cópia `.bak`.
* Botões no cabeçalho para gerar **Backup Geral** e **Abrir Pasta de Backups**.

---

## 📂 Arquivos de Configuração Monitorados

| Agente | Arquivos de Configuração | Diretórios de Skills / Plugins |
|---|---|---|
| 🚀 **Antigravity CLI** | `~/.gemini/settings.json`<br>`~/.gemini/mcp_servers.json`<br>`~/.gemini/extensions/extension-enablement.json` | `~/.gemini/skills/`<br>`~/.gemini/config/skills/`<br>`~/.gemini/extensions/` |
| 🟣 **Claude Code** | `~/.claude.json` *(global + projetos)*<br>`~/.claude/settings.json` | `~/.claude/plugins/`<br>`~/.claude/skills/` |
| ⚡ **OpenCode** | `~/.config/opencode/opencode.jsonc` (ou `.json`) | `~/.config/opencode/plugins/`<br>`~/.config/opencode/skills/` |

---

## 🧩 Como Adicionar Novos Providers (Codex, Windsurf, Cursor, Goose, etc.)

O projeto utiliza uma arquitetura desacoplada e extensível. Para adicionar um novo agente:

1. **Model**: Adicione o método `to_<provider>_dict()` em [`models/mcp.py`](models/mcp.py).
2. **Config Manager**: Crie `config_managers/<provider>.py` herdando de `BaseConfigManager` implementando `list_mcps()`, `save_mcp()`, `toggle_mcp()`, `delete_mcp()`.
3. **UI**: Registre a nova aba em [`ui/main_window.py`](ui/main_window.py) e adicione o ícone em [`ui/agent_tab.py`](ui/agent_tab.py).
4. **Testes & Rebuild**: Adicione os testes em [`tests/test_managers.py`](tests/test_managers.py) e execute `./build.sh`.

👉 **Guia completo para agentes**: Consulte a skill [`skills/extending-ia-tools-providers/SKILL.md`](skills/extending-ia-tools-providers/SKILL.md).

---

## 🧪 Rodando os Testes Automatizados

```bash
cd ia-tools
./.venv/bin/python3 -m unittest discover tests/
```

---

## 🛠️ Tecnologias Utilizadas
* **Python 3.12**
* **PyQt6** (Interface desktop nativa com dark theme de alto contraste)
* **QtAwesome** (Ícones FontAwesome vetoriais)
* **JSON5** (Tolerância a comentários e vírgulas finais em arquivos JSONC)
* **PyInstaller** (Empacotamento em binário standalone único)

---

## 📄 Licença
Distribuído sob a licença **MIT**. Consulte [`LICENSE`](LICENSE) para mais detalhes.
