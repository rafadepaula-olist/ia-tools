from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTabWidget, QPushButton, QStatusBar, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
import qtawesome as qta
import os
import subprocess
import datetime

from config_managers import AntigravityConfigManager, ClaudeConfigManager, OpenCodeConfigManager
from ui.agent_tab import AgentTab
from ui.dialogs.sync_dialog import SyncDialog
from ui.styles import DARK_THEME_QSS

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IA Tools Manager - Gestor de Ferramentas, MCPs & Plugins")
        self.resize(1100, 780)
        self.setMinimumSize(850, 600)

        # Set Window Icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "ia-tools.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            self.setWindowIcon(qta.icon('fa5s.robot', color='#818cf8'))

        # Initialize Config Managers
        self.managers = {
            "Antigravity": AntigravityConfigManager(),
            "Claude": ClaudeConfigManager(),
            "OpenCode": OpenCodeConfigManager()
        }

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 14, 16, 12)
        main_layout.setSpacing(12)

        # Top Header Bar
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #161a29, stop:1 #1e1b38);
                border: 1px solid #282e44;
                border-radius: 10px;
                padding: 10px 16px;
            }
        """)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(10, 6, 10, 6)
        h_layout.setSpacing(16)

        # App Icon & Title
        logo_lbl = QLabel()
        logo_lbl.setPixmap(qta.icon('fa5s.robot', color='#818cf8').pixmap(32, 32))
        h_layout.addWidget(logo_lbl)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_lbl = QLabel("⚡ IA Tools Manager")
        title_lbl.setObjectName("headerTitle")
        subtitle_lbl = QLabel("Gestão centralizada de MCPs, Plugins & Skills para Antigravity, Claude e OpenCode")
        subtitle_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(subtitle_lbl)
        h_layout.addLayout(title_box)

        h_layout.addStretch()

        # Global Action Buttons
        self.sync_btn = QPushButton("Sincronizar Agentes")
        self.sync_btn.setObjectName("primaryBtn")
        self.sync_btn.setIcon(qta.icon('fa5s.exchange-alt', color='white'))
        self.sync_btn.setToolTip("Copiar / Sincronizar MCP Servers entre os agentes")
        self.sync_btn.clicked.connect(self._open_sync_dialog)
        h_layout.addWidget(self.sync_btn)

        self.backup_btn = QPushButton("Backup Geral")
        self.backup_btn.setObjectName("secondaryBtn")
        self.backup_btn.setIcon(qta.icon('fa5s.shield-alt', color='#10b981'))
        self.backup_btn.setToolTip("Gerar backup de todos os arquivos de configuração agora")
        self.backup_btn.clicked.connect(self._backup_all)
        h_layout.addWidget(self.backup_btn)

        self.open_bkp_btn = QPushButton("Pasta Backups")
        self.open_bkp_btn.setObjectName("secondaryBtn")
        self.open_bkp_btn.setIcon(qta.icon('fa5s.folder', color='#fbbf24'))
        self.open_bkp_btn.setToolTip("Abrir pasta de backups no gerenciador de arquivos")
        self.open_bkp_btn.clicked.connect(self._open_backup_folder)
        h_layout.addWidget(self.open_bkp_btn)

        self.refresh_all_btn = QPushButton()
        self.refresh_all_btn.setObjectName("secondaryBtn")
        self.refresh_all_btn.setIcon(qta.icon('fa5s.redo', color='#cbd5e1'))
        self.refresh_all_btn.setToolTip("Recarregar todos os agentes do disco")
        self.refresh_all_btn.clicked.connect(self.reload_all_agents)
        h_layout.addWidget(self.refresh_all_btn)

        main_layout.addWidget(header)

        # 3 Main Tabs: Antigravity, Claude, OpenCode
        self.main_tabs = QTabWidget()
        
        # 1. Antigravity Tab
        self.antigravity_tab = AgentTab(
            agent_name="Antigravity",
            config_manager=self.managers["Antigravity"],
            sync_callback=self._sync_single_mcp,
            parent=self
        )
        self.antigravity_tab.statusChanged.connect(self._set_status)
        self.main_tabs.addTab(self.antigravity_tab, qta.icon('fa5s.rocket', color='#818cf8'), "🚀 Antigravity CLI (Gemini)")

        # 2. Claude Tab
        self.claude_tab = AgentTab(
            agent_name="Claude",
            config_manager=self.managers["Claude"],
            sync_callback=self._sync_single_mcp,
            parent=self
        )
        self.claude_tab.statusChanged.connect(self._set_status)
        self.main_tabs.addTab(self.claude_tab, qta.icon('fa5s.brain', color='#c084fc'), "🟣 Claude Code (Claude)")

        # 3. OpenCode Tab
        self.opencode_tab = AgentTab(
            agent_name="OpenCode",
            config_manager=self.managers["OpenCode"],
            sync_callback=self._sync_single_mcp,
            parent=self
        )
        self.opencode_tab.statusChanged.connect(self._set_status)
        self.main_tabs.addTab(self.opencode_tab, qta.icon('fa5s.bolt', color='#38bdf8'), "⚡ OpenCode (Opencode)")

        main_layout.addWidget(self.main_tabs, 1)

        # Bottom Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.status_msg_lbl = QLabel("Sistema pronto.")
        self.status_msg_lbl.setStyleSheet("color: #cbd5e1;")
        self.status_bar.addWidget(self.status_msg_lbl, 1)

        self.stats_summary_lbl = QLabel()
        self.stats_summary_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.status_bar.addPermanentWidget(self.stats_summary_lbl)

        self._update_global_summary()

    def _apply_styles(self):
        self.setStyleSheet(DARK_THEME_QSS)

    def _set_status(self, msg: str):
        self.status_msg_lbl.setText(msg)
        self._update_global_summary()

    def _update_global_summary(self):
        total_mcps = sum(len(m.list_mcps()) for m in self.managers.values())
        total_plugins = sum(len(m.list_plugins_and_skills()) for m in self.managers.values())
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        self.stats_summary_lbl.setText(f"📊 Total no PC: {total_mcps} MCPs | {total_plugins} Plugins & Skills  •  Última checagem: {now_str}")

    def reload_all_agents(self):
        self.antigravity_tab.reload_all()
        self.claude_tab.reload_all()
        self.opencode_tab.reload_all()
        self._set_status("Todos os agentes e configurações foram recarregados com sucesso.")

    def _open_sync_dialog(self):
        curr_tab_text = self.main_tabs.tabText(self.main_tabs.currentIndex())
        init_src = "Antigravity"
        if "Claude" in curr_tab_text:
            init_src = "Claude"
        elif "OpenCode" in curr_tab_text:
            init_src = "OpenCode"

        dialog = SyncDialog(managers=self.managers, initial_source=init_src, parent=self)
        if dialog.exec():
            self.reload_all_agents()

    def _sync_single_mcp(self, source_agent: str, mcp):
        # Open sync dialog preset to source
        dialog = SyncDialog(managers=self.managers, initial_source=source_agent, parent=self)
        if dialog.exec():
            self.reload_all_agents()

    def _backup_all(self):
        backed_up = []
        for name, mgr in self.managers.items():
            path = mgr.get_raw_config_path()
            if path and os.path.exists(path):
                bkp = mgr.backup_file(path)
                if bkp:
                    backed_up.append(os.path.basename(bkp))
        
        QMessageBox.information(
            self,
            "Backup Concluído",
            f"✅ {len(backed_up)} arquivos de configuração foram salvos com sucesso em:\n~/.ia-tools-backups/\n\nArquivos gerados:\n" + "\n".join(backed_up)
        )
        self._set_status(f"Backup manual de {len(backed_up)} arquivos concluído.")

    def _open_backup_folder(self):
        bkp_dir = os.path.expanduser("~/.ia-tools-backups")
        os.makedirs(bkp_dir, exist_ok=True)
        try:
            subprocess.Popen(["xdg-open", bkp_dir])
        except Exception as e:
            QMessageBox.warning(self, "Aviso", f"Não foi possível abrir o gerenciador de arquivos: {e}")
