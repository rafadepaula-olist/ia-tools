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
        self.current_project_path = "GLOBAL"
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(4)

        # Sub Tabs
        self.sub_tabs = QTabWidget()
        self.sub_tabs.setObjectName("subTabWidget")

        # Corner Stats in SubTabs
        stats_widget = QWidget()
        stats_layout = QHBoxLayout(stats_widget)
        stats_layout.setContentsMargins(0, 0, 6, 0)
        stats_layout.setSpacing(10)

        self.mcp_stat_lbl = QLabel("🔌 0 MCPs")
        self.mcp_stat_lbl.setStyleSheet("color: #38bdf8; font-size: 11px; font-weight: 600;")
        
        self.plugin_stat_lbl = QLabel("🧩 0 Plugins/Skills")
        self.plugin_stat_lbl.setStyleSheet("color: #34d399; font-size: 11px; font-weight: 600;")

        stats_layout.addWidget(self.mcp_stat_lbl)
        stats_layout.addWidget(self.plugin_stat_lbl)
        self.sub_tabs.setCornerWidget(stats_widget, Qt.Corner.TopRightCorner)

        # MCP Panel
        self.mcp_panel = McpPanel(
            agent_name=self.agent_name,
            config_manager=self.config_manager,
            sync_callback=self.sync_callback,
            parent=self
        )
        self.mcp_panel.statusChanged.connect(self._handle_status)
        self.sub_tabs.addTab(self.mcp_panel, qta.icon('fa5s.plug', color='#38bdf8'), "MCP Servers")

        # Plugin Panel
        self.plugin_panel = PluginPanel(
            agent_name=self.agent_name,
            config_manager=self.config_manager,
            parent=self
        )
        self.plugin_panel.statusChanged.connect(self._handle_status)
        self.sub_tabs.addTab(self.plugin_panel, qta.icon('fa5s.puzzle-piece', color='#a78bfa'), "Plugins & Skills")

        layout.addWidget(self.sub_tabs, 1)
        self.update_stats()

    def on_scope_changed_from_panel(self, project_path: str, source: str = "mcp"):
        self.current_project_path = project_path
        if source == "mcp" and hasattr(self, 'plugin_panel'):
            self.plugin_panel.set_project_filter(project_path)
        elif source == "plugin" and hasattr(self, 'mcp_panel'):
            self.mcp_panel.set_project_filter(project_path)
        self.update_stats()

    def update_stats(self):
        proj_data = getattr(self, 'current_project_path', "__ALL__")
        
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
        self.mcp_panel.reload_data(self.current_project_path)
        self.plugin_panel.reload_data(self.current_project_path)
        self.update_stats()
