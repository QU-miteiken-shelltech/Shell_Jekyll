# =====================================================================
#  HIGH CONTRAST THEME  (弱視・視認性重視 / Qt stylesheet)
#  - 黒背景 + 白文字 + 黄アクセント。枠線 2px、文字サイズ 15px
#  - 変数名は theme_cyberpunk.py と共通 (import 先の切替だけで差し替え可能)
# =====================================================================

# --- main_win Visual theme ---------------------------------
MAIN_WIN_BG = "#000000"
MAIN_WIN_PANEL = "#0d0d0d"
MAIN_WIN_BORDER = "#ffffff"
MAIN_WIN_TEXT = "#ffffff"
MAIN_WIN_TEXT_DIM = "#d0d0d0"
MAIN_WIN_ACCENT = "#ffd400"
MAIN_WIN_ACCENT_HOVER = "#ffe766"
MAIN_WIN_ACCENT_PRESSED = "#c9a600"
MAIN_WIN_SUCCESS = "#00ff7f"

# [追加] main_win 用の拡張カラー
MAIN_WIN_ACCENT_ALT = "#00e5ff"
MAIN_WIN_ACCENT_ALT_HOVER = "#66f0ff"
MAIN_WIN_ACCENT_ALT_PRESSED = "#00b2c7"
MAIN_WIN_ACCENT_TEXT = "#000000"
MAIN_WIN_PANEL_HOVER = "#1f1f1f"
MAIN_WIN_PANEL_PRESSED = "#333333"
MAIN_WIN_DISABLED_TEXT = "#8a8a8a"
MAIN_WIN_SELECTION = "#ffd400"
MAIN_WIN_WARNING = "#ff9500"
MAIN_WIN_FONT = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"

MAIN_WIN_STYLESHEET = f"""
QWidget {{
    background-color: {MAIN_WIN_BG};
    color: {MAIN_WIN_TEXT};
    font-family: {MAIN_WIN_FONT};
    font-size: 15px;
    selection-background-color: {MAIN_WIN_SELECTION};
    selection-color: {MAIN_WIN_ACCENT_TEXT};
}}
QLabel {{
    color: {MAIN_WIN_TEXT_DIM};
    background: transparent;
}}
QPushButton {{
    background-color: {MAIN_WIN_PANEL};
    color: {MAIN_WIN_TEXT};
    border: 2px solid {MAIN_WIN_BORDER};
    border-radius: 4px;
    padding: 8px 18px;
}}
QPushButton:hover {{
    background-color: {MAIN_WIN_PANEL_HOVER};
    border: 2px solid {MAIN_WIN_ACCENT};
    color: {MAIN_WIN_ACCENT};
}}
QPushButton:focus {{
    border: 3px solid {MAIN_WIN_ACCENT_ALT};
}}
QPushButton:pressed {{
    background-color: {MAIN_WIN_PANEL_PRESSED};
}}
QPushButton:disabled {{
    color: {MAIN_WIN_DISABLED_TEXT};
    background-color: {MAIN_WIN_BG};
    border: 2px dashed {MAIN_WIN_DISABLED_TEXT};
}}
QPushButton#primaryButton {{
    background-color: {MAIN_WIN_ACCENT};
    color: {MAIN_WIN_ACCENT_TEXT};
    border: 2px solid {MAIN_WIN_ACCENT};
    font-weight: 700;
}}
QPushButton#primaryButton:hover {{
    background-color: {MAIN_WIN_ACCENT_HOVER};
    color: {MAIN_WIN_ACCENT_TEXT};
}}
QPushButton#primaryButton:pressed {{
    background-color: {MAIN_WIN_ACCENT_PRESSED};
    color: {MAIN_WIN_ACCENT_TEXT};
}}
QLineEdit, QComboBox {{
    background-color: {MAIN_WIN_PANEL};
    color: {MAIN_WIN_TEXT};
    border: 2px solid {MAIN_WIN_BORDER};
    border-radius: 4px;
    padding: 6px 10px;
}}
QLineEdit:focus, QComboBox:focus {{
    border: 3px solid {MAIN_WIN_ACCENT};
}}
QComboBox::drop-down {{
    border: none;
}}
QComboBox QAbstractItemView {{
    background-color: {MAIN_WIN_BG};
    color: {MAIN_WIN_TEXT};
    border: 2px solid {MAIN_WIN_BORDER};
    selection-background-color: {MAIN_WIN_SELECTION};
    selection-color: {MAIN_WIN_ACCENT_TEXT};
    outline: none;
}}
QToolTip {{
    background-color: {MAIN_WIN_BG};
    color: {MAIN_WIN_TEXT};
    border: 2px solid {MAIN_WIN_ACCENT};
    padding: 4px 8px;
}}
QScrollBar:vertical {{
    background: {MAIN_WIN_PANEL};
    width: 16px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {MAIN_WIN_TEXT};
    min-height: 30px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical:hover {{
    background: {MAIN_WIN_ACCENT};
}}
QScrollBar:horizontal {{
    background: {MAIN_WIN_PANEL};
    height: 16px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {MAIN_WIN_TEXT};
    min-width: 30px;
    border-radius: 3px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {MAIN_WIN_ACCENT};
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    width: 0px;
    height: 0px;
}}
"""
# --- main_win Visual theme ---------------------------------



