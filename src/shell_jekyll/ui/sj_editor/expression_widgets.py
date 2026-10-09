import json
from pathlib import Path

from PySide6.QtCore import QStringListModel
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton,
    QComboBox, QDialog, QLineEdit,
    QLabel, QCompleter
)
from shell_jekyll.ui.sj_editor.expression_editor import ExpressionEditor
from shell_jekyll.ui.sj_editor.ui_utils import flash_button

PRESETS_PATH = Path(__file__).resolve().parents[1] / "_resources" / "expression_presets.json"


class TCLExpressionWidget(QWidget):
    def __init__(self, controller):
        """``controller``: the ``shell_jekyll.api.ShellJekyll`` that runs the expression.

        [Changed] The no-op ``lo.addStretch`` (missing parentheses) was removed, so the layout is unchanged.
        """
        super().__init__()
        self.sj = controller
        lo = QHBoxLayout()
        self.command_func_combo = QComboBox()
        self.command_func_combo.setFixedWidth(300)
        lo.addWidget(self.command_func_combo)
        self.exec_btn = QPushButton("Run Expression")
        self.exec_btn.clicked.connect(self.run_expression)
        lo.addWidget(self.exec_btn)
        self.edit_btn = QPushButton("Edit Expression")
        self.edit_btn.clicked.connect(self.edit_expresion)
        lo.addWidget(self.edit_btn)

        self.from_word_label = QLabel("loop over frames")
        lo.addWidget(self.from_word_label)
        self.run_from_input = QLineEdit("0")
        self.run_from_input.setValidator(QIntValidator())
        lo.addWidget(self.run_from_input)
        self.to_word_label = QLabel(" ~ ")
        lo.addWidget(self.to_word_label)
        self.run_to_input = QLineEdit("1")
        self.run_to_input.setValidator(QIntValidator())
        lo.addWidget(self.run_to_input)
        self.setLayout(lo)

    def edit_expresion(self):
        """Open the script editor.  [Changed] The editor and the proc list use the controller."""
        expression_edit = ExpressionEditor(self.sj).exec()
        if expression_edit == QDialog.Accepted:
            self.command_func_combo.clear()
            self.command_func_combo.addItems(self.sj.get_tcl_procs())

    def run_expression(self):
        """Run the selected TCL proc over the frame range (see ``ShellJekyll.run_tcl_expression``).

        [Changed] Works now: the old body built the argument dict with the loop
        variable ``frame`` before the loop (``UnboundLocalError`` on every
        click).  Empty range fields are ignored instead of raising.
        """
        try:
            from_frame = int(self.run_from_input.text())
            to_frame = int(self.run_to_input.text())
        except ValueError:
            return
        self.sj.run_tcl_expression(
            func_name=self.command_func_combo.currentText(),
            from_frame=from_frame,
            to_frame=to_frame
        )
        flash_button(self.exec_btn, flash_text="Executed", original_text="Run Expression")


class CELExpressionWidget(QWidget):
    def __init__(self, controller):
        """``controller``: the ``shell_jekyll.api.ShellJekyll`` that runs the expression.

        [Changed] A missing presets file now raises ``FileNotFoundError`` with the
        path (it was a bare ``raise Exception``); the no-op ``lo.addStretch``
        (missing parentheses) was removed, so the layout is unchanged.
        """
        super().__init__()
        self.sj = controller
        lo = QHBoxLayout()
        self.cel_input = QLineEdit()
        self.cel_input.setPlaceholderText("CEL expression ...")
        self.cel_input.setFixedWidth(220)
        lo.addWidget(self.cel_input)
        with open(PRESETS_PATH, "r", encoding="utf-8") as f:
            self.presets = json.load(f)
        preset_completer = QCompleter()
        preset_completer.setModel(QStringListModel(self.presets))
        preset_completer.setCompletionMode(QCompleter.PopupCompletion)
        self.cel_input.setCompleter(preset_completer)
        self.cel_input.editingFinished.connect(self.complete_presets)

        self.exec_btn = QPushButton("Run Expression")
        self.exec_btn.clicked.connect(self.run_expression)
        lo.addWidget(self.exec_btn)

        self.from_word_label = QLabel("loop over frames")
        lo.addWidget(self.from_word_label)
        self.run_from_input = QLineEdit("0")
        self.run_from_input.setValidator(QIntValidator())
        lo.addWidget(self.run_from_input)
        self.to_word_label = QLabel(" ~ ")
        lo.addWidget(self.to_word_label)
        self.run_to_input = QLineEdit("1")
        self.run_to_input.setValidator(QIntValidator())
        lo.addWidget(self.run_to_input)
        self.setLayout(lo)

    def run_expression(self):
        """Run the CEL expression over the frame range (see ``ShellJekyll.run_cel_expression``).

        The debug ``print`` of ``base_frame_list`` / ``asdict(gb_var)`` was removed.
        """
        try:
            from_frame = int(self.run_from_input.text())
            to_frame = int(self.run_to_input.text())
        except ValueError:
            return
        self.sj.run_cel_expression(
            expression=self.cel_input.text(),
            from_frame=from_frame,
            to_frame=to_frame
        )
        flash_button(self.exec_btn, flash_text="Executed", original_text="Run Expression")

    def complete_presets(self):
        """Replace a typed ``$preset`` name by its expression (unchanged)."""
        if not self.cel_input.text().startswith("$"):
            return
        preset_used = self.cel_input.text()
        self.cel_input.setText(self.presets.get(preset_used, ""))
