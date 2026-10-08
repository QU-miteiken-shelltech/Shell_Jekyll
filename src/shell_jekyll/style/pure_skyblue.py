# --- main_win Visual theme ---------------------------------
MAIN_WIN_BG = "#eef7fc"
MAIN_WIN_PANEL = "#dcf0fa"
MAIN_WIN_BORDER = "#b8e2f2"
MAIN_WIN_TEXT = "#33475b"
MAIN_WIN_TEXT_DIM = "#7093a8"
MAIN_WIN_ACCENT = "#4fc3f7"
MAIN_WIN_ACCENT_HOVER = "#7ad4fa"
MAIN_WIN_ACCENT_PRESSED = "#2fa8de"
MAIN_WIN_SUCCESS = "#5fd3a0"

MAIN_WIN_STYLESHEET = f"""
QWidget {{
    background-color: {MAIN_WIN_BG};
    color: {MAIN_WIN_TEXT};
    font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
    font-size: 13px;
}}
QLabel {{
    color: {MAIN_WIN_TEXT_DIM};
    background: transparent;
}}
QPushButton {{
    background-color: {MAIN_WIN_PANEL};
    color: {MAIN_WIN_TEXT};
    border: 1px solid {MAIN_WIN_BORDER};
    border-radius: 6px;
    padding: 6px 14px;
}}
QPushButton:hover {{
    background-color: #c9e9f8;
    border: 1px solid {MAIN_WIN_ACCENT};
}}
QPushButton:pressed {{
    background-color: #b8e2f2;
}}
QPushButton:disabled {{
    color: #a7bccb;
    background-color: #e4f3fa;
    border: 1px solid {MAIN_WIN_PANEL};
}}
QPushButton#primaryButton {{
    background-color: {MAIN_WIN_ACCENT};
    color: #ffffff;
    border: 1px solid {MAIN_WIN_ACCENT};
    font-weight: 600;
}}
QPushButton#primaryButton:hover {{
    background-color: {MAIN_WIN_ACCENT_HOVER};
}}
QPushButton#primaryButton:pressed {{
    background-color: {MAIN_WIN_ACCENT_PRESSED};
}}
QLineEdit, QComboBox {{
    background-color: {MAIN_WIN_PANEL};
    color: {MAIN_WIN_TEXT};
    border: 1px solid {MAIN_WIN_BORDER};
    border-radius: 6px;
    padding: 4px 8px;
}}
QLineEdit:focus, QComboBox:focus {{
    border: 1px solid {MAIN_WIN_ACCENT};
}}
QComboBox::drop-down {{
    border: none;
}}
"""
# --- main_win Visual theme ---------------------------------



# --- expression_editor Visual theme ---------------------------------
EXP_EDITOR_BG = "#eef7fc"
EXP_EDITOR_PANEL = "#dcf0fa"
EXP_EDITOR_BORDER = "#b8e2f2"
EXP_EDITOR_TEXT = "#33475b"
EXP_EDITOR_ACCENT = "#4fc3f7"
EXP_EDITOR_ACCENT_HOVER = "#7ad4fa"
EXP_EDITOR_ACCENT_PRESSED = "#2fa8de"

EXP_EDITOR_STYLESHEET = f"""
QDialog {{
    background-color: {EXP_EDITOR_BG};
    color: {EXP_EDITOR_TEXT};
    font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
    font-size: 13px;
}}
QPlainTextEdit {{
    background-color: {EXP_EDITOR_PANEL};
    color: {EXP_EDITOR_TEXT};
    border: 1px solid {EXP_EDITOR_BORDER};
    border-radius: 6px;
    padding: 8px;
    font-family: Consolas, 'Courier New', monospace;
}}
QPlainTextEdit:focus {{
    border: 1px solid {EXP_EDITOR_ACCENT};
}}
QPushButton {{
    background-color: {EXP_EDITOR_PANEL};
    color: {EXP_EDITOR_TEXT};
    border: 1px solid {EXP_EDITOR_BORDER};
    border-radius: 6px;
    padding: 6px 14px;
}}
QPushButton:hover {{
    background-color: #c9e9f8;
    border: 1px solid {EXP_EDITOR_ACCENT};
}}
QPushButton:pressed {{
    background-color: #b8e2f2;
}}
QPushButton#primaryButton {{
    background-color: {EXP_EDITOR_ACCENT};
    color: #ffffff;
    border: 1px solid {EXP_EDITOR_ACCENT};
    font-weight: 600;
}}
QPushButton#primaryButton:hover {{
    background-color: {EXP_EDITOR_ACCENT_HOVER};
}}
QPushButton#primaryButton:pressed {{
    background-color: {EXP_EDITOR_ACCENT_PRESSED};
}}
"""
# --- expression_editor Visual theme ---------------------------------



# --- render_dialog Visual theme ---------------------------------
REND_DIALOG_BG = "#eef7fc"
REND_DIALOG_PANEL = "#dcf0fa"
REND_DIALOG_BORDER = "#b8e2f2"
REND_DIALOG_TEXT = "#33475b"
REND_DIALOG_ACCENT = "#4fc3f7"
REND_DIALOG_ACCENT_HOVER = "#7ad4fa"
REND_DIALOG_ACCENT_PRESSED = "#2fa8de"

REND_DIALOG_STYLESHEET = f"""
QDialog {{
    background-color: {REND_DIALOG_BG};
    color: {REND_DIALOG_TEXT};
    font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
    font-size: 13px;
}}
QLabel {{
    color: {REND_DIALOG_TEXT};
    background: transparent;
}}
QPushButton {{
    background-color: {REND_DIALOG_PANEL};
    color: {REND_DIALOG_TEXT};
    border: 1px solid {REND_DIALOG_BORDER};
    border-radius: 6px;
    padding: 6px 14px;
}}
QPushButton:hover {{
    background-color: #c9e9f8;
    border: 1px solid {REND_DIALOG_ACCENT};
}}
QPushButton:pressed {{
    background-color: #b8e2f2;
}}
QPushButton#primaryButton {{
    background-color: {REND_DIALOG_ACCENT};
    color: #ffffff;
    border: 1px solid {REND_DIALOG_ACCENT};
    font-weight: 600;
}}
QPushButton#primaryButton:hover {{
    background-color: {REND_DIALOG_ACCENT_HOVER};
}}
QPushButton#primaryButton:pressed {{
    background-color: {REND_DIALOG_ACCENT_PRESSED};
}}
QLineEdit, QComboBox {{
    background-color: {REND_DIALOG_PANEL};
    color: {REND_DIALOG_TEXT};
    border: 1px solid {REND_DIALOG_BORDER};
    border-radius: 6px;
    padding: 4px 8px;
}}
QLineEdit:focus, QComboBox:focus {{
    border: 1px solid {REND_DIALOG_ACCENT};
}}
QComboBox::drop-down {{
    border: none;
}}
"""
# --- render_dialog Visual theme ---------------------------------
