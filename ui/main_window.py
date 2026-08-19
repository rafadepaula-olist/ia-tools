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
from typing import Dict, List, Any

from config_managers import (
    AntigravityConfigManager, ClaudeConfigManager, OpenCodeConfigManager,
    CodexConfigManager, WindsurfConfigManager, CursorConfigManager
)
from ui.agent_tab import AgentTab
from ui.dialogs.sync_dialog import SyncDialog
from ui.dialogs.copy_mcp_dialog import CopyMcpDialog
from ui.styles import DARK_THEME_QSS

PROVIDER_REGISTRY = [
    {
        "name": "Antigravity",
        "manager_cls": AntigravityConfigManager,
        "icon": "fa5s.rocket",
        "color": "#818cf8",
        "label": "🚀 Antigravity CLI (Gemini)",
        "desc": "Google Antigravity / Gemini CLI (~/.gemini)"
    },
    {
        "name": "Claude",
        "manager_cls": ClaudeConfigManager,
        "icon": "fa5s.brain",
        "color": "#c084fc",
        "label": "🟣 Claude Code (Claude)",
        "desc": "Anthropic Claude Code (~/.claude, ~/.claude.json)"
    },
    {
        "name": "OpenCode",
        "manager_cls": OpenCodeConfigManager,
        "icon": "fa5s.bolt",
        "color": "#38bdf8",
        "label": "⚡ OpenCode (Opencode)",
        "desc": "OpenCode Interpreter (~/.config/opencode)"
    },
    {
        "name": "Codex",
        "manager_cls": CodexConfigManager,
        "icon": "fa5s.code",
        "color": "#f59e0b",
        "label": "🟧 Codex (.agents)",
        "desc": "OpenAI Codex / Agents (~/.codex, ~/.agents)"
    },
    {
        "name": "Windsurf",
        "manager_cls": WindsurfConfigManager,
        "icon": "fa5s.wind",
        "color": "#10b981",
        "label": "🌊 Windsurf (Codeium)",
        "desc": "Codeium Windsurf IDE (~/.codeium/windsurf)"
    },
    {
        "name": "Cursor",
        "manager_cls": CursorConfigManager,
        "icon": "fa5s.mouse-pointer",
        "color": "#06b6d4",
        "label": "🖱️ Cursor",
        "desc": "Cursor AI Editor (~/.cursor, ~/.config/Cursor)"
    }
]

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

        # Dictionaries for dynamic managers and agent tabs
        self.managers: Dict[str, Any] = {}
        self.agent_tabs: Dict[str, AgentTab] = {}

        self._setup_ui()
        self.discover_agents()
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
        self.subtitle_lbl = QLabel("Gestão centralizada de MCPs, Plugins & Skills para agentes de IA locais")
        self.subtitle_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(self.subtitle_lbl)
        h_layout.addLayout(title_box)

        h_layout.addStretch()

        # Global Action Buttons
        self.sync_btn = QPushButton("Sincronizar Agentes")
        self.sync_btn.setObjectName("primaryBtn")
        self.sync_btn.setIcon(qta.icon('fa5s.exchange-alt', color='white'))
        self.sync_btn.setToolTip("Copiar / Sincronizar MCP Servers entre os agentes detectados")
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
        self.refresh_all_btn.setToolTip("Redescobrir e recarregar agentes do sistema")
        self.refresh_all_btn.clicked.connect(self.reload_all_agents)
        h_layout.addWidget(self.refresh_all_btn)

        main_layout.addWidget(header)

        # Main Dynamic Tabs Container
        self.main_tabs = QTabWidget()
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

    def discover_agents(self, force_all: bool = False):
        """Dynamically checks which AI agent tools exist and mounts their tabs."""
        # Preserve active tab name if possible
        prev_agent_name = None
        curr_widget = self.main_tabs.currentWidget()
        if isinstance(curr_widget, AgentTab):
            prev_agent_name = curr_widget.agent_name

        self.main_tabs.clear()
        self.managers.clear()
        self.agent_tabs.clear()

        discovered: List[str] = []
        for prov in PROVIDER_REGISTRY:
            mgr = prov["manager_cls"]()
            if force_all or mgr.is_installed():
                name = prov["name"]
                self.managers[name] = mgr
                tab = AgentTab(
                    agent_name=name,
                    config_manager=mgr,
                    sync_callback=self._sync_single_mcp,
                    parent=self
                )
                tab.statusChanged.connect(self._set_status)
                self.agent_tabs[name] = tab
                self.main_tabs.addTab(tab, qta.icon(prov["icon"], color=prov["color"]), prov["label"])
                discovered.append(name)

        if not self.agent_tabs:
            # Empty state when no supported agent tools are detected
            empty_widget = self._create_empty_state_widget()
            self.main_tabs.addTab(empty_widget, qta.icon('fa5s.exclamation-triangle', color='#f59e0b'), "⚠️ Nenhum Agente Detectado")
            self.sync_btn.setEnabled(False)
            self._set_status("Nenhum agente IA compatível foi detectado no sistema.")
        else:
            self.sync_btn.setEnabled(len(self.managers) >= 2)
            if prev_agent_name and prev_agent_name in self.agent_tabs:
                idx = list(self.agent_tabs.keys()).index(prev_agent_name)
                self.main_tabs.setCurrentIndex(idx)
            self._set_status(f"Agentes detectados: {', '.join(discovered)}")

        self._update_global_summary()

    def _create_empty_state_widget(self) -> QWidget:
        widget = QWidget()
        vbox = QVBoxLayout(widget)
        vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.setSpacing(16)
        vbox.setContentsMargins(32, 32, 32, 32)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon('fa5s.search', color='#64748b').pixmap(64, 64))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(icon_lbl)

        title_lbl = QLabel("Nenhum Agente de IA Detectado")
        title_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #f8fafc;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(title_lbl)

        desc_lbl = QLabel(
            "Não localizamos configurações ou executáveis no seu sistema para:<br><br>"
            "• 🚀 <b>Antigravity / Gemini CLI</b>: <code>~/.gemini</code>, <code>~/.antigravity</code> ou comando <code>gemini</code>/<code>agy</code><br>"
            "• 🟣 <b>Claude Code</b>: <code>~/.claude.json</code>, <code>~/.claude/</code> ou comando <code>claude</code><br>"
            "• ⚡ <b>OpenCode</b>: <code>~/.config/opencode/</code>, <code>~/.opencode/</code> ou comando <code>opencode</code><br>"
            "• 🟧 <b>Codex</b>: <code>~/.codex/</code>, <code>~/.agents/</code> ou comando <code>codex</code><br>"
            "• 🌊 <b>Windsurf</b>: <code>~/.codeium/windsurf/</code>, <code>~/.windsurf/</code> ou comando <code>windsurf</code><br>"
            "• 🖱️ <b>Cursor</b>: <code>~/.cursor/</code>, <code>~/.config/Cursor/</code> ou comando <code>cursor</code><br><br>"
            "Instale ou utilize qualquer um dos agentes acima e clique em <b>Buscar Novamente</b>."
        )
        desc_lbl.setStyleSheet("color: #94a3b8; font-size: 13px; line-height: 1.6;")
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(desc_lbl)

        btn_box = QHBoxLayout()
        btn_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_box.setSpacing(14)

        rescan_btn = QPushButton("🔍 Buscar Novamente")
        rescan_btn.setObjectName("primaryBtn")
        rescan_btn.clicked.connect(lambda: self.discover_agents(force_all=False))
        btn_box.addWidget(rescan_btn)

        force_btn = QPushButton("Mostrar Todas as Abas")
        force_btn.setObjectName("secondaryBtn")
        force_btn.clicked.connect(lambda: self.discover_agents(force_all=True))
        btn_box.addWidget(force_btn)

        vbox.addLayout(btn_box)
        return widget

    def _apply_styles(self):
        self.setStyleSheet(DARK_THEME_QSS)

    def _set_status(self, msg: str):
        self.status_msg_lbl.setText(msg)
        self._update_global_summary()

    def _update_global_summary(self):
        total_mcps = sum(len(m.list_mcps()) for m in self.managers.values())
        total_plugins = sum(len(m.list_plugins_and_skills()) for m in self.managers.values())
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        agents_count = len(self.managers)
        self.stats_summary_lbl.setText(f"📊 {agents_count} Agente(s) Ativo(s)  |  {total_mcps} MCPs  |  {total_plugins} Plugins & Skills  •  {now_str}")

    def reload_all_agents(self):
        self.discover_agents()
        for tab in self.agent_tabs.values():
            tab.reload_all()
        self._set_status("Todos os agentes foram atualizados e recarregados do disco.")

    def _open_sync_dialog(self):
        if len(self.managers) < 2:
            QMessageBox.information(
                self,
                "Sincronização Indisponível",
                f"A sincronização entre agentes requer ao menos 2 agentes detectados no sistema.\n\nAgentes detectados atualmente: {len(self.managers)} ({', '.join(self.managers.keys()) if self.managers else 'nenhum'})."
            )
            return

        curr_widget = self.main_tabs.currentWidget()
        init_src = getattr(curr_widget, 'agent_name', None) or list(self.managers.keys())[0]

        dialog = SyncDialog(managers=self.managers, initial_source=init_src, parent=self)
        if dialog.exec():
            self.reload_all_agents()

    def _get_all_available_managers(self) -> Dict[str, Any]:
        all_mgrs = dict(self.managers)
        for prov in PROVIDER_REGISTRY:
            if prov["name"] not in all_mgrs:
                all_mgrs[prov["name"]] = prov["manager_cls"]()
        return all_mgrs

    def _sync_single_mcp(self, source_agent: str, mcp):
        all_mgrs = self._get_all_available_managers()
        dialog = CopyMcpDialog(mcp=mcp, source_agent=source_agent, managers=all_mgrs, parent=self)
        if dialog.exec():
            target_agent = dialog.target_agent_name
            self.reload_all_agents()
            self._set_status(f"MCP '{mcp.name}' copiado com sucesso de {source_agent} para {target_agent}.")

    def _backup_all(self):
        backed_up = []
        for name, mgr in self.managers.items():
            path = mgr.get_raw_config_path()
            if path and os.path.exists(path):
                bkp = mgr.backup_file(path)
                if bkp:
                    backed_up.append(os.path.basename(bkp))
        
        if backed_up:
            QMessageBox.information(
                self,
                "Backup Concluído",
                f"✅ {len(backed_up)} arquivos de configuração foram salvos com sucesso em:\n~/.ia-tools-backups/\n\nArquivos gerados:\n" + "\n".join(backed_up)
            )
            self._set_status(f"Backup manual de {len(backed_up)} arquivos concluído.")
        else:
            QMessageBox.information(
                self,
                "Backup",
                "Nenhum arquivo de configuração para fazer backup no momento."
            )

    def _open_backup_folder(self):
        bkp_dir = os.path.expanduser("~/.ia-tools-backups")
        os.makedirs(bkp_dir, exist_ok=True)
        try:
            subprocess.Popen(["xdg-open", bkp_dir])
        except Exception as e:
            QMessageBox.warning(self, "Aviso", f"Não foi possível abrir o gerenciador de arquivos: {e}")