# --- expression_editor Visual theme ---------------------------------
EXP_EDITOR_BG = "#000000"
EXP_EDITOR_PANEL = "#0d0d0d"
EXP_EDITOR_BORDER = "#ffffff"
EXP_EDITOR_TEXT = "#ffffff"
EXP_EDITOR_ACCENT = "#ffd400"
EXP_EDITOR_ACCENT_HOVER = "#ffe766"
EXP_EDITOR_ACCENT_PRESSED = "#c9a600"

# [追加] expression_editor 用の拡張カラー
EXP_EDITOR_ACCENT_ALT = "#00e5ff"
EXP_EDITOR_ACCENT_ALT_HOVER = "#66f0ff"
EXP_EDITOR_ACCENT_ALT_PRESSED = "#00b2c7"
EXP_EDITOR_ACCENT_TEXT = "#000000"
EXP_EDITOR_PANEL_HOVER = "#1f1f1f"
EXP_EDITOR_PANEL_PRESSED = "#333333"
EXP_EDITOR_CODE_TEXT = "#ffffff"
EXP_EDITOR_SELECTION = "#ffd400"
EXP_EDITOR_FONT = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
EXP_EDITOR_MONO_FONT = "Consolas, 'Courier New', monospace"

EXP_EDITOR_STYLESHEET = f"""
QDialog {{
    background-color: {EXP_EDITOR_BG};
    color: {EXP_EDITOR_TEXT};
    font-family: {EXP_EDITOR_FONT};
    font-size: 15px;
}}
QLabel {{
    color: {EXP_EDITOR_TEXT};
    background: transparent;
}}
QPlainTextEdit {{
    background-color: {EXP_EDITOR_PANEL};
    color: {EXP_EDITOR_CODE_TEXT};
    border: 2px solid {EXP_EDITOR_BORDER};
    border-radius: 4px;
    padding: 8px;
    font-family: {EXP_EDITOR_MONO_FONT};
    font-size: 16px;
    selection-background-color: {EXP_EDITOR_SELECTION};
    selection-color: {EXP_EDITOR_ACCENT_TEXT};
}}
QPlainTextEdit:focus {{
    border: 3px solid {EXP_EDITOR_ACCENT};
}}
QPushButton {{
    background-color: {EXP_EDITOR_PANEL};
    color: {EXP_EDITOR_TEXT};
    border: 2px solid {EXP_EDITOR_BORDER};
    border-radius: 4px;
    padding: 8px 18px;
}}
QPushButton:hover {{
    background-color: {EXP_EDITOR_PANEL_HOVER};
    border: 2px solid {EXP_EDITOR_ACCENT};
    color: {EXP_EDITOR_ACCENT};
}}
QPushButton:focus {{
    border: 3px solid {EXP_EDITOR_ACCENT_ALT};
}}
QPushButton:pressed {{
    background-color: {EXP_EDITOR_PANEL_PRESSED};
}}
QPushButton#primaryButton {{
    background-color: {EXP_EDITOR_ACCENT};
    color: {EXP_EDITOR_ACCENT_TEXT};
    border: 2px solid {EXP_EDITOR_ACCENT};
    font-weight: 700;
}}
QPushButton#primaryButton:hover {{
    background-color: {EXP_EDITOR_ACCENT_HOVER};
    color: {EXP_EDITOR_ACCENT_TEXT};
}}
QPushButton#primaryButton:pressed {{
    background-color: {EXP_EDITOR_ACCENT_PRESSED};
    color: {EXP_EDITOR_ACCENT_TEXT};
}}
QScrollBar:vertical {{
    background: {EXP_EDITOR_PANEL};
    width: 16px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {EXP_EDITOR_TEXT};
    min-height: 30px;
    border-radius: 3px;
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    width: 0px;
    height: 0px;
}}
"""
# --- expression_editor Visual theme ---------------------------------



