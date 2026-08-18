from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QComboBox, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
import qtawesome as qta
import subprocess
import os

from models.mcp import McpServer
from ui.components.toggle_switch import ToggleSwitch
from ui.components.badge import Badge
from ui.components.search_bar import SearchBar
from ui.dialogs.mcp_editor import McpEditorDialog
from ui.dialogs.raw_json_viewer import RawJsonViewerDialog

class McpCard(QFrame):
    toggled = pyqtSignal(McpServer, bool)
    edited = pyqtSignal(McpServer)
    deleted = pyqtSignal(McpServer)
    synced = pyqtSignal(McpServer)

    def __init__(self, mcp: McpServer, parent=None):
        super().__init__(parent)
        self.mcp = mcp
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            McpCard {
                background-color: #161924;
                border: 1px solid #232736;
                border-radius: 8px;
                padding: 12px;
            }
            McpCard:hover {
                border: 1px solid #38bdf8;
                background-color: #191d2a;
            }
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        # Header Row
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        # Left Info
        self.name_lbl = QLabel(self.mcp.name)
        self.name_lbl.setObjectName("cardTitle")

        self.type_badge = Badge(self.mcp.display_type, variant=self.mcp.display_type)
        self.status_badge = Badge("ATIVO" if self.mcp.enabled else "INATIVO", variant="active" if self.mcp.enabled else "inactive")

        # Scope badge (Global vs Project vs Cloud)
        if self.mcp.scope == "project" and self.mcp.project_path:
            home = os.path.expanduser("~")
            short_p = "~" if self.mcp.project_path == home else os.path.basename(self.mcp.project_path)
            self.scope_badge = Badge(f"PROJ: {short_p}", variant="project")
            self.scope_badge.setToolTip(f"Escopo do Projeto: {self.mcp.project_path}")
        elif self.mcp.scope == "cloud":
            self.scope_badge = Badge("CLAUDE.AI", variant="cloud")
            self.scope_badge.setToolTip("Integração Cloud Claude.ai (OAuth)")
        else:
            self.scope_badge = Badge("GLOBAL", variant="global")
            self.scope_badge.setToolTip("Escopo Global (Todos os Projetos)")

        top_row.addWidget(self.name_lbl)
        top_row.addWidget(self.scope_badge)
        top_row.addWidget(self.type_badge)
        top_row.addWidget(self.status_badge)
        top_row.addStretch()

        # Toggle Switch
        self.switch = ToggleSwitch(checked=self.mcp.enabled)
        self.switch.toggled.connect(self._on_toggled)
        top_row.addWidget(self.switch)

        # Action Buttons
        self.edit_btn = QPushButton("Editar")
        self.edit_btn.setObjectName("secondaryBtn")
        self.edit_btn.setIcon(qta.icon('fa5s.edit', color='#cbd5e1'))
        self.edit_btn.clicked.connect(lambda: self.edited.emit(self.mcp))
        top_row.addWidget(self.edit_btn)

        self.sync_btn = QPushButton()
        self.sync_btn.setObjectName("secondaryBtn")
        self.sync_btn.setIcon(qta.icon('fa5s.share-alt', color='#818cf8'))
        self.sync_btn.setToolTip("Copiar este MCP para outro agente")
        self.sync_btn.clicked.connect(lambda: self.synced.emit(self.mcp))
        top_row.addWidget(self.sync_btn)

        self.del_btn = QPushButton()
        self.del_btn.setObjectName("dangerBtn")
        self.del_btn.setIcon(qta.icon('fa5s.trash', color='white'))
        self.del_btn.setToolTip("Excluir MCP Server")
        self.del_btn.clicked.connect(lambda: self.deleted.emit(self.mcp))
        top_row.addWidget(self.del_btn)

        layout.addLayout(top_row)

        # Details Snippet
        snippet_row = QHBoxLayout()
        snippet_box = QFrame()
        snippet_box.setStyleSheet("background-color: #0f1118; border: 1px solid #1e2230; border-radius: 6px; padding: 6px 10px;")
        s_layout = QHBoxLayout(snippet_box)
        s_layout.setContentsMargins(6, 4, 6, 4)

        icon_name = 'fa5s.globe' if self.mcp.is_remote else 'fa5s.terminal'
        snippet_icon = QLabel()
        snippet_icon.setPixmap(qta.icon(icon_name, color='#94a3b8').pixmap(14, 14))
        s_layout.addWidget(snippet_icon)

        cmd_text = self.mcp.command_display or "(Sem comando configurado)"
        self.cmd_lbl = QLabel(cmd_text)
        self.cmd_lbl.setStyleSheet("font-family: monospace; color: #38bdf8; font-size: 11px;")
        s_layout.addWidget(self.cmd_lbl, 1)

        copy_btn = QPushButton()
        copy_btn.setIcon(qta.icon('fa5s.copy', color='#64748b'))
        copy_btn.setFixedSize(22, 22)
        copy_btn.setToolTip("Copiar comando")
        copy_btn.setStyleSheet("background: transparent; border: none;")
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(cmd_text))
        s_layout.addWidget(copy_btn)

        snippet_row.addWidget(snippet_box, 1)

        # Env / Headers count tags
        if self.mcp.env:
            env_tag = QLabel(f"⚡ {len(self.mcp.env)} env vars")
            env_tag.setStyleSheet("color: #fbbf24; font-size: 11px; padding: 0 4px;")
            snippet_row.addWidget(env_tag)

        if self.mcp.headers:
            hdr_tag = QLabel(f"🔑 {len(self.mcp.headers)} headers")
            hdr_tag.setStyleSheet("color: #a78bfa; font-size: 11px; padding: 0 4px;")
            snippet_row.addWidget(hdr_tag)

        layout.addLayout(snippet_row)

    def _on_toggled(self, checked: bool):
        self.status_badge.setText("ATIVO" if checked else "INATIVO")
        self.status_badge.set_variant("active" if checked else "inactive")
        self.toggled.emit(self.mcp, checked)

