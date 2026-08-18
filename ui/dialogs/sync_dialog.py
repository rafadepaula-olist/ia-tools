from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QListWidget, QListWidgetItem, QPushButton, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt
import qtawesome as qta
from typing import Dict, List
from models.mcp import McpServer

class SyncDialog(QDialog):
    def __init__(self, managers: dict, initial_source="Antigravity", parent=None):
        super().__init__(parent)
        self.managers = managers
        self.setWindowTitle("Sincronizar Ferramentas entre Agentes (Import / Export)")
        self.resize(580, 520)
        self._setup_ui(initial_source)

    def _setup_ui(self, initial_source: str):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(18, 18, 18, 18)

        # Agent Selectors
        sel_box = QHBoxLayout()
        
        # Source
        src_group = QGroupBox("Origem (Copiar de)")
        s_layout = QVBoxLayout(src_group)
        self.src_combo = QComboBox()
        self.src_combo.addItems(["Antigravity", "Claude", "OpenCode"])
        self.src_combo.setCurrentText(initial_source)
        self.src_combo.currentTextChanged.connect(self._load_source_items)
        s_layout.addWidget(self.src_combo)
        sel_box.addWidget(src_group)

        # Arrow icon
        arrow_lbl = QLabel()
        arrow_lbl.setPixmap(qta.icon('fa5s.arrow-right', color='#818cf8').pixmap(24, 24))
        arrow_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sel_box.addWidget(arrow_lbl)

        # Target
        tgt_group = QGroupBox("Destino (Importar para)")
        t_layout = QVBoxLayout(tgt_group)
        self.tgt_combo = QComboBox()
        self.tgt_combo.addItems(["Antigravity", "Claude", "OpenCode"])
        # Default target different from source
        for idx in range(self.tgt_combo.count()):
            if self.tgt_combo.itemText(idx) != initial_source:
                self.tgt_combo.setCurrentIndex(idx)
                break
        t_layout.addWidget(self.tgt_combo)
        sel_box.addWidget(tgt_group)

        layout.addLayout(sel_box)

        # Items List
        items_group = QGroupBox("Selecione os MCP Servers para Sincronizar:")
        i_layout = QVBoxLayout(items_group)

        self.list_widget = QListWidget()
        i_layout.addWidget(self.list_widget)

        # Select all / Deselect all
        sel_btn_row = QHBoxLayout()
        sel_all_btn = QPushButton("Selecionar Todos")
        sel_all_btn.setObjectName("secondaryBtn")
        sel_all_btn.clicked.connect(self._select_all)
        
        desel_all_btn = QPushButton("Desmarcar Todos")
        desel_all_btn.setObjectName("secondaryBtn")
        desel_all_btn.clicked.connect(self._deselect_all)

        sel_btn_row.addWidget(sel_all_btn)
        sel_btn_row.addWidget(desel_all_btn)
        sel_btn_row.addStretch()
        i_layout.addLayout(sel_btn_row)

        layout.addWidget(items_group, 1)

        # Action Buttons
        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.clicked.connect(self.reject)

        sync_btn = QPushButton("Copiar MCPs Selecionados")
        sync_btn.setObjectName("primaryBtn")
        sync_btn.setIcon(qta.icon('fa5s.sync', color='white'))
        sync_btn.clicked.connect(self._on_sync)

        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(sync_btn)
        layout.addLayout(btn_row)

        self._load_source_items()

    def _load_source_items(self):
        self.list_widget.clear()
        src_name = self.src_combo.currentText()
        mgr = self.managers.get(src_name)
        if not mgr:
            return

        self.loaded_mcps: List[McpServer] = mgr.list_mcps()
        for mcp in self.loaded_mcps:
            item = QListWidgetItem(f"{mcp.name}  ({mcp.display_type}) - {mcp.command_display[:50]}")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            item.setData(Qt.ItemDataRole.UserRole, mcp)
            self.list_widget.addItem(item)

    def _select_all(self):
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.CheckState.Checked)

    def _deselect_all(self):
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.CheckState.Unchecked)

    def _on_sync(self):
        src_name = self.src_combo.currentText()
        tgt_name = self.tgt_combo.currentText()

        if src_name == tgt_name:
            QMessageBox.warning(self, "Aviso", "A origem e o destino devem ser agentes diferentes.")
            return

        tgt_mgr = self.managers.get(tgt_name)
        if not tgt_mgr:
            return

        selected_mcps = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_mcps.append(item.data(Qt.ItemDataRole.UserRole))

        if not selected_mcps:
            QMessageBox.warning(self, "Aviso", "Selecione ao menos um MCP Server para sincronizar.")
            return

        count = 0
        for mcp in selected_mcps:
            success = tgt_mgr.save_mcp(mcp)
            if success:
                count += 1

        QMessageBox.information(
            self,
            "Sincronização Concluída",
            f"✅ {count} de {len(selected_mcps)} MCPs foram sincronizados com sucesso de {src_name} para {tgt_name}!"
        )
        self.accept()
