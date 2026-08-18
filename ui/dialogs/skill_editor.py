from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QMessageBox, QGroupBox
)
import qtawesome as qta

class SkillEditorDialog(QDialog):
    def __init__(self, agent_name: str = "Antigravity", skill_name: str = "", skill_desc: str = "", instructions: str = "", parent=None):
        super().__init__(parent)
        self.agent_name = agent_name
        self.is_edit = bool(skill_name)
        
        self.setWindowTitle(f"{'Editar' if self.is_edit else 'Criar Nova'} Skill ({agent_name})")
        self.resize(650, 580)
        self._setup_ui(skill_name, skill_desc, instructions)

    def _setup_ui(self, name: str, desc: str, inst: str):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(18, 18, 18, 18)

        meta_group = QGroupBox("Metadados da Skill (Frontmatter)")
        m_layout = QVBoxLayout(meta_group)
        m_layout.setSpacing(8)

        name_lbl = QLabel("Nome da Skill (kebab-case):")
        self.name_input = QLineEdit(name)
        self.name_input.setPlaceholderText("ex: run-custom-tests, format-sql-queries")
        if self.is_edit:
            self.name_input.setReadOnly(True)
        m_layout.addWidget(name_lbl)
        m_layout.addWidget(self.name_input)

        desc_lbl = QLabel("Descrição / Quando o agente deve usar:")
        self.desc_input = QLineEdit(desc)
        self.desc_input.setPlaceholderText("ex: Use when the user asks to format SQL queries or validate database schema")
        m_layout.addWidget(desc_lbl)
        m_layout.addWidget(self.desc_input)

        layout.addWidget(meta_group)

        inst_group = QGroupBox("Instruções e Regras (Markdown - SKILL.md)")
        i_layout = QVBoxLayout(inst_group)
        self.inst_edit = QTextEdit()
        self.inst_edit.setFontFamily("monospace")
        
        default_template = """## Overview
Descreva aqui o objetivo principal desta skill.

## Guidelines
- Passo 1: ...
- Passo 2: ...

## Exemplos de Uso
```bash
# comando ou exemplo
```
"""
        self.inst_edit.setPlainText(inst if inst else default_template)
        i_layout.addWidget(self.inst_edit)

        layout.addWidget(inst_group, 1)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setObjectName("secondaryBtn")
        self.cancel_btn.clicked.connect(self.reject)

        self.save_btn = QPushButton("Salvar Skill")
        self.save_btn.setObjectName("primaryBtn")
        self.save_btn.setIcon(qta.icon('fa5s.save', color='white'))
        self.save_btn.clicked.connect(self._on_save)

        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def _on_save(self):
        name = self.name_input.text().strip()
        desc = self.desc_input.text().strip()
        inst = self.inst_edit.toPlainText().strip()

        if not name:
            QMessageBox.warning(self, "Aviso", "O nome da Skill é obrigatório.")
            return
        if not desc:
            QMessageBox.warning(self, "Aviso", "A descrição da Skill é obrigatória para o agente saber quando ativá-la.")
            return

        self.skill_data = {
            "name": name,
            "description": desc,
            "instructions": inst
        }
        self.accept()
