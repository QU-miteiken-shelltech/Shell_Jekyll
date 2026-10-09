from PySide6.QtWidgets import (
    QMainWindow, QWidget, QPushButton, QHBoxLayout, QVBoxLayout,
    QLabel, QFrame, QGraphicsDropShadowEffect, QComboBox
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QFont, QColor, QKeySequence, QShortcut

from shell_jekyll.ui.sj_editor.main_win.main_win import MainUserUi
from shell_jekyll.ui.sj_player.main_ui.vj_win import VjUserUi
from shell_jekyll import gb_var as gb_var_global

TITLE_TEXT = "Shell Jekyll"
SUBTITLE_TEXT = "Choose a mode to get started"
EDITOR_DESC = "Edit your timeline\nShortcut: Ctrl+1"   
PLAYER_DESC = "Play your movie\nShortcut: Ctrl+2"  


class LauncherCard(QFrame):

    def __init__(self, title: str, description: str, on_click):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setFixedSize(240, 320)

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(15)
        self._shadow.setOffset(0, 3)
        self._shadow.setColor(QColor(0, 0, 0, 90))
        self.setGraphicsEffect(self._shadow)

        lo = QVBoxLayout(self)
        lo.setContentsMargins(12, 12, 12, 12)
        lo.setSpacing(10)

        self.btn = QPushButton(title)
        self.btn.setMinimumHeight(220)
        self.btn.setStyleSheet("font-size: 30px; text-align: center")
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn.clicked.connect(on_click)
        lo.addWidget(self.btn)

        desc = QLabel(description)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        font = QFont()
        font.setPointSize(10)
        desc.setFont(font)
        lo.addWidget(desc)

    def enterEvent(self, event):
        self._shadow.setBlurRadius(30)
        self._shadow.setOffset(0, 6)
        self._shadow.setColor(QColor(0, 0, 0, 140))
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._shadow.setBlurRadius(15)
        self._shadow.setOffset(0, 3)
        self._shadow.setColor(QColor(0, 0, 0, 90))
        super().leaveEvent(event)


class LauncherUi(QWidget):
    def __init__(self):
        super().__init__()

        title_lb = QLabel(TITLE_TEXT)
        title_lb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(36)
        title_font.setBold(True)
        title_lb.setFont(title_font)

        subtitle_lb = QLabel(SUBTITLE_TEXT)
        subtitle_lb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_font = QFont()
        sub_font.setPointSize(13)
        subtitle_lb.setFont(sub_font)

        self.editor_card = LauncherCard("Jekyll\nEditor", EDITOR_DESC, self.go_editor)
        self.vj_card = LauncherCard("Jekyll\nPlayer", PLAYER_DESC, self.go_vj)
        self.go_editor_btn = self.editor_card.btn
        self.go_vj_btn = self.vj_card.btn

        cards_lo = QHBoxLayout()
        cards_lo.setSpacing(40)
        cards_lo.addStretch(1)
        cards_lo.addWidget(self.editor_card)
        cards_lo.addWidget(self.vj_card)
        cards_lo.addStretch(1)

        switch_style_lo = QHBoxLayout()
        switch_style_lo.addStretch(1)                       
        self.switch_style_combo = QComboBox()
        self.switch_style_combo.clear()
        self.switch_style_combo.addItems([style for style in gb_var_global.styles])
        self.settings = QSettings("Shell Tech", "Shell Jekyll")
        self.switch_style_combo.setCurrentText(self.settings.value("default_style_sheet"))
        self.switch_style_combo.currentIndexChanged.connect(self.switch_style)
        switch_style_lo.addWidget(self.switch_style_combo)
        set_default_btn = QPushButton("Default")
        set_default_btn.clicked.connect(
            lambda : self.settings.setValue("default_style_sheet", self.switch_style_combo.currentText())
        )
        switch_style_lo.addWidget(set_default_btn)

        main_lo = QVBoxLayout()
        main_lo.addLayout(switch_style_lo)
        main_lo.setContentsMargins(30, 30, 30, 30)
        main_lo.setSpacing(12)
        main_lo.addStretch(2)
        main_lo.addWidget(title_lb)
        main_lo.addWidget(subtitle_lb)
        main_lo.addSpacing(30)
        main_lo.addLayout(cards_lo)
        main_lo.addStretch(3)

        self.setStyleSheet(gb_var_global.style_script.MAIN_WIN_STYLESHEET)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setLayout(main_lo)

        QShortcut(QKeySequence("Ctrl+1"), self, activated=self.go_editor)
        QShortcut(QKeySequence("Ctrl+2"), self, activated=self.go_vj)

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

    def switch_style(self):
        gb_var_global.style_script = gb_var_global.styles[self.switch_style_combo.currentText()]
        self.setStyleSheet(gb_var_global.style_script.MAIN_WIN_STYLESHEET)