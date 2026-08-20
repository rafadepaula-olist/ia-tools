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
    promoted_global = pyqtSignal(McpServer)
    shelved = pyqtSignal(McpServer)
    unshelved = pyqtSignal(McpServer)

    def __init__(self, mcp: McpServer, parent=None):
        super().__init__(parent)
        self.mcp = mcp
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            McpCard {
                background-color: #12151f;
                border: 1px solid #1e2230;
                border-radius: 8px;
                padding: 10px 12px;
            }
            McpCard:hover {
                border: 1px solid #283044;
                background-color: #151824;
            }
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header Row
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        # Left: Name and Badges
        self.name_lbl = QLabel(self.mcp.name)
        self.name_lbl.setObjectName("cardTitle")
        self.name_lbl.setStyleSheet("background: transparent; border: none; font-size: 14px; font-weight: 700; color: #f8fafc;")

        # Scope badge
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

        self.type_badge = Badge(self.mcp.display_type, variant=self.mcp.display_type)
        
        if self.mcp.shelved:
            self.status_badge = Badge("TEMPORÁRIO", variant="shelved")
            self.status_badge.setToolTip("Removido da config ativa para economizar recursos")
        else:
            self.status_badge = Badge("ATIVO" if self.mcp.enabled else "INATIVO", variant="active" if self.mcp.enabled else "inactive")

        top_row.addWidget(self.name_lbl)
        top_row.addWidget(self.scope_badge)
        top_row.addWidget(self.type_badge)
        top_row.addWidget(self.status_badge)
        top_row.addStretch()

        # Right Controls: ToggleSwitch + Action Icon Buttons
        self.switch = ToggleSwitch(checked=self.mcp.enabled and not self.mcp.shelved)
        self.switch.setEnabled(not self.mcp.shelved)
        if self.mcp.shelved:
            self.switch.setToolTip("MCP temporariamente removido. Clique em 'Restaurar' para habilitar.")
        self.switch.toggled.connect(self._on_toggled)
        top_row.addWidget(self.switch)

        # Minimal icon buttons
        if self.mcp.scope == "project":
            self.promote_btn = QPushButton()
            self.promote_btn.setObjectName("iconBtn")
            self.promote_btn.setIcon(qta.icon('fa5s.globe', color='#38bdf8'))
            self.promote_btn.setFixedSize(28, 28)
            self.promote_btn.setToolTip("Transformar este MCP de Projeto em MCP Global")
            self.promote_btn.clicked.connect(lambda: self.promoted_global.emit(self.mcp))
            top_row.addWidget(self.promote_btn)

        if self.mcp.shelved:
            self.restore_btn = QPushButton()
            self.restore_btn.setObjectName("iconBtn")
            self.restore_btn.setIcon(qta.icon('fa5s.trash-restore', color='#34d399'))
            self.restore_btn.setFixedSize(28, 28)
            self.restore_btn.setToolTip("Restaurar este MCP de volta para a configuração ativa")
            self.restore_btn.clicked.connect(lambda: self.unshelved.emit(self.mcp))
            top_row.addWidget(self.restore_btn)
        else:
            self.shelve_btn = QPushButton()
            self.shelve_btn.setObjectName("iconBtn")
            self.shelve_btn.setIcon(qta.icon('fa5s.pause-circle', color='#94a3b8'))
            self.shelve_btn.setFixedSize(28, 28)
            self.shelve_btn.setToolTip("Remover temporariamente (desvincula da config sem perder dados)")
            self.shelve_btn.clicked.connect(lambda: self.shelved.emit(self.mcp))
            top_row.addWidget(self.shelve_btn)

        self.sync_btn = QPushButton()
        self.sync_btn.setObjectName("iconBtn")
        self.sync_btn.setIcon(qta.icon('fa5s.clone', color='#94a3b8'))
        self.sync_btn.setFixedSize(28, 28)
        self.sync_btn.setToolTip("Copiar este MCP para outro agente / provedor")
        self.sync_btn.clicked.connect(lambda: self.synced.emit(self.mcp))
        top_row.addWidget(self.sync_btn)

        self.edit_btn = QPushButton()
        self.edit_btn.setObjectName("editIconBtn")
        self.edit_btn.setIcon(qta.icon('fa5s.pen', color='#94a3b8'))
        self.edit_btn.setFixedSize(28, 28)
        self.edit_btn.setToolTip("Editar MCP Server")
        self.edit_btn.clicked.connect(lambda: self.edited.emit(self.mcp))
        top_row.addWidget(self.edit_btn)

        self.del_btn = QPushButton()
        self.del_btn.setObjectName("dangerIconBtn")
        self.del_btn.setIcon(qta.icon('fa5s.trash-alt', color='#94a3b8'))
        self.del_btn.setFixedSize(28, 28)
        self.del_btn.setToolTip("Excluir MCP Server")
        self.del_btn.clicked.connect(lambda: self.deleted.emit(self.mcp))
        top_row.addWidget(self.del_btn)

        layout.addLayout(top_row)

        # Details / Command Box
        snippet_box = QFrame()
        snippet_box.setStyleSheet("""
            QFrame {
                background-color: #090b10;
                border: 1px solid #181b26;
                border-radius: 6px;
                padding: 4px 8px;
            }
        """)
        s_layout = QHBoxLayout(snippet_box)
        s_layout.setContentsMargins(6, 3, 6, 3)
        s_layout.setSpacing(8)

        cmd_text = self.mcp.command_display_masked or "(Sem comando configurado)"
        self.cmd_lbl = QLabel(cmd_text)
        self.cmd_lbl.setStyleSheet("background: transparent; border: none; font-family: 'JetBrains Mono', 'Fira Code', 'DejaVu Sans Mono', Consolas, monospace; color: #94a3b8; font-size: 11px;")
        s_layout.addWidget(self.cmd_lbl, 1)

        # Env / Headers count tags
        if self.mcp.env:
            env_tag = QLabel(f"⚡ {len(self.mcp.env)} env")
            env_tag.setStyleSheet("background: transparent; border: none; color: #fbbf24; font-size: 10px; font-weight: 600; padding: 0 4px;")
            s_layout.addWidget(env_tag)

        if self.mcp.headers:
            hdr_tag = QLabel(f"🔑 {len(self.mcp.headers)} hdr")
            hdr_tag.setStyleSheet("background: transparent; border: none; color: #c084fc; font-size: 10px; font-weight: 600; padding: 0 4px;")
            s_layout.addWidget(hdr_tag)

        copy_btn = QPushButton()
        copy_btn.setIcon(qta.icon('fa5s.copy', color='#64748b'))
        copy_btn.setFixedSize(22, 22)
        copy_btn.setToolTip("Copiar comando")
        copy_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background: #1e2434;
            }
        """)
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(cmd_text))
        s_layout.addWidget(copy_btn)

        layout.addWidget(snippet_box)

    def _on_toggled(self, checked: bool):
        self.status_badge.set_variant("active" if checked else "inactive", text="ATIVO" if checked else "INATIVO")
        self.toggled.emit(self.mcp, checked)

class McpPanel(QWidget):
    statusChanged = pyqtSignal(str)

    def __init__(self, agent_name: str, config_manager, sync_callback=None, parent=None):
        super().__init__(parent)
        self.agent_name = agent_name
        self.config_manager = config_manager
        self.sync_callback = sync_callback
        self.mcps: list[McpServer] = []
        self.project_path = "GLOBAL"
        self._setup_ui()
        self.reload_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(8)

        # Clean Unified Filter Bar
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)

        # Search Bar
        self.search_bar = SearchBar(placeholder="Buscar MCP Server...")
        self.search_bar.textChanged.connect(self._filter_items)
        top_bar.addWidget(self.search_bar, 3)

        # Scope Filter Combo (Default: Global)
        scope_lbl = QLabel("Escopo:")
        scope_lbl.setStyleSheet("font-size: 11px; color: #94a3b8; font-weight: 500;")
        top_bar.addWidget(scope_lbl)

        self.scope_combo = QComboBox()
        self.scope_combo.addItem("Apenas Global / Home (~)", "GLOBAL")
        self.scope_combo.addItem("Todos os Escopos (Global + Projetos)", "__ALL__")
        from config_managers.base import BaseConfigManager
        for p in BaseConfigManager.get_known_projects():
            self.scope_combo.addItem(f"{os.path.basename(p)} ({p})", p)
        self.scope_combo.setCurrentIndex(0)
        self.scope_combo.currentIndexChanged.connect(self._on_scope_changed)
        top_bar.addWidget(self.scope_combo, 2)

        # Add Project Button
        self.add_proj_btn = QPushButton("Adicionar Projeto")
        self.add_proj_btn.setObjectName("secondaryBtn")
        self.add_proj_btn.setIcon(qta.icon('fa5s.folder-plus', color='#fbbf24'))
        self.add_proj_btn.setToolTip("Adicionar pasta de projeto ao seletor de escopo")
        self.add_proj_btn.clicked.connect(self._browse_and_add_project)
        top_bar.addWidget(self.add_proj_btn)

        # Status Filter Combo
        status_lbl = QLabel("Select:")
        status_lbl.setStyleSheet("font-size: 11px; color: #94a3b8; font-weight: 500;")
        top_bar.addWidget(status_lbl)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Todos os Status", "● Ativos", "● Inativos", "● Temporários"])
        self.filter_combo.currentTextChanged.connect(self._filter_items)
        top_bar.addWidget(self.filter_combo, 1)

        # Add Button
        self.add_btn = QPushButton("+ Adicionar MCP")
        self.add_btn.setObjectName("primaryBtn")
        self.add_btn.setIcon(qta.icon('fa5s.plus', color='white'))
        self.add_btn.clicked.connect(self._add_mcp)
        top_bar.addWidget(self.add_btn)

        # Raw Config button
        self.raw_btn = QPushButton()
        self.raw_btn.setObjectName("secondaryBtn")
        self.raw_btn.setIcon(qta.icon('fa5s.code', color='#94a3b8'))
        self.raw_btn.setToolTip("Visualizar/editar JSON de configuração bruta")
        self.raw_btn.setFixedSize(30, 28)
        self.raw_btn.clicked.connect(self._open_raw_config)
        top_bar.addWidget(self.raw_btn)

        # Reload button
        self.reload_btn = QPushButton()
        self.reload_btn.setObjectName("secondaryBtn")
        self.reload_btn.setIcon(qta.icon('fa5s.redo', color='#94a3b8'))
        self.reload_btn.setToolTip("Recarregar do disco")
        self.reload_btn.setFixedSize(30, 28)
        self.reload_btn.clicked.connect(lambda: self.reload_data())
        top_bar.addWidget(self.reload_btn)

        layout.addLayout(top_bar)

        # Scroll Area for Cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")

        self.cards_container = QWidget()
        self.cards_container.setStyleSheet("background: transparent; border: none;")
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(8)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.addStretch()

        self.scroll_area.setWidget(self.cards_container)
        layout.addWidget(self.scroll_area, 1)

    def _browse_and_add_project(self):
        from PyQt6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(self, "Selecionar Diretório do Projeto", os.path.expanduser("~"))
        if folder:
            from config_managers.base import BaseConfigManager
            if not BaseConfigManager.is_valid_project_path(folder):
                QMessageBox.warning(self, "Aviso", "O diretório selecionado não é válido como projeto.")
                return
            BaseConfigManager.register_known_project(folder)
            idx = self.scope_combo.findData(folder)
            if idx < 0:
                self.scope_combo.addItem(f"{os.path.basename(folder)} ({folder})", folder)
                idx = self.scope_combo.count() - 1
            self.scope_combo.setCurrentIndex(idx)

    def _on_scope_changed(self, idx: int):
        self.project_path = self.scope_combo.currentData() or "__ALL__"
        self._render_cards()
        # Notify parent AgentTab if needed
        if hasattr(self.parent(), 'on_scope_changed_from_panel'):
            self.parent().on_scope_changed_from_panel(self.project_path, source="mcp")

    def reload_data(self, project_path: str = None):
        self.project_path = getattr(self, 'project_path', "__ALL__") if project_path is None else project_path
        if hasattr(self.config_manager, 'list_mcps'):
            self.mcps = self.config_manager.list_mcps()
        else:
            self.mcps = []
        self._render_cards()
        self.statusChanged.emit(f"{len(self.mcps)} MCP Servers carregados para {self.agent_name}")

    def set_project_filter(self, project_path: str = None):
        self.project_path = project_path or "__ALL__"
        for i in range(self.scope_combo.count()):
            if self.scope_combo.itemData(i) == self.project_path:
                self.scope_combo.blockSignals(True)
                self.scope_combo.setCurrentIndex(i)
                self.scope_combo.blockSignals(False)
                break
        self.reload_data(self.project_path)

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
            # Check project filter
            if hasattr(self, 'project_path') and self.project_path:
                if self.project_path == "GLOBAL":
                    if mcp.scope == "project":
                        continue
                elif self.project_path != "__ALL__":
                    if mcp.scope == "project" and mcp.project_path != self.project_path:
                        continue

            # Check search
            if query and query not in mcp.name.lower() and query not in mcp.command_display.lower():
                continue
            # Check status
            if "Ativos" in status_filter and (not mcp.enabled or mcp.shelved):
                continue
            if "Inativos" in status_filter and (mcp.enabled or mcp.shelved):
                continue
            if "Temporários" in status_filter and not mcp.shelved:
                continue

            card = McpCard(mcp)
            card.toggled.connect(self._on_mcp_toggled)
            card.edited.connect(self._on_mcp_edited)
            card.deleted.connect(self._on_mcp_deleted)
            card.synced.connect(self._on_mcp_synced)
            card.promoted_global.connect(self._on_mcp_promoted_global)
            card.shelved.connect(self._on_mcp_shelved)
            card.unshelved.connect(self._on_mcp_unshelved)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
            filtered_count += 1

        if filtered_count == 0:
            empty_lbl = QLabel("Nenhum MCP Server encontrado correspondente ao filtro.")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setStyleSheet("color: #64748b; padding: 40px; font-size: 14px;")
            self.cards_layout.insertWidget(0, empty_lbl)

    def _filter_items(self):
        self._render_cards()

    def _on_mcp_promoted_global(self, mcp: McpServer):
        proj_name = os.path.basename(mcp.project_path) if mcp.project_path else "projeto"
        reply = QMessageBox.question(
            self,
            "Tornar MCP Global",
            f"Deseja transformar o MCP Server '{mcp.name}' (atualmente restrito ao projeto '{proj_name}') em um MCP Global?\n\nEle ficará disponível para todos os projetos do agente {self.agent_name}.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if hasattr(self.config_manager, 'convert_mcp_to_global'):
                success = self.config_manager.convert_mcp_to_global(mcp)
            else:
                mcp.scope = "global"
                mcp.project_path = None
                success = self.config_manager.save_mcp(mcp)

            if success:
                self.statusChanged.emit(f"MCP '{mcp.name}' promovido para escopo Global com sucesso!")
                self.reload_data()
            else:
                QMessageBox.critical(self, "Erro", f"Falha ao promover MCP '{mcp.name}' para global.")

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
            import inspect
            sig = inspect.signature(self.config_manager.save_mcp)
            if 'old_mcp' in sig.parameters:
                success = self.config_manager.save_mcp(updated_mcp, old_mcp=mcp)
            else:
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

    def _on_mcp_shelved(self, mcp: McpServer):
        scope_info = f" (Projeto: {mcp.project_path})" if mcp.project_path else ""
        reply = QMessageBox.question(
            self,
            "Remover Temporariamente",
            f"Deseja remover temporariamente o MCP Server '{mcp.name}'{scope_info} de {self.agent_name}?\n\n"
            f"O MCP será totalmente retirado do arquivo de configuração do provedor para evitar spawn de processos em background e consumo de recursos.\n\n"
            f"Você poderá restaurá-lo a qualquer momento com um clique no botão 'Restaurar'.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if hasattr(self.config_manager, 'shelve_mcp'):
                success = self.config_manager.shelve_mcp(mcp)
            else:
                success = False

            if success:
                self.statusChanged.emit(f"MCP '{mcp.name}' removido temporariamente de {self.agent_name}.")
                self.reload_data()
            else:
                QMessageBox.critical(self, "Erro", f"Falha ao remover temporariamente o MCP {mcp.name}.")

    def _on_mcp_unshelved(self, mcp: McpServer):
        if hasattr(self.config_manager, 'unshelve_mcp'):
            success = self.config_manager.unshelve_mcp(mcp)
        else:
            success = False

        if success:
            self.statusChanged.emit(f"MCP '{mcp.name}' restaurado com sucesso em {self.agent_name}!")
            self.reload_data()
        else:
            QMessageBox.critical(self, "Erro", f"Falha ao restaurar MCP {mcp.name}.")

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
