from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QFrame
from PyQt6.QtCore import pyqtSignal, Qt
import qtawesome as qta

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
            "OpenCode": ('fa5s.bolt', '#38bdf8')
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
        
        title_box.addWidget(title_lbl)
        title_box.addWidget(self.path_lbl)
        b_layout.addLayout(title_box)

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

    def update_stats(self):
        mcps = self.config_manager.list_mcps()
        m_active = sum(1 for m in mcps if m.enabled)
        self.mcp_stat_lbl.setText(f"🔌 {m_active}/{len(mcps)} MCPs Ativos")

        plugs = self.config_manager.list_plugins_and_skills()
        p_active = sum(1 for p in plugs if p.enabled)
        self.plugin_stat_lbl.setText(f"🧩 {p_active}/{len(plugs)} Plugins/Skills Ativos")

    def _handle_status(self, msg: str):
        self.update_stats()
        self.statusChanged.emit(msg)

    def reload_all(self):
        self.mcp_panel.reload_data()
        self.plugin_panel.reload_data()
        self.update_stats()
