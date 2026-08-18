from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QTextEdit, QPushButton, QTabWidget, QWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QCheckBox, QGroupBox
)
from PyQt6.QtCore import Qt
import json
import qtawesome as qta
from models.mcp import McpServer

PRESETS = {
    "Custom (Vazio)": {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-example"],
        "env": {},
        "url": "",
        "headers": {}
    },
    "Mercado Livre Remote MCP": {
        "type": "http",
        "url": "https://mcp.mercadolibre.com/mcp",
        "headers": {
            "Authorization": "Bearer APP_USR-xxx"
        }
    },
    "ClickUp Remote MCP": {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "mcp-remote", "https://mcp.clickup.com/mcp"],
        "env": {}
    },
    "GitHub MCP Server": {
        "type": "http",
        "url": "https://api.githubcopilot.com/mcp",
        "headers": {
            "Authorization": "Bearer ghp_xxx"
        }
    },
    "Amazon SP-API Dev Assistant": {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@amazon-sp-api-release/sp-api-dev-mcp", "sp-api-dev-assistant-mcp-server"],
        "env": {
            "SP_API_CLIENT_ID": "your_client_id",
            "SP_API_CLIENT_SECRET": "your_client_secret"
        }
    },
    "Filesystem MCP": {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/rafael.paula"],
        "env": {}
    },
    "Memory MCP (Knowledge Graph)": {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-memory"],
        "env": {}
    },
    "PostgreSQL MCP": {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://user:password@localhost:5432/dbname"],
        "env": {}
    },
    "SQLite MCP": {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-sqlite", "--db-path", "/path/to/database.db"],
        "env": {}
    },
    "Brave Search MCP": {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-brave-search"],
        "env": {
            "BRAVE_API_KEY": "your_brave_api_key"
        }
    },
    "Puppeteer MCP (Browser Automation)": {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
        "env": {}
    },
    "Git MCP": {
        "type": "stdio",
        "command": "uvx",
        "args": ["mcp-server-git", "--repository", "."],
        "env": {}
    },
    "Python UVX Server": {
        "type": "stdio",
        "command": "uvx",
        "args": ["mcp-server-fetch"],
        "env": {}
    }
}