# --- render_dialog Visual theme ---------------------------------
REND_DIALOG_BG = "#000000"
REND_DIALOG_PANEL = "#0d0d0d"
REND_DIALOG_BORDER = "#ffffff"
REND_DIALOG_TEXT = "#ffffff"
REND_DIALOG_ACCENT = "#ffd400"
REND_DIALOG_ACCENT_HOVER = "#ffe766"
REND_DIALOG_ACCENT_PRESSED = "#c9a600"

# [追加] render_dialog 用の拡張カラー
REND_DIALOG_ACCENT_ALT = "#00e5ff"
REND_DIALOG_ACCENT_ALT_HOVER = "#66f0ff"
REND_DIALOG_ACCENT_ALT_PRESSED = "#00b2c7"
REND_DIALOG_ACCENT_TEXT = "#000000"
REND_DIALOG_PANEL_HOVER = "#1f1f1f"
REND_DIALOG_PANEL_PRESSED = "#333333"
REND_DIALOG_SELECTION = "#ffd400"
REND_DIALOG_FONT = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"

REND_DIALOG_STYLESHEET = f"""
QDialog {{
    background-color: {REND_DIALOG_BG};
    color: {REND_DIALOG_TEXT};
    font-family: {REND_DIALOG_FONT};
    font-size: 15px;
}}
QLabel {{
    color: {REND_DIALOG_TEXT};
    background: transparent;
}}
QPushButton {{
    background-color: {REND_DIALOG_PANEL};
    color: {REND_DIALOG_TEXT};
    border: 2px solid {REND_DIALOG_BORDER};
    border-radius: 4px;
    padding: 8px 18px;
}}
QPushButton:hover {{
    background-color: {REND_DIALOG_PANEL_HOVER};
    border: 2px solid {REND_DIALOG_ACCENT};
    color: {REND_DIALOG_ACCENT};
}}
QPushButton:focus {{
    border: 3px solid {REND_DIALOG_ACCENT_ALT};
}}
QPushButton:pressed {{
    background-color: {REND_DIALOG_PANEL_PRESSED};
}}
QPushButton#primaryButton {{
    background-color: {REND_DIALOG_ACCENT};
    color: {REND_DIALOG_ACCENT_TEXT};
    border: 2px solid {REND_DIALOG_ACCENT};
    font-weight: 700;
}}
QPushButton#primaryButton:hover {{
    background-color: {REND_DIALOG_ACCENT_HOVER};
    color: {REND_DIALOG_ACCENT_TEXT};
}}
QPushButton#primaryButton:pressed {{
    background-color: {REND_DIALOG_ACCENT_PRESSED};
    color: {REND_DIALOG_ACCENT_TEXT};
}}
QLineEdit, QComboBox {{
    background-color: {REND_DIALOG_PANEL};
    color: {REND_DIALOG_TEXT};
    border: 2px solid {REND_DIALOG_BORDER};
    border-radius: 4px;
    padding: 6px 10px;
}}
QLineEdit:focus, QComboBox:focus {{
    border: 3px solid {REND_DIALOG_ACCENT};
}}
QComboBox::drop-down {{
    border: none;
}}
QComboBox QAbstractItemView {{
    background-color: {REND_DIALOG_BG};
    color: {REND_DIALOG_TEXT};
    border: 2px solid {REND_DIALOG_BORDER};
    selection-background-color: {REND_DIALOG_SELECTION};
    selection-color: {REND_DIALOG_ACCENT_TEXT};
    outline: none;
}}
"""
# --- render_dialog Visual theme ---------------------------------