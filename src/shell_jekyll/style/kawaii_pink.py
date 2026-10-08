# --- main_win Visual theme ---------------------------------
MAIN_WIN_BG = "#fff0f5"
MAIN_WIN_PANEL = "#ffe1ec"
MAIN_WIN_BORDER = "#ffc2d9"
MAIN_WIN_TEXT = "#6b3550"
MAIN_WIN_TEXT_DIM = "#a9748f"
MAIN_WIN_ACCENT = "#ff6fa5"
MAIN_WIN_ACCENT_HOVER = "#ff8fb8"
MAIN_WIN_ACCENT_PRESSED = "#e0507f"
MAIN_WIN_SUCCESS = "#8fd9a8"

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
    background-color: #ffd2e2;
    border: 1px solid {MAIN_WIN_ACCENT};
}}
QPushButton:pressed {{
    background-color: #ffc2d9;
}}
QPushButton:disabled {{
    color: #d3a9bc;
    background-color: #ffe9f0;
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
EXP_EDITOR_BG = "#fff0f5"
EXP_EDITOR_PANEL = "#ffe1ec"
EXP_EDITOR_BORDER = "#ffc2d9"
EXP_EDITOR_TEXT = "#6b3550"
EXP_EDITOR_ACCENT = "#ff6fa5"
EXP_EDITOR_ACCENT_HOVER = "#ff8fb8"
EXP_EDITOR_ACCENT_PRESSED = "#e0507f"

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
    background-color: #ffd2e2;
    border: 1px solid {EXP_EDITOR_ACCENT};
}}
QPushButton:pressed {{
    background-color: #ffc2d9;
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
REND_DIALOG_BG = "#fff0f5"
REND_DIALOG_PANEL = "#ffe1ec"
REND_DIALOG_BORDER = "#ffc2d9"
REND_DIALOG_TEXT = "#6b3550"
REND_DIALOG_ACCENT = "#ff6fa5"
REND_DIALOG_ACCENT_HOVER = "#ff8fb8"
REND_DIALOG_ACCENT_PRESSED = "#e0507f"

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
    background-color: #ffd2e2;
    border: 1px solid {REND_DIALOG_ACCENT};
}}
QPushButton:pressed {{
    background-color: #ffc2d9;
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
