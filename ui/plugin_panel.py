from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QComboBox, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtGui import QDesktopServices
import qtawesome as qta
import os

from models.plugin import PluginSkill
from ui.components.toggle_switch import ToggleSwitch
from ui.components.badge import Badge
from ui.components.search_bar import SearchBar
from ui.dialogs.plugin_editor import PluginEditorDialog
from ui.dialogs.skill_editor import SkillEditorDialog

class PluginSkillCard(QFrame):
    toggled = pyqtSignal(PluginSkill, bool)
    edited = pyqtSignal(PluginSkill)
    deleted = pyqtSignal(PluginSkill)

    def __init__(self, item: PluginSkill, parent=None):
        super().__init__(parent)
        self.item = item
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            PluginSkillCard {
                background-color: #12151f;
                border: 1px solid #1e2230;
                border-radius: 8px;
                padding: 10px 12px;
            }
            PluginSkillCard:hover {
                border: 1px solid #283044;
                background-color: #151824;
            }
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)

        # Top Header
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        # Name and Badges
        self.name_lbl = QLabel(self.item.name)
        self.name_lbl.setObjectName("cardTitle")
        self.name_lbl.setStyleSheet("background: transparent; border: none; font-size: 14px; font-weight: 700; color: #f8fafc;")

        self.kind_badge = Badge(self.item.display_kind, variant=self.item.kind)
        self.status_badge = Badge("ATIVO" if self.item.enabled else "INATIVO", variant="active" if self.item.enabled else "inactive")

        top_row.addWidget(self.name_lbl)
        
        # Scope badge if project-level
        if self.item.metadata and self.item.metadata.get("scope") == "project":
            p_path = self.item.metadata.get("project_path", "")
            p_name = os.path.basename(p_path) if p_path else "PROJ"
            self.scope_badge = Badge(f"PROJ: {p_name}", variant="project")
            self.scope_badge.setToolTip(f"Skill local do projeto: {p_path}")
            top_row.addWidget(self.scope_badge)

        top_row.addWidget(self.kind_badge)
        top_row.addWidget(self.status_badge)
        top_row.addStretch()

        # Toggle Switch
        self.switch = ToggleSwitch(checked=self.item.enabled)
        self.switch.toggled.connect(self._on_toggled)
        top_row.addWidget(self.switch)

        # Action Buttons
        if self.item.kind == "skill" or (self.item.path and os.path.exists(os.path.join(self.item.path, "SKILL.md"))):
            self.edit_btn = QPushButton()
            self.edit_btn.setObjectName("editIconBtn")
            self.edit_btn.setIcon(qta.icon('fa5s.pen', color='#94a3b8'))
            self.edit_btn.setFixedSize(28, 28)
            self.edit_btn.setToolTip("Ver/Editar SKILL.md")
            self.edit_btn.clicked.connect(lambda: self.edited.emit(self.item))
            top_row.addWidget(self.edit_btn)

        if self.item.path and os.path.exists(self.item.path):
            self.folder_btn = QPushButton()
            self.folder_btn.setObjectName("iconBtn")
            self.folder_btn.setIcon(qta.icon('fa5s.folder-open', color='#fbbf24'))
            self.folder_btn.setFixedSize(28, 28)
            self.folder_btn.setToolTip("Abrir pasta local no explorador de arquivos")
            self.folder_btn.clicked.connect(self._open_folder)
            top_row.addWidget(self.folder_btn)

        self.del_btn = QPushButton()
        self.del_btn.setObjectName("dangerIconBtn")
        self.del_btn.setIcon(qta.icon('fa5s.trash-alt', color='#94a3b8'))
        self.del_btn.setFixedSize(28, 28)
        self.del_btn.setToolTip("Remover plugin / skill")
        self.del_btn.clicked.connect(lambda: self.deleted.emit(self.item))
        top_row.addWidget(self.del_btn)

        layout.addLayout(top_row)

        # Description / Source Box
        desc_box = QFrame()
        desc_box.setStyleSheet("""
            QFrame {
                background-color: #090b10;
                border: 1px solid #181b26;
                border-radius: 6px;
                padding: 4px 8px;
            }
        """)
        d_layout = QHBoxLayout(desc_box)
        d_layout.setContentsMargins(6, 4, 6, 4)
        d_layout.setSpacing(8)

        desc_text = self.item.description or self.item.source or "(Sem descrição disponível)"
        self.desc_lbl = QLabel(desc_text)
        self.desc_lbl.setStyleSheet("background: transparent; border: none; color: #94a3b8; font-size: 11px;")
        self.desc_lbl.setWordWrap(True)
        d_layout.addWidget(self.desc_lbl, 1)

        # Source snippet if available
        if self.item.source and self.item.source != self.item.name:
            import html
            safe_source = html.escape(self.item.source)
            src_lbl = QLabel(f"<code>{safe_source}</code>")
            src_lbl.setStyleSheet("background: transparent; border: none; font-size: 10px; color: #38bdf8; font-family: monospace;")
            d_layout.addWidget(src_lbl)

        layout.addWidget(desc_box)

    def _open_folder(self):
        if self.item.path and os.path.exists(self.item.path):
            try:
                QDesktopServices.openUrl(QUrl.fromLocalFile(self.item.path))
            except Exception as e:
                print(f"Error opening folder: {e}")

    def _on_toggled(self, checked: bool):
        self.status_badge.set_variant("active" if checked else "inactive", text="ATIVO" if checked else "INATIVO")
        self.toggled.emit(self.item, checked)

