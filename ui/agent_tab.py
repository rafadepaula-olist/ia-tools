import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QFrame,
    QComboBox, QPushButton, QFileDialog
)
from PyQt6.QtCore import pyqtSignal, Qt
import qtawesome as qta

from config_managers.base import BaseConfigManager
from ui.mcp_panel import McpPanel
from ui.plugin_panel import PluginPanel
from ui.components.badge import Badge

class AgentTab(QWidget):
    statusChanged = pyqtSignal(str)

    def __init__(self, agent_name: str, config_manager, sync_callback=None, parent=None):
        super().__init__(parent)
        self.agent_name = agent_name
        self.config_manager = config_manager
        self.sync_callback = sync_callback
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # Header Info Banner
        self.banner = QFrame()
        self.banner.setStyleSheet("""
            QFrame {
                background-color: #161924;
                border: 1px solid #232736;
                border-radius: 8px;
                padding: 10px 14px;
            }
        """)
        b_layout = QHBoxLayout(self.banner)
        b_layout.setContentsMargins(10, 8, 10, 8)
        b_layout.setSpacing(14)

        # Agent Icon + Name
        icon_map = {
            "Antigravity": ('fa5s.rocket', '#6366f1'),
            "Claude": ('fa5s.brain', '#c084fc'),
            "OpenCode": ('fa5s.bolt', '#38bdf8'),
            "Codex": ('fa5s.code', '#f59e0b'),
            "Windsurf": ('fa5s.wind', '#10b981'),
            "Cursor": ('fa5s.mouse-pointer', '#06b6d4')
        }
        icon_name, icon_color = icon_map.get(self.agent_name, ('fa5s.robot', '#38bdf8'))
        
        agent_icon = QLabel()
        agent_icon.setPixmap(qta.icon(icon_name, color=icon_color).pixmap(24, 24))
        b_layout.addWidget(agent_icon)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        
        title_lbl = QLabel(f"Agente: <b>{self.agent_name}</b>")
        title_lbl.setStyleSheet("font-size: 14px; color: #f8fafc;")
        
        cfg_path = getattr(self.config_manager, 'get_raw_config_path', lambda: '')()
        self.path_lbl = QLabel(f"Config: <span style='color:#94a3b8;'>{cfg_path}</span>")
        self.path_lbl.setStyleSheet("font-size: 11px;")
        
        b_layout.addLayout(title_box)

        # Workspace / Project Selector
        b_layout.addSpacing(10)
        proj_box = QHBoxLayout()
        proj_box.setSpacing(6)

        proj_icon = QLabel()
        proj_icon.setPixmap(qta.icon('fa5s.folder-open', color='#fbbf24').pixmap(16, 16))
        proj_box.addWidget(proj_icon)

        proj_lbl = QLabel("Projeto / Escopo:")
        proj_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #94a3b8;")
        proj_box.addWidget(proj_lbl)

        self.proj_combo = QComboBox()
        self.proj_combo.setStyleSheet("""
            QComboBox {
                background-color: #0f1118;
                border: 1px solid #2e384d;
                border-radius: 6px;
                padding: 4px 10px;
                color: #f1f5f9;
                font-weight: 600;
                min-width: 260px;
                font-size: 11px;
            }
            QComboBox:hover {
                border-color: #38bdf8;
            }
        """)
        self._populate_projects()
        self.proj_combo.currentIndexChanged.connect(self._on_project_changed)
        proj_box.addWidget(self.proj_combo)

        browse_btn = QPushButton()
        browse_btn.setIcon(qta.icon('fa5s.plus', color='#38bdf8'))
        browse_btn.setToolTip("Abrir pasta de outro projeto...")
        browse_btn.setFixedSize(28, 26)
        browse_btn.setObjectName("secondaryBtn")
        browse_btn.clicked.connect(self._browse_custom_project)
        proj_box.addWidget(browse_btn)

        b_layout.addLayout(proj_box)
        b_layout.addStretch()

        # Stats Badges
        self.mcp_stat_lbl = QLabel("🔌 0 MCPs")
        self.mcp_stat_lbl.setStyleSheet("background: #1e2433; border: 1px solid #333a4d; border-radius: 4px; padding: 4px 8px; font-size: 11px; font-weight: 600; color: #38bdf8;")
        
        self.plugin_stat_lbl = QLabel("🧩 0 Plugins/Skills")
        self.plugin_stat_lbl.setStyleSheet("background: #1e2433; border: 1px solid #333a4d; border-radius: 4px; padding: 4px 8px; font-size: 11px; font-weight: 600; color: #a78bfa;")

        b_layout.addWidget(self.mcp_stat_lbl)
        b_layout.addWidget(self.plugin_stat_lbl)

        layout.addWidget(self.banner)

        # Sub Tabs
        self.sub_tabs = QTabWidget()
        self.sub_tabs.setObjectName("subTabWidget")

        # MCP Panel
        self.mcp_panel = McpPanel(
            agent_name=self.agent_name,
            config_manager=self.config_manager,
            sync_callback=self.sync_callback,
            parent=self
        )
        self.mcp_panel.statusChanged.connect(self._handle_status)
        self.sub_tabs.addTab(self.mcp_panel, qta.icon('fa5s.plug', color='#38bdf8'), "🔌 MCP Servers")

        # Plugin Panel
        self.plugin_panel = PluginPanel(
            agent_name=self.agent_name,
            config_manager=self.config_manager,
            parent=self
        )
        self.plugin_panel.statusChanged.connect(self._handle_status)
        self.sub_tabs.addTab(self.plugin_panel, qta.icon('fa5s.puzzle-piece', color='#a78bfa'), "🧩 Plugins & Skills")

        layout.addWidget(self.sub_tabs, 1)

        self.update_stats()

    def _populate_projects(self):
        self.proj_combo.blockSignals(True)
        self.proj_combo.clear()
        self.proj_combo.addItem("🌐 Todos os Escopos (Global + Projetos)", "__ALL__")
        self.proj_combo.addItem("🏠 Apenas Global / Home (~)", "GLOBAL")

        home = os.path.expanduser("~")
        for p_path in BaseConfigManager.get_known_projects():
            base_n = os.path.basename(p_path)
            short_p = p_path.replace(home, "~")
            self.proj_combo.addItem(f"📁 {base_n} ({short_p})", p_path)

        self.proj_combo.blockSignals(False)

    def _on_project_changed(self, index: int):
        proj_data = self.proj_combo.currentData()
        self.mcp_panel.set_project_filter(proj_data)
        self.plugin_panel.set_project_filter(proj_data)
        self.update_stats()

    def _browse_custom_project(self):
        folder = QFileDialog.getExistingDirectory(self, "Selecionar Diretório do Projeto", os.path.expanduser("~"))
        if folder:
            # Check if already exists in combo
            idx = self.proj_combo.findData(folder)
            if idx >= 0:
                self.proj_combo.setCurrentIndex(idx)
            else:
                base_n = os.path.basename(folder)
                home = os.path.expanduser("~")
                short_p = folder.replace(home, "~")
                self.proj_combo.addItem(f"📁 {base_n} ({short_p})", folder)
                self.proj_combo.setCurrentIndex(self.proj_combo.count() - 1)

    def update_stats(self):
        proj_data = self.proj_combo.currentData() if hasattr(self, 'proj_combo') else "__ALL__"
        
        # MCP count
        mcps = getattr(self.mcp_panel, 'mcps', [])
        if proj_data == "GLOBAL":
            visible_mcps = [m for m in mcps if m.scope != "project"]
        elif proj_data and proj_data != "__ALL__":
            visible_mcps = [m for m in mcps if m.scope != "project" or m.project_path == proj_data]
        else:
            visible_mcps = mcps
        m_active = sum(1 for m in visible_mcps if m.enabled)
        self.mcp_stat_lbl.setText(f"🔌 {m_active}/{len(visible_mcps)} MCPs")

        # Plugin count
        plugs = getattr(self.plugin_panel, 'items', [])
        if proj_data == "GLOBAL":
            visible_plugs = [p for p in plugs if not (p.metadata and p.metadata.get("scope") == "project")]
        elif proj_data and proj_data != "__ALL__":
            visible_plugs = [p for p in plugs if not (p.metadata and p.metadata.get("scope") == "project") or p.metadata.get("project_path") == proj_data]
        else:
            visible_plugs = plugs
        p_active = sum(1 for p in visible_plugs if p.enabled)
        self.plugin_stat_lbl.setText(f"🧩 {p_active}/{len(visible_plugs)} Plugins/Skills")

    def _handle_status(self, msg: str):
        self.update_stats()
        self.statusChanged.emit(msg)

    def reload_all(self):
        proj_data = self.proj_combo.currentData() if hasattr(self, 'proj_combo') else "__ALL__"
        self._populate_projects()
        if proj_data:
            idx = self.proj_combo.findData(proj_data)
            if idx >= 0:
                self.proj_combo.setCurrentIndex(idx)
        self.mcp_panel.reload_data(proj_data)
        self.plugin_panel.reload_data(proj_data)
        self.update_stats()
