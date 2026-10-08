from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QPlainTextEdit,
    QPushButton, QHBoxLayout, QFileDialog
)

from shell_jekyll import gb_var as gb_var_global

class ExpressionEditor(QDialog):
    def __init__(self, controller):
        """``controller``: the ``shell_jekyll.api.ShellJekyll`` that stores the script in the project."""
        super().__init__()
        self.sj = controller
        self.resize(600,390)

        dialog_lo = QVBoxLayout()
        dialog_lo.setSpacing(10)
        dialog_lo.setContentsMargins(16, 16, 16, 16)

        self.scripting_area = QPlainTextEdit()
        self.scripting_area.setPlaceholderText("Custom Expression")
        self.set_expression()
        dialog_lo.addWidget(self.scripting_area)

        btn_lo = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.save_expression)
        btn_lo.addWidget(save_btn)
        open_tcl_btn = QPushButton("Load TCL")
        open_tcl_btn.clicked.connect(self.load_tcl_script)
        btn_lo.addWidget(open_tcl_btn)
        dialog_lo.addLayout(btn_lo)

        self.setStyleSheet(gb_var_global.style_script.EXP_EDITOR_STYLESHEET)
        self.setLayout(dialog_lo)

    def load_tcl_script(self):
        """Load a .tcl file into the editor (unchanged)."""
        filename, _ = QFileDialog.getOpenFileName(self, "Open TCL Script", "", "TCL Script (*.tcl)")
        if not filename:
            return
        with open(filename, "r", encoding="utf-8") as f:
            expression_content = f.read()
        self.scripting_area.setPlainText(expression_content)

    def save_expression(self):
        """Store the script in the project file (``ShellJekyll.save_expression``); reject if the project has no file yet."""
        if not self.sj.save_expression(self.scripting_area.toPlainText()):
            self.reject()
            return
        self.accept()

    def set_expression(self):
        if self.sj.saving_path is None:
            self.reject()
            return
        current_expression = self.sj.get_expression()
        if current_expression is not None:
            self.scripting_area.setPlainText(current_expression)