class McpEditorDialog(QDialog):
    def __init__(self, mcp: McpServer = None, agent_name: str = "Antigravity", parent=None):
        super().__init__(parent)
        self.mcp = mcp
        self.agent_name = agent_name
        self.is_edit = mcp is not None

        title = f"Editar MCP Server: {mcp.name}" if self.is_edit else f"Instalar / Adicionar MCP Server ({agent_name})"
        self.setWindowTitle(title)
        self.resize(650, 680)

        self._setup_ui()
        if self.is_edit:
            self._load_from_mcp()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(18, 18, 18, 18)

        # Header with Presets (if creating new)
        if not self.is_edit:
            preset_box = QHBoxLayout()
            preset_lbl = QLabel("Template / Preset:")
            preset_lbl.setStyleSheet("font-weight: 600; color: #38bdf8;")
            self.preset_combo = QComboBox()
            for p_name in PRESETS.keys():
                self.preset_combo.addItem(p_name)
            self.preset_combo.currentTextChanged.connect(self._apply_preset)
            preset_box.addWidget(preset_lbl)
            preset_box.addWidget(self.preset_combo, 1)
            layout.addLayout(preset_box)

        # Tabs: Form Mode vs Raw JSON
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("subTabWidget")

        # Tab 1: Form
        self.form_tab = QWidget()
        self._setup_form_tab()
        self.tab_widget.addTab(self.form_tab, qta.icon('fa5s.edit', color='#6366f1'), "Formulário Visual")

        # Tab 2: Raw JSON
        self.json_tab = QWidget()
        self._setup_json_tab()
        self.tab_widget.addTab(self.json_tab, qta.icon('fa5s.code', color='#38bdf8'), "Configuração JSON")

        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tab_widget, 1)

        # Bottom Action Buttons
        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setObjectName("secondaryBtn")
        self.cancel_btn.clicked.connect(self.reject)

        self.save_btn = QPushButton("Salvar MCP Server")
        self.save_btn.setObjectName("primaryBtn")
        self.save_btn.setIcon(qta.icon('fa5s.check', color='white'))
        self.save_btn.clicked.connect(self._on_save)

        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def _setup_form_tab(self):
        f_layout = QVBoxLayout(self.form_tab)
        f_layout.setSpacing(12)

        # Name and Status
        row1 = QHBoxLayout()
        name_lbl = QLabel("Nome do Servidor:")
        name_lbl.setStyleSheet("font-weight: 600;")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ex: mercadolibre, github, postgres")

        self.enabled_check = QCheckBox("Habilitado")
        self.enabled_check.setChecked(True)
        self.enabled_check.setStyleSheet("color: #10b981; font-weight: 600;")

        row1.addWidget(name_lbl)
        row1.addWidget(self.name_input, 1)
        row1.addWidget(self.enabled_check)
        f_layout.addLayout(row1)

        # Type Selector
        row2 = QHBoxLayout()
        type_lbl = QLabel("Tipo de Conexão:")
        type_lbl.setStyleSheet("font-weight: 600;")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["stdio (Comando Local)", "http (Remote SSE / HTTP)", "sse", "local", "remote"])
        self.type_combo.currentTextChanged.connect(self._on_type_changed)

        row2.addWidget(type_lbl)
        row2.addWidget(self.type_combo, 1)
        f_layout.addLayout(row2)

        # Section: Stdio / Command
        self.stdio_group = QGroupBox("Configuração STDIO (Executável / NPX / UVX)")
        std_layout = QVBoxLayout(self.stdio_group)
        std_layout.setSpacing(8)

        cmd_lbl = QLabel("Comando base:")
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Ex: npx, uvx, python3, docker, node")
        std_layout.addWidget(cmd_lbl)
        std_layout.addWidget(self.cmd_input)

        args_lbl = QLabel("Argumentos (um por linha ou separados por espaço):")
        self.args_input = QTextEdit()
        self.args_input.setMaximumHeight(75)
        self.args_input.setPlaceholderText("-y\n@modelcontextprotocol/server-filesystem\n/home/rafael.paula")
        std_layout.addWidget(args_lbl)
        std_layout.addWidget(self.args_input)

        # Env Variables Table
        env_header = QHBoxLayout()
        env_lbl = QLabel("Variáveis de Ambiente (Environment):")
        self.add_env_btn = QPushButton("+ Adicionar Variável")
        self.add_env_btn.setObjectName("secondaryBtn")
        self.add_env_btn.clicked.connect(self._add_env_row)
        env_header.addWidget(env_lbl)
        env_header.addStretch()
        env_header.addWidget(self.add_env_btn)
        std_layout.addLayout(env_header)

        self.env_table = QTableWidget(0, 3)
        self.env_table.setHorizontalHeaderLabels(["Chave (KEY)", "Valor (VALUE)", "Ação"])
        self.env_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.env_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.env_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.env_table.setColumnWidth(2, 60)
        self.env_table.setMaximumHeight(100)
        std_layout.addWidget(self.env_table)

        f_layout.addWidget(self.stdio_group)

        # Section: Remote / HTTP / SSE
        self.http_group = QGroupBox("Configuração Remota (HTTP / SSE URL)")
        http_layout = QVBoxLayout(self.http_group)
        http_layout.setSpacing(8)

        url_lbl = QLabel("URL do Endpoint MCP:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://mcp.exemplo.com/mcp")
        http_layout.addWidget(url_lbl)
        http_layout.addWidget(self.url_input)

        # Headers Table
        hdr_header = QHBoxLayout()
        hdr_lbl = QLabel("Headers HTTP (ex: Authorization Bearer):")
        self.add_hdr_btn = QPushButton("+ Adicionar Header")
        self.add_hdr_btn.setObjectName("secondaryBtn")
        self.add_hdr_btn.clicked.connect(self._add_hdr_row)
        hdr_header.addWidget(hdr_lbl)
        hdr_header.addStretch()
        hdr_header.addWidget(self.add_hdr_btn)
        http_layout.addLayout(hdr_header)

        self.hdr_table = QTableWidget(0, 3)
        self.hdr_table.setHorizontalHeaderLabels(["Header", "Valor", "Ação"])
        self.hdr_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.hdr_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.hdr_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.hdr_table.setColumnWidth(2, 60)
        self.hdr_table.setMaximumHeight(90)
        http_layout.addWidget(self.hdr_table)

        f_layout.addWidget(self.http_group)

        # Initial visibility
        self._on_type_changed(self.type_combo.currentText())

    def _setup_json_tab(self):
        j_layout = QVBoxLayout(self.json_tab)
        lbl = QLabel("Edite diretamente o objeto JSON de configuração do MCP:")
        self.json_edit = QTextEdit()
        self.json_edit.setFontFamily("monospace")
        j_layout.addWidget(lbl)
        j_layout.addWidget(self.json_edit, 1)

    def _on_type_changed(self, text: str):
        is_remote = any(k in text.lower() for k in ["http", "sse", "remote"])
        self.stdio_group.setVisible(not is_remote)
        self.http_group.setVisible(is_remote)

    def _add_env_row(self, key="", val=""):
        row = self.env_table.rowCount()
        self.env_table.insertRow(row)
        self.env_table.setItem(row, 0, QTableWidgetItem(key))
        self.env_table.setItem(row, 1, QTableWidgetItem(val))
        del_btn = QPushButton()
        del_btn.setIcon(qta.icon('fa5s.trash', color='#ef4444'))
        del_btn.clicked.connect(lambda: self.env_table.removeRow(self.env_table.currentRow() if self.env_table.currentRow() >= 0 else row))
        self.env_table.setCellWidget(row, 2, del_btn)

    def _add_hdr_row(self, key="", val=""):
        row = self.hdr_table.rowCount()
        self.hdr_table.insertRow(row)
        self.hdr_table.setItem(row, 0, QTableWidgetItem(key))
        self.hdr_table.setItem(row, 1, QTableWidgetItem(val))
        del_btn = QPushButton()
        del_btn.setIcon(qta.icon('fa5s.trash', color='#ef4444'))
        del_btn.clicked.connect(lambda: self.hdr_table.removeRow(self.hdr_table.currentRow() if self.hdr_table.currentRow() >= 0 else row))
        self.hdr_table.setCellWidget(row, 2, del_btn)

    def _apply_preset(self, preset_name: str):
        if preset_name not in PRESETS:
            return
        p = PRESETS[preset_name]
        is_remote = p.get("type") in ["http", "sse", "remote"] or bool(p.get("url"))
        
        if is_remote:
            self.type_combo.setCurrentText("http (Remote SSE / HTTP)")
            self.url_input.setText(p.get("url", ""))
            self.hdr_table.setRowCount(0)
            for k, v in p.get("headers", {}).items():
                self._add_hdr_row(k, v)
        else:
            self.type_combo.setCurrentText("stdio (Comando Local)")
            self.cmd_input.setText(p.get("command", "npx"))
            args = p.get("args", [])
            self.args_input.setPlainText("\n".join(args) if isinstance(args, list) else str(args))
            self.env_table.setRowCount(0)
            for k, v in p.get("env", {}).items():
                self._add_env_row(k, v)

    def _load_from_mcp(self):
        self.name_input.setText(self.mcp.name)
        self.enabled_check.setChecked(self.mcp.enabled)
        
        if self.mcp.is_remote:
            self.type_combo.setCurrentText("http (Remote SSE / HTTP)")
            self.url_input.setText(self.mcp.url or "")
            self.hdr_table.setRowCount(0)
            for k, v in self.mcp.headers.items():
                self._add_hdr_row(k, v)
        else:
            self.type_combo.setCurrentText("stdio (Comando Local)")
            self.cmd_input.setText(self.mcp.command or "")
            self.args_input.setPlainText("\n".join(self.mcp.args))
            self.env_table.setRowCount(0)
            for k, v in self.mcp.env.items():
                self._add_env_row(k, v)

    def _on_tab_changed(self, index: int):
        if index == 1: # switched to JSON
            try:
                mcp_obj = self._build_mcp_object()
                d = mcp_obj.to_antigravity_dict() if "Antigravity" in self.agent_name else (mcp_obj.to_claude_dict() if "Claude" in self.agent_name else mcp_obj.to_opencode_dict())
                self.json_edit.setPlainText(json.dumps(d, indent=2))
            except Exception:
                pass

    def _build_mcp_object(self) -> McpServer:
        name = self.name_input.text().strip()
        enabled = self.enabled_check.isChecked()
        type_str = self.type_combo.currentText()
        is_remote = any(k in type_str.lower() for k in ["http", "sse", "remote"])

        if is_remote:
            url = self.url_input.text().strip()
            headers = {}
            for r in range(self.hdr_table.rowCount()):
                k_item = self.hdr_table.item(r, 0)
                v_item = self.hdr_table.item(r, 1)
                if k_item and k_item.text().strip():
                    headers[k_item.text().strip()] = v_item.text().strip() if v_item else ""
            return McpServer(
                name=name,
                server_type="http" if "http" in type_str.lower() else ("sse" if "sse" in type_str.lower() else "remote"),
                url=url,
                headers=headers,
                enabled=enabled
            )
        else:
            cmd = self.cmd_input.text().strip()
            args_text = self.args_input.toPlainText().strip()
            args = [a.strip() for a in args_text.split('\n') if a.strip()] if '\n' in args_text else [a.strip() for a in args_text.split() if a.strip()]
            env = {}
            for r in range(self.env_table.rowCount()):
                k_item = self.env_table.item(r, 0)
                v_item = self.env_table.item(r, 1)
                if k_item and k_item.text().strip():
                    env[k_item.text().strip()] = v_item.text().strip() if v_item else ""
            return McpServer(
                name=name,
                server_type="local" if "local" in type_str.lower() else "stdio",
                command=cmd if cmd else None,
                args=args,
                env=env,
                enabled=enabled
            )

    def _on_save(self):
        # If active tab is JSON, parse JSON
        if self.tab_widget.currentIndex() == 1:
            try:
                raw_json = self.json_edit.toPlainText().strip()
                data = json.loads(raw_json)
                name = self.name_input.text().strip()
                if not name:
                    QMessageBox.warning(self, "Aviso", "Por favor informe o Nome do MCP Server na aba de formulário.")
                    return
                # Create MCP from JSON dict
                url = data.get("url", "")
                self.result_mcp = McpServer(
                    name=name,
                    server_type=data.get("type", "http" if url else "stdio"),
                    command=data.get("command"),
                    args=data.get("args", []),
                    env=data.get("env", data.get("environment", {})),
                    url=url if url else None,
                    headers=data.get("headers", {}),
                    enabled=data.get("enabled", self.enabled_check.isChecked()),
                    raw_data=data
                )
                self.accept()
                return
            except Exception as e:
                QMessageBox.critical(self, "Erro de Validação JSON", f"O JSON inserido é inválido:\n{e}")
                return

        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Aviso", "O nome do MCP Server é obrigatório.")
            self.name_input.setFocus()
            return

        self.result_mcp = self._build_mcp_object()
        self.accept()