class McpPanel(QWidget):
    statusChanged = pyqtSignal(str)

    def __init__(self, agent_name: str, config_manager, sync_callback=None, parent=None):
        super().__init__(parent)
        self.agent_name = agent_name
        self.config_manager = config_manager
        self.sync_callback = sync_callback
        self.mcps: list[McpServer] = []
        self._setup_ui()
        self.reload_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Top Bar
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        # Search
        self.search_bar = SearchBar(placeholder="Buscar MCP Server por nome ou comando...")
        self.search_bar.textChanged.connect(self._filter_items)
        top_bar.addWidget(self.search_bar, 1)

        # Filter Status
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Todos os Status", "Apenas Habilitados", "Apenas Desabilitados"])
        self.filter_combo.currentTextChanged.connect(self._filter_items)
        top_bar.addWidget(self.filter_combo)

        # Add Button
        self.add_btn = QPushButton("+ Adicionar MCP")
        self.add_btn.setObjectName("primaryBtn")
        self.add_btn.setIcon(qta.icon('fa5s.plus', color='white'))
        self.add_btn.clicked.connect(self._add_mcp)
        top_bar.addWidget(self.add_btn)

        # Raw Config button
        self.raw_btn = QPushButton("Config JSON")
        self.raw_btn.setObjectName("secondaryBtn")
        self.raw_btn.setIcon(qta.icon('fa5s.code', color='#38bdf8'))
        self.raw_btn.setToolTip("Visualizar e editar JSON de configuração diretamente")
        self.raw_btn.clicked.connect(self._open_raw_config)
        top_bar.addWidget(self.raw_btn)

        # Reload button
        self.reload_btn = QPushButton()
        self.reload_btn.setObjectName("secondaryBtn")
        self.reload_btn.setIcon(qta.icon('fa5s.redo', color='#cbd5e1'))
        self.reload_btn.setToolTip("Recarregar do disco")
        self.reload_btn.clicked.connect(self.reload_data)
        top_bar.addWidget(self.reload_btn)

        layout.addLayout(top_bar)

        # Scroll Area for Cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(10)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.addStretch()

        self.scroll_area.setWidget(self.cards_container)
        layout.addWidget(self.scroll_area, 1)

    def reload_data(self):
        self.mcps = self.config_manager.list_mcps()
        self._render_cards()
        self.statusChanged.emit(f"{len(self.mcps)} MCP Servers carregados para {self.agent_name}")

    def _render_cards(self):
        # Clear existing cards
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        query = self.search_bar.text().lower().strip()
        status_filter = self.filter_combo.currentText()

        filtered_count = 0
        for mcp in self.mcps:
            # Check search
            if query and query not in mcp.name.lower() and query not in mcp.command_display.lower():
                continue
            # Check status
            if "Habilitados" in status_filter and not mcp.enabled:
                continue
            if "Desabilitados" in status_filter and mcp.enabled:
                continue

            card = McpCard(mcp)
            card.toggled.connect(self._on_mcp_toggled)
            card.edited.connect(self._on_mcp_edited)
            card.deleted.connect(self._on_mcp_deleted)
            card.synced.connect(self._on_mcp_synced)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
            filtered_count += 1

        if filtered_count == 0:
            empty_lbl = QLabel("Nenhum MCP Server encontrado correspondente ao filtro.")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setStyleSheet("color: #64748b; padding: 40px; font-size: 14px;")
            self.cards_layout.insertWidget(0, empty_lbl)

    def _filter_items(self):
        self._render_cards()

    def _on_mcp_toggled(self, mcp: McpServer, enabled: bool):
        if hasattr(self.config_manager, 'toggle_mcp'):
            import inspect
            sig = inspect.signature(self.config_manager.toggle_mcp)
            if 'project_path' in sig.parameters:
                success = self.config_manager.toggle_mcp(mcp.name, enabled, project_path=mcp.project_path)
            else:
                success = self.config_manager.toggle_mcp(mcp.name, enabled)
        else:
            success = False

        if success:
            state_str = "habilitado" if enabled else "desabilitado"
            self.statusChanged.emit(f"MCP '{mcp.name}' {state_str} com sucesso em {self.agent_name}.")
        else:
            QMessageBox.critical(self, "Erro", f"Falha ao alterar estado do MCP {mcp.name}.")
            self.reload_data()

    def _add_mcp(self):
        dialog = McpEditorDialog(agent_name=self.agent_name, parent=self)
        if dialog.exec():
            new_mcp = dialog.result_mcp
            success = self.config_manager.save_mcp(new_mcp)
            if success:
                self.statusChanged.emit(f"MCP '{new_mcp.name}' adicionado com sucesso!")
                self.reload_data()
            else:
                QMessageBox.critical(self, "Erro", f"Falha ao salvar MCP {new_mcp.name}.")

    def _on_mcp_edited(self, mcp: McpServer):
        dialog = McpEditorDialog(mcp=mcp, agent_name=self.agent_name, parent=self)
        if dialog.exec():
            updated_mcp = dialog.result_mcp
            # preserve scope and project_path
            updated_mcp.scope = mcp.scope
            updated_mcp.project_path = mcp.project_path
            success = self.config_manager.save_mcp(updated_mcp)
            if success:
                self.statusChanged.emit(f"MCP '{updated_mcp.name}' atualizado com sucesso!")
                self.reload_data()
            else:
                QMessageBox.critical(self, "Erro", f"Falha ao atualizar MCP {updated_mcp.name}.")

    def _on_mcp_deleted(self, mcp: McpServer):
        scope_info = f" (Projeto: {mcp.project_path})" if mcp.project_path else ""
        reply = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Tem certeza que deseja remover o MCP Server '{mcp.name}'{scope_info} de {self.agent_name}?\n\nUm backup automático da configuração será mantido.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            import inspect
            sig = inspect.signature(self.config_manager.delete_mcp)
            if 'project_path' in sig.parameters:
                success = self.config_manager.delete_mcp(mcp.name, project_path=mcp.project_path)
            else:
                success = self.config_manager.delete_mcp(mcp.name)

            if success:
                self.statusChanged.emit(f"MCP '{mcp.name}' removido com sucesso.")
                self.reload_data()
            else:
                QMessageBox.critical(self, "Erro", f"Falha ao excluir MCP {mcp.name}.")

    def _on_mcp_synced(self, mcp: McpServer):
        if self.sync_callback:
            self.sync_callback(self.agent_name, mcp)

    def _open_raw_config(self):
        path = self.config_manager.get_raw_config_path()
        data = self.config_manager.get_raw_config()
        dialog = RawJsonViewerDialog(
            title=f"{self.agent_name} Settings",
            file_path=path,
            initial_content=data,
            save_callback=self.config_manager.save_raw_config,
            parent=self
        )
        if dialog.exec():
            self.reload_data()
