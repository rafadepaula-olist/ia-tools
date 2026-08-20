from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QMessageBox, QGroupBox, QFileDialog
)
import qtawesome as qta

import os

POPULAR_PLUGINS = {
    "Custom / Outro": {"name": "", "source_type": "github", "source": ""},
    "Superpowers (Claude & Gemini)": {"name": "superpowers@claude-plugins-official", "source_type": "github", "source": "anthropics/claude-plugins-official"},
    "Caveman (Ultra Token Efficiency)": {"name": "caveman@caveman", "source_type": "github", "source": "JuliusBrussee/caveman"},
    "I Have ADHD (Workflow Helper)": {"name": "i-have-adhd@i-have-adhd", "source_type": "directory", "source": os.path.join(os.path.expanduser("~"), "i-have-adhd")},
    "Anthropic Agent Skills": {"name": "anthropic-agent-skills", "source_type": "github", "source": "anthropics/skills"},
    "Olist ERP Plugins": {"name": "olist-erp-plugins", "source_type": "git", "source": "git@github.com:olist/harness-plugins-erp.git"},
    "Delegate AGY (Subagents)": {"name": "agy-delegate@agy-delegate", "source_type": "git", "source": "https://github.com/davdittrich/delegate-agy.git"},
    "CCC Skills": {"name": "ccc-skills@ccc", "source_type": "github", "source": "ooiyeefei/ccc"},
    "Gopls LSP (Go Language Server)": {"name": "gopls-lsp@claude-plugins-official", "source_type": "github", "source": "claude-plugins-official"}
}

class PluginEditorDialog(QDialog):
    def __init__(self, agent_name: str = "Claude", parent=None):
        super().__init__(parent)
        self.agent_name = agent_name
        self.setWindowTitle(f"Instalar / Habilitar Plugin ({agent_name})")
        self.resize(550, 420)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(18, 18, 18, 18)

        # Preset selector
        preset_box = QHBoxLayout()
        preset_lbl = QLabel("Plugins Populares:")
        preset_lbl.setStyleSheet("font-weight: 600; color: #38bdf8;")
        self.preset_combo = QComboBox()
        for p in POPULAR_PLUGINS.keys():
            self.preset_combo.addItem(p)
        self.preset_combo.currentTextChanged.connect(self._apply_preset)
        preset_box.addWidget(preset_lbl)
        preset_box.addWidget(self.preset_combo, 1)
        layout.addLayout(preset_box)

        # Main Group
        form_group = QGroupBox("Dados do Plugin")
        f_layout = QVBoxLayout(form_group)
        f_layout.setSpacing(10)

        # Plugin Identifier / Name
        p_name_lbl = QLabel("Identificador do Plugin (ID / Nome):")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ex: superpowers@claude-plugins-official ou ./plugins/meu-plugin.js")
        f_layout.addWidget(p_name_lbl)
        f_layout.addWidget(self.name_input)

        # Source Type
        src_type_lbl = QLabel("Tipo de Origem (Source):")
        self.src_type_combo = QComboBox()
        self.src_type_combo.addItems(["github (Repositório GitHub)", "git (URL Git / SSH)", "directory (Pasta Local)", "npm / path (OpenCode / Local)"])
        self.src_type_combo.currentTextChanged.connect(self._on_source_type_changed)
        f_layout.addWidget(src_type_lbl)
        f_layout.addWidget(self.src_type_combo)

        # Source Value / Path
        src_val_lbl = QLabel("Repositório / URL / Caminho:")
        src_row = QHBoxLayout()
        self.src_input = QLineEdit()
        self.src_input.setPlaceholderText("Ex: owner/repo, git@github.com:..., ou /caminho/local")
        
        self.browse_btn = QPushButton("Buscar Pasta...")
        self.browse_btn.setObjectName("secondaryBtn")
        self.browse_btn.clicked.connect(self._browse_directory)

        src_row.addWidget(self.src_input, 1)
        src_row.addWidget(self.browse_btn)
        f_layout.addWidget(src_val_lbl)
        f_layout.addLayout(src_row)

        layout.addWidget(form_group)

        # Marketplace Name (Optional for Claude)
        if "Claude" in self.agent_name:
            mkt_box = QHBoxLayout()
            mkt_lbl = QLabel("Marketplace Alias (Opcional):")
            self.mkt_input = QLineEdit()
            self.mkt_input.setPlaceholderText("Ex: caveman, olist-erp-plugins")
            mkt_box.addWidget(mkt_lbl)
            mkt_box.addWidget(self.mkt_input, 1)
            layout.addLayout(mkt_box)

        layout.addStretch()

        # Action Buttons
        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setObjectName("secondaryBtn")
        self.cancel_btn.clicked.connect(self.reject)

        self.save_btn = QPushButton("Adicionar Plugin")
        self.save_btn.setObjectName("primaryBtn")
        self.save_btn.setIcon(qta.icon('fa5s.plus', color='white'))
        self.save_btn.clicked.connect(self._on_save)

        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def _browse_directory(self):
        d = QFileDialog.getExistingDirectory(self, "Selecione a Pasta do Plugin")
        if d:
            self.src_input.setText(d)
            if not self.name_input.text():
                import os
                self.name_input.setText(os.path.basename(d))

    def _on_source_type_changed(self, text: str):
        is_dir = "directory" in text.lower() or "path" in text.lower()
        self.browse_btn.setVisible(is_dir)

    def _apply_preset(self, preset_name: str):
        if preset_name not in POPULAR_PLUGINS:
            return
        p = POPULAR_PLUGINS[preset_name]
        self.name_input.setText(p.get("name", ""))
        stype = p.get("source_type", "github")
        if stype == "github":
            self.src_type_combo.setCurrentIndex(0)
        elif stype == "git":
            self.src_type_combo.setCurrentIndex(1)
        elif stype == "directory":
            self.src_type_combo.setCurrentIndex(2)
        else:
            self.src_type_combo.setCurrentIndex(3)
        self.src_input.setText(p.get("source", ""))

    def _on_save(self):
        import re
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Aviso", "O nome/identificador do plugin é obrigatório.")
            return

        if not re.match(r'^[a-zA-Z0-9_\-\.@\/:]+$', name):
            QMessageBox.warning(self, "Aviso", "O nome do plugin contém caracteres inválidos. Utilize apenas letras, números, hífen, underline, ponto ou arroba.")
            return

        stype_text = self.src_type_combo.currentText().split()[0]
        self.plugin_data = {
            "name": name,
            "source_type": stype_text,
            "source": self.src_input.text().strip(),
            "marketplace": getattr(self, 'mkt_input', None).text().strip() if hasattr(self, 'mkt_input') else ""
        }
        self.accept()