class PluginPanel(QWidget):
    statusChanged = pyqtSignal(str)

    def __init__(self, agent_name: str, config_manager, parent=None):
        super().__init__(parent)
        self.agent_name = agent_name
        self.config_manager = config_manager
        self.items: list[PluginSkill] = []
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
        self.search_bar = SearchBar(placeholder="Buscar Plugins ou Skills...")
        self.search_bar.textChanged.connect(self._filter_items)
        top_bar.addWidget(self.search_bar, 3)

        # Scope Filter (Default: Global)
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

        # Filter Kind
        kind_lbl = QLabel("Tipo:")
        kind_lbl.setStyleSheet("font-size: 11px; color: #94a3b8; font-weight: 500;")
        top_bar.addWidget(kind_lbl)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Todos os Tipos", "Apenas Plugins", "Apenas Skills", "Apenas Extensões"])
        self.filter_combo.currentTextChanged.connect(self._filter_items)
        top_bar.addWidget(self.filter_combo, 1)

        # Filter Status
        status_lbl = QLabel("Select:")
        status_lbl.setStyleSheet("font-size: 11px; color: #94a3b8; font-weight: 500;")
        top_bar.addWidget(status_lbl)

        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems(["Todos Status", "● Habilitados", "● Desabilitados"])
        self.status_filter_combo.currentTextChanged.connect(self._filter_items)
        top_bar.addWidget(self.status_filter_combo, 1)

        # Add Skill Button
        self.add_skill_btn = QPushButton("+ Nova Skill")
        self.add_skill_btn.setObjectName("primaryBtn")
        self.add_skill_btn.setIcon(qta.icon('fa5s.magic', color='white'))
        self.add_skill_btn.clicked.connect(self._add_skill)
        top_bar.addWidget(self.add_skill_btn)

        # Add Plugin Button
        self.add_plugin_btn = QPushButton("+ Instalar Plugin")
        self.add_plugin_btn.setObjectName("secondaryBtn")
        self.add_plugin_btn.setIcon(qta.icon('fa5s.puzzle-piece', color='#94a3b8'))
        self.add_plugin_btn.clicked.connect(self._add_plugin)
        top_bar.addWidget(self.add_plugin_btn)

        # Reload button
        self.reload_btn = QPushButton()
        self.reload_btn.setObjectName("secondaryBtn")
        self.reload_btn.setIcon(qta.icon('fa5s.redo', color='#94a3b8'))
        self.reload_btn.setToolTip("Recarregar do disco")
        self.reload_btn.setFixedSize(30, 28)
        self.reload_btn.clicked.connect(lambda: self.reload_data())
        top_bar.addWidget(self.reload_btn)

        layout.addLayout(top_bar)

        # Scroll Area
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
        if hasattr(self.parent(), 'on_scope_changed_from_panel'):
            self.parent().on_scope_changed_from_panel(self.project_path, source="plugin")

    def reload_data(self, project_path: str = None):
        self.project_path = getattr(self, 'project_path', "__ALL__") if project_path is None else project_path
        if hasattr(self.config_manager, 'list_plugins_and_skills'):
            import inspect
            sig = inspect.signature(self.config_manager.list_plugins_and_skills)
            if 'project_path' in sig.parameters:
                self.items = self.config_manager.list_plugins_and_skills(self.project_path)
            else:
                self.items = self.config_manager.list_plugins_and_skills()
        else:
            self.items = []
        self._render_cards()
        self.statusChanged.emit(f"{len(self.items)} Plugins e Skills carregados para {self.agent_name}")

    def set_project_filter(self, project_path: str = None):
        self.project_path = project_path
        self.reload_data(project_path)

    def _render_cards(self):
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        query = self.search_bar.text().lower().strip()
        kind_filter = self.filter_combo.currentText()
        status_filter = self.status_filter_combo.currentText()

        filtered_count = 0
        for it in self.items:
            # Check project filter
            if hasattr(self, 'project_path') and self.project_path:
                if self.project_path == "GLOBAL":
                    # Only global
                    if it.metadata and it.metadata.get("scope") == "project":
                        continue
                elif self.project_path != "__ALL__":
                    # Must match project or be global
                    if it.metadata and it.metadata.get("scope") == "project":
                        if it.metadata.get("project_path") != self.project_path:
                            continue

            if query and query not in it.name.lower() and query not in it.description.lower() and query not in it.source.lower():
                continue

            if "Plugins" in kind_filter and it.kind != "plugin":
                continue
            if "Skills" in kind_filter and it.kind != "skill":
                continue
            if "Extensões" in kind_filter and it.kind != "extension":
                continue

            if "Habilitados" in status_filter and not it.enabled:
                continue
            if "Desabilitados" in status_filter and it.enabled:
                continue

            card = PluginSkillCard(it)
            card.toggled.connect(self._on_item_toggled)
            card.edited.connect(self._on_item_edited)
            card.deleted.connect(self._on_item_deleted)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
            filtered_count += 1

        if filtered_count == 0:
            empty_lbl = QLabel("Nenhum Plugin ou Skill encontrado correspondente ao filtro.")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setStyleSheet("color: #64748b; padding: 40px; font-size: 14px;")
            self.cards_layout.insertWidget(0, empty_lbl)

    def _filter_items(self):
        self._render_cards()

    def _on_item_toggled(self, item: PluginSkill, enabled: bool):
        success = self.config_manager.toggle_plugin_skill(item, enabled)
        if success:
            state_str = "habilitado" if enabled else "desabilitado"
            self.statusChanged.emit(f"{item.display_kind} '{item.name}' {state_str} com sucesso em {self.agent_name}.")
        else:
            QMessageBox.critical(self, "Erro", f"Falha ao alterar estado de {item.name}.")
            self.reload_data()

    def _add_plugin(self):
        dialog = PluginEditorDialog(agent_name=self.agent_name, parent=self)
        if dialog.exec():
            data = dialog.plugin_data
            name = data["name"]
            success = False
            if hasattr(self.config_manager, 'add_plugin'):
                if "Claude" in self.agent_name:
                    success = self.config_manager.add_plugin(
                        plugin_id=name,
                        marketplace_name=data.get("marketplace", ""),
                        repo_or_url=data.get("source", ""),
                        source_type=data.get("source_type", "github")
                    )
                else: # OpenCode
                    success = self.config_manager.add_plugin(data.get("source") or name)
            else:
                QMessageBox.information(self, "Aviso", f"Adição de plugins em {self.agent_name} é gerenciada via arquivos de extensão ou skills.")
                return

            if success:
                self.statusChanged.emit(f"Plugin '{name}' adicionado com sucesso!")
                self.reload_data()
            else:
                QMessageBox.critical(self, "Erro", f"Falha ao adicionar plugin {name}.")

    def _add_skill(self):
        dialog = SkillEditorDialog(agent_name=self.agent_name, parent=self)
        if dialog.exec():
            data = dialog.skill_data
            success = self.config_manager.add_skill(
                name=data["name"],
                description=data["description"],
                instructions=data["instructions"]
            )
            if success:
                self.statusChanged.emit(f"Skill '{data['name']}' criada com sucesso!")
                self.reload_data()
            else:
                QMessageBox.critical(self, "Erro", f"Falha ao criar skill {data['name']}.")

    def _on_item_edited(self, item: PluginSkill):
        skill_md = os.path.join(item.path, "SKILL.md") if item.path else ""
        inst = ""
        if os.path.exists(skill_md):
            try:
                with open(skill_md, 'r', encoding='utf-8') as f:
                    inst = f.read()
            except Exception:
                pass

        dialog = SkillEditorDialog(
            agent_name=self.agent_name,
            skill_name=item.name,
            skill_desc=item.description,
            instructions=inst,
            parent=self
        )
        if dialog.exec():
            data = dialog.skill_data
            if os.path.exists(skill_md):
                try:
                    with open(skill_md, 'w', encoding='utf-8') as f:
                        f.write(data["instructions"])
                    self.statusChanged.emit(f"Skill '{item.name}' atualizada com sucesso!")
                    self.reload_data()
                except Exception as e:
                    QMessageBox.critical(self, "Erro", f"Falha ao atualizar SKILL.md: {e}")

    def _on_item_deleted(self, item: PluginSkill):
        reply = QMessageBox.question(
            self,
            "Confirmar Remoção",
            f"Tem certeza que deseja remover o {item.display_kind} '{item.name}' de {self.agent_name}?\n\nUma cópia de segurança será mantida.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            success = self.config_manager.delete_plugin_skill(item)
            if success:
                self.statusChanged.emit(f"{item.display_kind} '{item.name}' removido com sucesso.")
                self.reload_data()
            else:
                QMessageBox.critical(self, "Erro", f"Falha ao remover {item.name}.")
