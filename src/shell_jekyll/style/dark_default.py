# --- main_win Visual theme ---------------------------------
MAIN_WIN_BG = "#1b1c22"
MAIN_WIN_PANEL = "#24252c"
MAIN_WIN_BORDER = "#3a3b45"
MAIN_WIN_TEXT = "#e6e6ec"
MAIN_WIN_TEXT_DIM = "#9a9ba8"
MAIN_WIN_ACCENT = "#5b8cff"
MAIN_WIN_ACCENT_HOVER = "#6f9bff"
MAIN_WIN_ACCENT_PRESSED = "#4a76e0"
MAIN_WIN_SUCCESS = "#43b581"

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
    background-color: #34353f;
    border: 1px solid {MAIN_WIN_ACCENT};
}}
QPushButton:pressed {{
    background-color: #202128;
}}
QPushButton:disabled {{
    color: #6b6c78;
    background-color: #202128;
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
EXP_EDITOR_BG = "#1b1c22"
EXP_EDITOR_PANEL = "#24252c"
EXP_EDITOR_BORDER = "#3a3b45"
EXP_EDITOR_TEXT = "#e6e6ec"
EXP_EDITOR_ACCENT = "#5b8cff"
EXP_EDITOR_ACCENT_HOVER = "#6f9bff"
EXP_EDITOR_ACCENT_PRESSED = "#4a76e0"

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
    background-color: #34353f;
    border: 1px solid {EXP_EDITOR_ACCENT};
}}
QPushButton:pressed {{
    background-color: #202128;
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
REND_DIALOG_BG = "#1b1c22"
REND_DIALOG_PANEL = "#24252c"
REND_DIALOG_BORDER = "#3a3b45"
REND_DIALOG_TEXT = "#e6e6ec"
REND_DIALOG_ACCENT = "#5b8cff"
REND_DIALOG_ACCENT_HOVER = "#6f9bff"
REND_DIALOG_ACCENT_PRESSED = "#4a76e0"

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
    background-color: #34353f;
    border: 1px solid {REND_DIALOG_ACCENT};
}}
QPushButton:pressed {{
    background-color: #202128;
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