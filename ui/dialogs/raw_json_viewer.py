from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QMessageBox
)
import json
import json5
import qtawesome as qta

class RawJsonViewerDialog(QDialog):
    def __init__(self, title: str, file_path: str, initial_content: dict, save_callback, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.save_callback = save_callback

        self.setWindowTitle(f"Editor de Arquivo de Configuração: {title}")
        self.resize(750, 600)
        self._setup_ui(initial_content)

    def _setup_ui(self, initial_content: dict):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(18, 18, 18, 18)

        # Header with Path
        top_row = QHBoxLayout()
        path_lbl = QLabel(f"Arquivo: <b style='color:#38bdf8;'>{self.file_path}</b>")
        path_lbl.setStyleSheet("font-size: 12px;")
        top_row.addWidget(path_lbl)
        top_row.addStretch()

        format_btn = QPushButton("Formatar / Indentar JSON")
        format_btn.setObjectName("secondaryBtn")
        format_btn.setIcon(qta.icon('fa5s.magic', color='#818cf8'))
        format_btn.clicked.connect(self._format_json)
        top_row.addWidget(format_btn)

        layout.addLayout(top_row)

        # Editor
        self.editor = QTextEdit()
        self.editor.setFontFamily("monospace")
        self.editor.setPlainText(json.dumps(initial_content, indent=2, ensure_ascii=False))
        layout.addWidget(self.editor, 1)

        # Status / Actions
        bottom_row = QHBoxLayout()
        info_lbl = QLabel("⚡ Um backup automático (.bak) será gerado antes de salvar.")
        info_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        bottom_row.addWidget(info_lbl)
        bottom_row.addStretch()

        cancel_btn = QPushButton("Fechar")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.clicked.connect(self.reject)
        bottom_row.addWidget(cancel_btn)

        save_btn = QPushButton("Salvar Alterações")
        save_btn.setObjectName("primaryBtn")
        save_btn.setIcon(qta.icon('fa5s.save', color='white'))
        save_btn.clicked.connect(self._on_save)
        bottom_row.addWidget(save_btn)

        layout.addLayout(bottom_row)

    def _format_json(self):
        try:
            txt = self.editor.toPlainText().strip()
            data = json5.loads(txt)
            self.editor.setPlainText(json.dumps(data, indent=2, ensure_ascii=False))
        except Exception as e:
            QMessageBox.warning(self, "Erro de Sintaxe", f"Não foi possível formatar o JSON:\n{e}")

    def _on_save(self):
        txt = self.editor.toPlainText().strip()
        try:
            data = json5.loads(txt)
        except Exception as e:
            QMessageBox.critical(self, "JSON Inválido", f"Erro ao interpretar JSON:\n{e}")
            return

        success = self.save_callback(data)
        if success:
            QMessageBox.information(self, "Sucesso", "Arquivo de configuração salvo com sucesso!")
            self.accept()
        else:
            QMessageBox.critical(self, "Erro", "Falha ao salvar o arquivo.")
