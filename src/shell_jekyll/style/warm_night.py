# =====================================================================
#  WARM NIGHT THEME  (夜間・長時間作業向け、ブルーライト控えめ / Qt stylesheet)
#  - 暖色寄りの暗色背景 + アンバーのアクセント
#  - 変数名は theme_cyberpunk.py と共通 (import 先の切替だけで差し替え可能)
# =====================================================================

# --- main_win Visual theme ---------------------------------
MAIN_WIN_BG = "#1c1815"
MAIN_WIN_PANEL = "#26211d"
MAIN_WIN_BORDER = "#4a3f36"
MAIN_WIN_TEXT = "#eadfce"
MAIN_WIN_TEXT_DIM = "#a39482"
MAIN_WIN_ACCENT = "#e0a458"
MAIN_WIN_ACCENT_HOVER = "#ebb872"
MAIN_WIN_ACCENT_PRESSED = "#c58b3f"
MAIN_WIN_SUCCESS = "#8fbf6a"

# [追加] main_win 用の拡張カラー
MAIN_WIN_ACCENT_ALT = "#d97b66"
MAIN_WIN_ACCENT_ALT_HOVER = "#e3917e"
MAIN_WIN_ACCENT_ALT_PRESSED = "#b9604d"
MAIN_WIN_ACCENT_TEXT = "#1c1815"
MAIN_WIN_PANEL_HOVER = "#322b25"
MAIN_WIN_PANEL_PRESSED = "#1a1613"
MAIN_WIN_DISABLED_TEXT = "#6b5f53"
MAIN_WIN_SELECTION = "#4a3a28"
MAIN_WIN_WARNING = "#e8c547"
MAIN_WIN_FONT = "'Segoe UI', 'Helvetica Neue', sans-serif"

MAIN_WIN_STYLESHEET = f"""
QWidget {{
    background-color: {MAIN_WIN_BG};
    color: {MAIN_WIN_TEXT};
    font-family: {MAIN_WIN_FONT};
    font-size: 13px;
    selection-background-color: {MAIN_WIN_SELECTION};
    selection-color: {MAIN_WIN_ACCENT_HOVER};
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
    background-color: {MAIN_WIN_PANEL_HOVER};
    border: 1px solid {MAIN_WIN_ACCENT};
}}
QPushButton:pressed {{
    background-color: {MAIN_WIN_PANEL_PRESSED};
}}
QPushButton:disabled {{
    color: {MAIN_WIN_DISABLED_TEXT};
    background-color: {MAIN_WIN_PANEL_PRESSED};
    border: 1px solid {MAIN_WIN_PANEL};
}}
QPushButton#primaryButton {{
    background-color: {MAIN_WIN_ACCENT};
    color: {MAIN_WIN_ACCENT_TEXT};
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
QComboBox QAbstractItemView {{
    background-color: {MAIN_WIN_PANEL};
    color: {MAIN_WIN_TEXT};
    border: 1px solid {MAIN_WIN_BORDER};
    selection-background-color: {MAIN_WIN_SELECTION};
    selection-color: {MAIN_WIN_ACCENT_HOVER};
    outline: none;
}}
QToolTip {{
    background-color: {MAIN_WIN_PANEL_PRESSED};
    color: {MAIN_WIN_TEXT};
    border: 1px solid {MAIN_WIN_BORDER};
    padding: 4px 6px;
}}
QScrollBar:vertical {{
    background: {MAIN_WIN_PANEL_PRESSED};
    width: 10px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {MAIN_WIN_BORDER};
    min-height: 24px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical:hover {{
    background: {MAIN_WIN_ACCENT_PRESSED};
}}
QScrollBar:horizontal {{
    background: {MAIN_WIN_PANEL_PRESSED};
    height: 10px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {MAIN_WIN_BORDER};
    min-width: 24px;
    border-radius: 5px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {MAIN_WIN_ACCENT_PRESSED};
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    width: 0px;
    height: 0px;
}}
"""
# --- main_win Visual theme ---------------------------------



# --- expression_editor Visual theme ---------------------------------
EXP_EDITOR_BG = "#1c1815"
EXP_EDITOR_PANEL = "#26211d"
EXP_EDITOR_BORDER = "#4a3f36"
EXP_EDITOR_TEXT = "#eadfce"
EXP_EDITOR_ACCENT = "#e0a458"
EXP_EDITOR_ACCENT_HOVER = "#ebb872"
EXP_EDITOR_ACCENT_PRESSED = "#c58b3f"

