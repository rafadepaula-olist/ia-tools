import os
from typing import Dict, List, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QPushButton, QMessageBox, QGroupBox, QFrame
)
from PyQt6.QtCore import Qt
import qtawesome as qta

from models.mcp import McpServer
from config_managers.base import BaseConfigManager

class CopyMcpDialog(QDialog):
    def __init__(self, mcp: McpServer, source_agent: str, managers: Dict[str, BaseConfigManager], parent=None):
        super().__init__(parent)
        self.mcp = mcp
        self.source_agent = source_agent
        self.managers = managers
        self.target_agent_name = ""

        self.setWindowTitle(f"Copiar MCP Server: {mcp.name}")
        self.resize(520, 480)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(18, 18, 18, 18)

        # MCP Source Info Card
        info_card = QFrame()
        info_card.setStyleSheet("""
            QFrame {
                background-color: #161924;
                border: 1px solid #232736;
                border-radius: 8px;
                padding: 10px 14px;
            }
        """)
        i_layout = QVBoxLayout(info_card)
        i_layout.setSpacing(6)

        header_row = QHBoxLayout()
        header_lbl = QLabel(f"<b>MCP:</b> <span style='color:#38bdf8; font-size:13px;'>{self.mcp.name}</span>")
        type_lbl = QLabel(f"Tipo: <span style='color:#a78bfa;'>{self.mcp.display_type}</span>")
        header_row.addWidget(header_lbl)
        header_row.addStretch()
        header_row.addWidget(type_lbl)
        i_layout.addLayout(header_row)

        src_lbl = QLabel(f"<b>Origem:</b> {self.source_agent} (Escopo: {self.mcp.scope.upper()})")
        src_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        i_layout.addWidget(src_lbl)

        cmd_preview = self.mcp.command_display or "(Sem comando)"
        cmd_lbl = QLabel(f"<code>{cmd_preview[:70]}{'...' if len(cmd_preview) > 70 else ''}</code>")
        cmd_lbl.setStyleSheet("color: #64748b; font-size: 10px; font-family: monospace;")
        i_layout.addWidget(cmd_lbl)

        layout.addWidget(info_card)

        # Destination Agent Selector
        dest_group = QGroupBox("Destino (Agente / Provider)")
        d_layout = QVBoxLayout(dest_group)
        d_layout.setSpacing(8)

        self.dest_combo = QComboBox()
        for name in sorted(self.managers.keys()):
            self.dest_combo.addItem(name)

        # Default select a different agent if available
        for idx in range(self.dest_combo.count()):
            if self.dest_combo.itemText(idx) != self.source_agent:
                self.dest_combo.setCurrentIndex(idx)
                break

        self.dest_combo.currentTextChanged.connect(self._on_dest_changed)
        d_layout.addWidget(self.dest_combo)
        layout.addWidget(dest_group)

        # Options: Name and Target Scope
        opts_group = QGroupBox("Opções de Cópia")
        o_layout = QVBoxLayout(opts_group)
        o_layout.setSpacing(10)

        # Target Name
        name_row = QHBoxLayout()
        name_lbl = QLabel("Nome no Destino:")
        name_lbl.setStyleSheet("font-weight: 600;")
        self.name_input = QLineEdit(self.mcp.name)
        name_row.addWidget(name_lbl)
        name_row.addWidget(self.name_input, 1)
        o_layout.addLayout(name_row)

        # Target Scope
        scope_row = QHBoxLayout()
        scope_lbl = QLabel("Escopo no Destino:")
        scope_lbl.setStyleSheet("font-weight: 600;")
        self.scope_combo = QComboBox()
        self.scope_combo.addItem("🌐 Global (Todos os Projetos)", "global")
        self.scope_combo.addItem("📁 Projeto Específico", "project")
        self.scope_combo.currentIndexChanged.connect(self._on_scope_changed)
        scope_row.addWidget(scope_lbl)
        scope_row.addWidget(self.scope_combo, 1)
        o_layout.addLayout(scope_row)

        # Project Path selector (if project scope selected)
        self.proj_path_row = QHBoxLayout()
        proj_path_lbl = QLabel("Pasta do Projeto:")
        self.proj_path_combo = QComboBox()
        home = os.path.expanduser("~")
        for p in BaseConfigManager.get_known_projects():
            short_p = p.replace(home, "~")
            self.proj_path_combo.addItem(f"{os.path.basename(p)} ({short_p})", p)

        self.proj_path_row.addWidget(proj_path_lbl)
        self.proj_path_row.addWidget(self.proj_path_combo, 1)
        o_layout.addLayout(self.proj_path_row)

        layout.addWidget(opts_group)
        self._on_scope_changed(self.scope_combo.currentIndex())

        # Action Buttons
        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.clicked.connect(self.reject)

        self.copy_btn = QPushButton("Copiar MCP")
        self.copy_btn.setObjectName("primaryBtn")
        self.copy_btn.setIcon(qta.icon('fa5s.clone', color='white'))
        self.copy_btn.clicked.connect(self._on_copy)

        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(self.copy_btn)
        layout.addLayout(btn_row)

    def _on_dest_changed(self, new_dest: str):
        pass

    def _on_scope_changed(self, index: int):
        is_project = self.scope_combo.currentData() == "project"
        for i in range(self.proj_path_row.count()):
            w = self.proj_path_row.itemAt(i).widget()
            if w:
                w.setVisible(is_project)

    def _on_copy(self):
        dest_name = self.dest_combo.currentText()
        dest_mgr = self.managers.get(dest_name)
        if not dest_mgr:
            QMessageBox.critical(self, "Erro", f"Provedor de destino '{dest_name}' não encontrado.")
            return

        target_name = self.name_input.text().strip()
        if not target_name:
            QMessageBox.warning(self, "Aviso", "O nome do MCP Server no destino é obrigatório.")
            self.name_input.setFocus()
            return

        target_scope = self.scope_combo.currentData()
        target_project_path = self.proj_path_combo.currentData() if target_scope == "project" else None

        # Build cloned McpServer object
        cloned_mcp = McpServer(
            name=target_name,
            server_type=self.mcp.server_type,
            command=self.mcp.command,
            args=list(self.mcp.args) if self.mcp.args else [],
            env=dict(self.mcp.env) if self.mcp.env else {},
            url=self.mcp.url,
            headers=dict(self.mcp.headers) if self.mcp.headers else {},
            enabled=self.mcp.enabled,
            scope=target_scope,
            project_path=target_project_path,
            raw_data=dict(self.mcp.raw_data) if self.mcp.raw_data else {}
        )

        success = dest_mgr.save_mcp(cloned_mcp)
        if success:
            self.target_agent_name = dest_name
            QMessageBox.information(
                self,
                "Cópia Concluída",
                f"✅ MCP Server '{target_name}' foi copiado com sucesso para o agente <b>{dest_name}</b>!"
            )
            self.accept()
        else:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar MCP Server no agente '{dest_name}'.")
