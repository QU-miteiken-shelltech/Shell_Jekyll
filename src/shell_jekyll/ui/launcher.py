from PySide6.QtWidgets import (
    QMainWindow, QWidget, QPushButton, 
    QHBoxLayout
)
from PySide6.QtCore import Qt

from shell_jekyll.ui.sj_editor.main_win.main_win import MainUserUi
from shell_jekyll.ui.sj_player.main_ui.vj_win import VjUserUi
from shell_jekyll import gb_var as gb_var_global

class LauncherUi(QWidget):
    def __init__(self):
        super().__init__()

        main_lo = QHBoxLayout()

        self.go_editor_btn = QPushButton("Jekyll\nEditor")
        self.go_editor_btn.setFixedSize(200, 300)
        self.go_editor_btn.setStyleSheet("font-size: 30px; text-align: center")
        self.go_editor_btn.clicked.connect(self.go_editor)
        main_lo.addWidget(self.go_editor_btn)
        self.go_vj_btn = QPushButton("Jekyll\nPlayer")
        self.go_vj_btn.setFixedSize(200, 300)
        self.go_vj_btn.setStyleSheet("font-size: 30px; text-align: center")
        self.go_vj_btn.clicked.connect(self.go_vj)
        main_lo.addWidget(self.go_vj_btn)

        self.setStyleSheet(gb_var_global.style_script.MAIN_WIN_STYLESHEET)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setLayout(main_lo)

    def go_editor(self):
        main_ui = MainUserUi()
        win = self.window()
        if isinstance(win, QMainWindow):
            win.setCentralWidget(main_ui)

    def go_vj(self):
            main_ui = VjUserUi()
            win = self.window()
            if isinstance(win, QMainWindow):
                win.setCentralWidget(main_ui)