# [追加] expression_editor 用の拡張カラー
EXP_EDITOR_ACCENT_ALT = "#d97b66"
EXP_EDITOR_ACCENT_ALT_HOVER = "#e3917e"
EXP_EDITOR_ACCENT_ALT_PRESSED = "#b9604d"
EXP_EDITOR_ACCENT_TEXT = "#1c1815"
EXP_EDITOR_PANEL_HOVER = "#322b25"
EXP_EDITOR_PANEL_PRESSED = "#1a1613"
EXP_EDITOR_CODE_TEXT = "#f0c987"
EXP_EDITOR_SELECTION = "#4a3a28"
EXP_EDITOR_FONT = "'Segoe UI', 'Helvetica Neue', sans-serif"
EXP_EDITOR_MONO_FONT = "Consolas, 'Courier New', monospace"

EXP_EDITOR_STYLESHEET = f"""
QDialog {{
    background-color: {EXP_EDITOR_BG};
    color: {EXP_EDITOR_TEXT};
    font-family: {EXP_EDITOR_FONT};
    font-size: 13px;
}}
QLabel {{
    color: {EXP_EDITOR_TEXT};
    background: transparent;
}}
QPlainTextEdit {{
    background-color: {EXP_EDITOR_PANEL};
    color: {EXP_EDITOR_CODE_TEXT};
    border: 1px solid {EXP_EDITOR_BORDER};
    border-radius: 6px;
    padding: 8px;
    font-family: {EXP_EDITOR_MONO_FONT};
    selection-background-color: {EXP_EDITOR_SELECTION};
    selection-color: {EXP_EDITOR_ACCENT_HOVER};
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
    background-color: {EXP_EDITOR_PANEL_HOVER};
    border: 1px solid {EXP_EDITOR_ACCENT};
}}
QPushButton:pressed {{
    background-color: {EXP_EDITOR_PANEL_PRESSED};
}}
QPushButton#primaryButton {{
    background-color: {EXP_EDITOR_ACCENT};
    color: {EXP_EDITOR_ACCENT_TEXT};
    border: 1px solid {EXP_EDITOR_ACCENT};
    font-weight: 600;
}}
QPushButton#primaryButton:hover {{
    background-color: {EXP_EDITOR_ACCENT_HOVER};
}}
QPushButton#primaryButton:pressed {{
    background-color: {EXP_EDITOR_ACCENT_PRESSED};
}}
QScrollBar:vertical {{
    background: {EXP_EDITOR_PANEL_PRESSED};
    width: 10px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {EXP_EDITOR_BORDER};
    min-height: 24px;
    border-radius: 5px;
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    width: 0px;
    height: 0px;
}}
"""
# --- expression_editor Visual theme ---------------------------------



# --- render_dialog Visual theme ---------------------------------
REND_DIALOG_BG = "#1c1815"
REND_DIALOG_PANEL = "#26211d"
REND_DIALOG_BORDER = "#4a3f36"
REND_DIALOG_TEXT = "#eadfce"
REND_DIALOG_ACCENT = "#e0a458"
REND_DIALOG_ACCENT_HOVER = "#ebb872"
REND_DIALOG_ACCENT_PRESSED = "#c58b3f"

# [追加] render_dialog 用の拡張カラー
REND_DIALOG_ACCENT_ALT = "#d97b66"
REND_DIALOG_ACCENT_ALT_HOVER = "#e3917e"
REND_DIALOG_ACCENT_ALT_PRESSED = "#b9604d"
REND_DIALOG_ACCENT_TEXT = "#1c1815"
REND_DIALOG_PANEL_HOVER = "#322b25"
REND_DIALOG_PANEL_PRESSED = "#1a1613"
REND_DIALOG_SELECTION = "#4a3a28"
REND_DIALOG_FONT = "'Segoe UI', 'Helvetica Neue', sans-serif"

REND_DIALOG_STYLESHEET = f"""
QDialog {{
    background-color: {REND_DIALOG_BG};
    color: {REND_DIALOG_TEXT};
    font-family: {REND_DIALOG_FONT};
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
    background-color: {REND_DIALOG_PANEL_HOVER};
    border: 1px solid {REND_DIALOG_ACCENT};
}}
QPushButton:pressed {{
    background-color: {REND_DIALOG_PANEL_PRESSED};
}}
QPushButton#primaryButton {{
    background-color: {REND_DIALOG_ACCENT};
    color: {REND_DIALOG_ACCENT_TEXT};
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
QComboBox QAbstractItemView {{
    background-color: {REND_DIALOG_PANEL};
    color: {REND_DIALOG_TEXT};
    border: 1px solid {REND_DIALOG_BORDER};
    selection-background-color: {REND_DIALOG_SELECTION};
    selection-color: {REND_DIALOG_ACCENT_HOVER};
    outline: none;
}}
"""
# --- render_dialog Visual theme ---------------------------------