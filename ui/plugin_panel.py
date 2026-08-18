from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QComboBox, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
import qtawesome as qta
import subprocess
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
                background-color: #161924;
                border: 1px solid #232736;
                border-radius: 8px;
                padding: 12px;
            }
            PluginSkillCard:hover {
                border: 1px solid #6366f1;
                background-color: #191d2a;
            }
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        # Top Header
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        # Name and Badges
        self.name_lbl = QLabel(self.item.name)
        self.name_lbl.setObjectName("cardTitle")

        self.kind_badge = Badge(self.item.display_kind, variant=self.item.kind)
        self.status_badge = Badge("ATIVO" if self.item.enabled else "INATIVO", variant="active" if self.item.enabled else "inactive")

        top_row.addWidget(self.name_lbl)
        top_row.addWidget(self.kind_badge)
        top_row.addWidget(self.status_badge)
        top_row.addStretch()

        # Toggle Switch
        self.switch = ToggleSwitch(checked=self.item.enabled)
        self.switch.toggled.connect(self._on_toggled)
        top_row.addWidget(self.switch)

        # Actions
        if self.item.kind == "skill" or (self.item.path and os.path.exists(os.path.join(self.item.path, "SKILL.md"))):
            self.edit_btn = QPushButton("Ver/Editar")
            self.edit_btn.setObjectName("secondaryBtn")
            self.edit_btn.setIcon(qta.icon('fa5s.edit', color='#cbd5e1'))
            self.edit_btn.clicked.connect(lambda: self.edited.emit(self.item))
            top_row.addWidget(self.edit_btn)

        if self.item.path and os.path.exists(self.item.path):
            self.folder_btn = QPushButton()
            self.folder_btn.setObjectName("secondaryBtn")
            self.folder_btn.setIcon(qta.icon('fa5s.folder-open', color='#fbbf24'))
            self.folder_btn.setToolTip("Abrir pasta local no explorador de arquivos")
            self.folder_btn.clicked.connect(self._open_folder)
            top_row.addWidget(self.folder_btn)

        self.del_btn = QPushButton()
        self.del_btn.setObjectName("dangerBtn")
        self.del_btn.setIcon(qta.icon('fa5s.trash', color='white'))
        self.del_btn.setToolTip("Remover plugin / skill")
        self.del_btn.clicked.connect(lambda: self.deleted.emit(self.item))
        top_row.addWidget(self.del_btn)

        layout.addLayout(top_row)

        # Description / Source Info
        desc_text = self.item.description or self.item.source or "(Sem descrição disponível)"
        self.desc_lbl = QLabel(desc_text)
        self.desc_lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")
        self.desc_lbl.setWordWrap(True)
        layout.addWidget(self.desc_lbl)

        # Source snippet if available
        if self.item.source and self.item.source != self.item.name:
            src_lbl = QLabel(f"Origem: <code style='color:#38bdf8;'>{self.item.source}</code>")
            src_lbl.setStyleSheet("font-size: 11px; color: #64748b;")
            layout.addWidget(src_lbl)

    def _open_folder(self):
        if self.item.path and os.path.exists(self.item.path):
            try:
                subprocess.Popen(["xdg-open", self.item.path])
            except Exception as e:
                print(f"Error opening folder: {e}")

    def _on_toggled(self, checked: bool):
        self.status_badge.setText("ATIVO" if checked else "INATIVO")
        self.status_badge.set_variant("active" if checked else "inactive")
        self.toggled.emit(self.item, checked)

class PluginPanel(QWidget):
    statusChanged = pyqtSignal(str)

    def __init__(self, agent_name: str, config_manager, parent=None):
        super().__init__(parent)
        self.agent_name = agent_name
        self.config_manager = config_manager
        self.items: list[PluginSkill] = []
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
        self.search_bar = SearchBar(placeholder="Buscar Plugins ou Skills...")
        self.search_bar.textChanged.connect(self._filter_items)
        top_bar.addWidget(self.search_bar, 1)

        # Filter Kind
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Todos os Tipos", "Apenas Plugins", "Apenas Skills", "Apenas Extensões"])
        self.filter_combo.currentTextChanged.connect(self._filter_items)
        top_bar.addWidget(self.filter_combo)

        # Filter Status
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems(["Todos Status", "Habilitados", "Desabilitados"])
        self.status_filter_combo.currentTextChanged.connect(self._filter_items)
        top_bar.addWidget(self.status_filter_combo)

        # Add Plugin Button
        self.add_plugin_btn = QPushButton("+ Instalar Plugin")
        self.add_plugin_btn.setObjectName("primaryBtn")
        self.add_plugin_btn.setIcon(qta.icon('fa5s.puzzle-piece', color='white'))
        self.add_plugin_btn.clicked.connect(self._add_plugin)
        top_bar.addWidget(self.add_plugin_btn)

        # Add Skill Button
        self.add_skill_btn = QPushButton("+ Nova Skill")
        self.add_skill_btn.setObjectName("secondaryBtn")
        self.add_skill_btn.setIcon(qta.icon('fa5s.magic', color='#818cf8'))
        self.add_skill_btn.clicked.connect(self._add_skill)
        top_bar.addWidget(self.add_skill_btn)

        # Reload button
        self.reload_btn = QPushButton()
        self.reload_btn.setObjectName("secondaryBtn")
        self.reload_btn.setIcon(qta.icon('fa5s.redo', color='#cbd5e1'))
        self.reload_btn.clicked.connect(self.reload_data)
        top_bar.addWidget(self.reload_btn)

        layout.addLayout(top_bar)

        # Scroll Area
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
        self.items = self.config_manager.list_plugins_and_skills()
        self._render_cards()
        self.statusChanged.emit(f"{len(self.items)} Plugins e Skills carregados para {self.agent_name}")

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
