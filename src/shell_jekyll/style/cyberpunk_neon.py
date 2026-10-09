# =====================================================================
#  CYBERPUNK THEME  (Qt stylesheet)
#  - 既存の変数名はすべて維持 (値のみ新デザインに更新)
#  - 新規変数は「追加」のみ
# =====================================================================

# --- main_win Visual theme ---------------------------------
MAIN_WIN_BG = "#0a0b12"
MAIN_WIN_PANEL = "#11121c"
MAIN_WIN_BORDER = "#1c4a5e"
MAIN_WIN_TEXT = "#d8f6ff"
MAIN_WIN_TEXT_DIM = "#6f8fa3"
MAIN_WIN_ACCENT = "#00f0ff"
MAIN_WIN_ACCENT_HOVER = "#5ffbff"
MAIN_WIN_ACCENT_PRESSED = "#00b8c4"
MAIN_WIN_SUCCESS = "#39ff88"

# [追加] main_win 用の拡張カラー
MAIN_WIN_ACCENT_ALT = "#ff2a6d"            # ネオンマゼンタ
MAIN_WIN_ACCENT_ALT_HOVER = "#ff5c8f"
MAIN_WIN_ACCENT_ALT_PRESSED = "#d11a56"
MAIN_WIN_ACCENT_TEXT = "#04060a"           # ネオン色の上に載せる文字色
MAIN_WIN_PANEL_HOVER = "#171a2b"
MAIN_WIN_PANEL_PRESSED = "#07080e"
MAIN_WIN_DISABLED_TEXT = "#44525e"
MAIN_WIN_SELECTION = "#12304a"
MAIN_WIN_WARNING = "#fcee09"
MAIN_WIN_FONT = "'Orbitron', 'Rajdhani', 'Segoe UI', 'Consolas', sans-serif"

MAIN_WIN_STYLESHEET = f"""
QWidget {{
    background-color: {MAIN_WIN_BG};
    color: {MAIN_WIN_TEXT};
    font-family: {MAIN_WIN_FONT};
    font-size: 13px;
    selection-background-color: {MAIN_WIN_SELECTION};
    selection-color: {MAIN_WIN_ACCENT};
}}
QLabel {{
    color: {MAIN_WIN_TEXT_DIM};
    background: transparent;
    letter-spacing: 1px;
}}
QPushButton {{
    background-color: {MAIN_WIN_PANEL};
    color: {MAIN_WIN_ACCENT};
    border: 1px solid {MAIN_WIN_BORDER};
    border-left: 3px solid {MAIN_WIN_ACCENT};
    border-radius: 2px;
    padding: 6px 16px;
    letter-spacing: 1px;
}}
QPushButton:hover {{
    background-color: {MAIN_WIN_PANEL_HOVER};
    color: {MAIN_WIN_ACCENT_HOVER};
    border: 1px solid {MAIN_WIN_ACCENT};
    border-left: 3px solid {MAIN_WIN_ACCENT_ALT};
}}
QPushButton:pressed {{
    background-color: {MAIN_WIN_PANEL_PRESSED};
    color: {MAIN_WIN_ACCENT_ALT};
    border: 1px solid {MAIN_WIN_ACCENT_ALT};
    border-left: 3px solid {MAIN_WIN_ACCENT_ALT};
}}
QPushButton:disabled {{
    color: {MAIN_WIN_DISABLED_TEXT};
    background-color: {MAIN_WIN_PANEL_PRESSED};
    border: 1px solid {MAIN_WIN_PANEL};
    border-left: 3px solid {MAIN_WIN_PANEL};
}}
QPushButton#primaryButton {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {MAIN_WIN_ACCENT}, stop:1 {MAIN_WIN_ACCENT_ALT});
    color: {MAIN_WIN_ACCENT_TEXT};
    border: 1px solid {MAIN_WIN_ACCENT};
    border-left: 3px solid {MAIN_WIN_ACCENT_ALT};
    font-weight: 700;
}}
QPushButton#primaryButton:hover {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {MAIN_WIN_ACCENT_HOVER}, stop:1 {MAIN_WIN_ACCENT_ALT_HOVER});
    color: {MAIN_WIN_ACCENT_TEXT};
    border: 1px solid {MAIN_WIN_ACCENT_HOVER};
}}
QPushButton#primaryButton:pressed {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {MAIN_WIN_ACCENT_PRESSED}, stop:1 {MAIN_WIN_ACCENT_ALT_PRESSED});
    color: {MAIN_WIN_ACCENT_TEXT};
    border: 1px solid {MAIN_WIN_ACCENT_PRESSED};
}}
QLineEdit, QComboBox {{
    background-color: {MAIN_WIN_PANEL};
    color: {MAIN_WIN_TEXT};
    border: 1px solid {MAIN_WIN_BORDER};
    border-bottom: 2px solid {MAIN_WIN_BORDER};
    border-radius: 2px;
    padding: 4px 8px;
}}
QLineEdit:hover, QComboBox:hover {{
    border: 1px solid {MAIN_WIN_ACCENT_PRESSED};
    border-bottom: 2px solid {MAIN_WIN_ACCENT_PRESSED};
}}
QLineEdit:focus, QComboBox:focus {{
    border: 1px solid {MAIN_WIN_ACCENT};
    border-bottom: 2px solid {MAIN_WIN_ACCENT_ALT};
    color: {MAIN_WIN_ACCENT_HOVER};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background-color: {MAIN_WIN_PANEL};
    color: {MAIN_WIN_TEXT};
    border: 1px solid {MAIN_WIN_ACCENT};
    selection-background-color: {MAIN_WIN_SELECTION};
    selection-color: {MAIN_WIN_ACCENT};
    outline: none;
}}
QToolTip {{
    background-color: {MAIN_WIN_PANEL_PRESSED};
    color: {MAIN_WIN_ACCENT};
    border: 1px solid {MAIN_WIN_ACCENT_ALT};
    padding: 4px 6px;
}}
QScrollBar:vertical {{
    background: {MAIN_WIN_PANEL_PRESSED};
    width: 10px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {MAIN_WIN_BORDER};
    border: 1px solid {MAIN_WIN_ACCENT_PRESSED};
    min-height: 24px;
    border-radius: 2px;
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
    border: 1px solid {MAIN_WIN_ACCENT_PRESSED};
    min-width: 24px;
    border-radius: 2px;
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
EXP_EDITOR_BG = "#0a0b12"
EXP_EDITOR_PANEL = "#11121c"
EXP_EDITOR_BORDER = "#1c4a5e"
EXP_EDITOR_TEXT = "#d8f6ff"
EXP_EDITOR_ACCENT = "#00f0ff"
EXP_EDITOR_ACCENT_HOVER = "#5ffbff"
EXP_EDITOR_ACCENT_PRESSED = "#00b8c4"

# [追加] expression_editor 用の拡張カラー
EXP_EDITOR_ACCENT_ALT = "#ff2a6d"
EXP_EDITOR_ACCENT_ALT_HOVER = "#ff5c8f"
EXP_EDITOR_ACCENT_ALT_PRESSED = "#d11a56"
EXP_EDITOR_ACCENT_TEXT = "#04060a"
EXP_EDITOR_PANEL_HOVER = "#171a2b"
EXP_EDITOR_PANEL_PRESSED = "#07080e"
EXP_EDITOR_CODE_TEXT = "#7dffb0"            # コード入力欄はターミナル風グリーン
EXP_EDITOR_SELECTION = "#12304a"
EXP_EDITOR_FONT = "'Orbitron', 'Rajdhani', 'Segoe UI', 'Consolas', sans-serif"
EXP_EDITOR_MONO_FONT = "'Share Tech Mono', Consolas, 'Courier New', monospace"

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
    letter-spacing: 1px;
}}
QPlainTextEdit {{
    background-color: {EXP_EDITOR_PANEL_PRESSED};
    color: {EXP_EDITOR_CODE_TEXT};
    border: 1px solid {EXP_EDITOR_BORDER};
    border-left: 3px solid {EXP_EDITOR_ACCENT_PRESSED};
    border-radius: 2px;
    padding: 8px;
    font-family: {EXP_EDITOR_MONO_FONT};
    selection-background-color: {EXP_EDITOR_SELECTION};
    selection-color: {EXP_EDITOR_ACCENT};
}}
QPlainTextEdit:focus {{
    border: 1px solid {EXP_EDITOR_ACCENT};
    border-left: 3px solid {EXP_EDITOR_ACCENT_ALT};
}}
QPushButton {{
    background-color: {EXP_EDITOR_PANEL};
    color: {EXP_EDITOR_ACCENT};
    border: 1px solid {EXP_EDITOR_BORDER};
    border-left: 3px solid {EXP_EDITOR_ACCENT};
    border-radius: 2px;
    padding: 6px 16px;
    letter-spacing: 1px;
}}
QPushButton:hover {{
    background-color: {EXP_EDITOR_PANEL_HOVER};
    color: {EXP_EDITOR_ACCENT_HOVER};
    border: 1px solid {EXP_EDITOR_ACCENT};
    border-left: 3px solid {EXP_EDITOR_ACCENT_ALT};
}}
QPushButton:pressed {{
    background-color: {EXP_EDITOR_PANEL_PRESSED};
    color: {EXP_EDITOR_ACCENT_ALT};
    border: 1px solid {EXP_EDITOR_ACCENT_ALT};
    border-left: 3px solid {EXP_EDITOR_ACCENT_ALT};
}}
QPushButton#primaryButton {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {EXP_EDITOR_ACCENT}, stop:1 {EXP_EDITOR_ACCENT_ALT});
    color: {EXP_EDITOR_ACCENT_TEXT};
    border: 1px solid {EXP_EDITOR_ACCENT};
    border-left: 3px solid {EXP_EDITOR_ACCENT_ALT};
    font-weight: 700;
}}
QPushButton#primaryButton:hover {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {EXP_EDITOR_ACCENT_HOVER}, stop:1 {EXP_EDITOR_ACCENT_ALT_HOVER});
    color: {EXP_EDITOR_ACCENT_TEXT};
    border: 1px solid {EXP_EDITOR_ACCENT_HOVER};
}}
QPushButton#primaryButton:pressed {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {EXP_EDITOR_ACCENT_PRESSED}, stop:1 {EXP_EDITOR_ACCENT_ALT_PRESSED});
    color: {EXP_EDITOR_ACCENT_TEXT};
    border: 1px solid {EXP_EDITOR_ACCENT_PRESSED};
}}
QScrollBar:vertical {{
    background: {EXP_EDITOR_PANEL_PRESSED};
    width: 10px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {EXP_EDITOR_BORDER};
    border: 1px solid {EXP_EDITOR_ACCENT_PRESSED};
    min-height: 24px;
    border-radius: 2px;
}}
QScrollBar::handle:vertical:hover {{
    background: {EXP_EDITOR_ACCENT_PRESSED};
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    width: 0px;
    height: 0px;
}}
"""
# --- expression_editor Visual theme ---------------------------------



# --- render_dialog Visual theme ---------------------------------
REND_DIALOG_BG = "#0a0b12"
REND_DIALOG_PANEL = "#11121c"
REND_DIALOG_BORDER = "#1c4a5e"
REND_DIALOG_TEXT = "#d8f6ff"
REND_DIALOG_ACCENT = "#00f0ff"
REND_DIALOG_ACCENT_HOVER = "#5ffbff"
REND_DIALOG_ACCENT_PRESSED = "#00b8c4"

# [追加] render_dialog 用の拡張カラー
REND_DIALOG_ACCENT_ALT = "#ff2a6d"
REND_DIALOG_ACCENT_ALT_HOVER = "#ff5c8f"
REND_DIALOG_ACCENT_ALT_PRESSED = "#d11a56"
REND_DIALOG_ACCENT_TEXT = "#04060a"
REND_DIALOG_PANEL_HOVER = "#171a2b"
REND_DIALOG_PANEL_PRESSED = "#07080e"
REND_DIALOG_SELECTION = "#12304a"
REND_DIALOG_FONT = "'Orbitron', 'Rajdhani', 'Segoe UI', 'Consolas', sans-serif"

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
    letter-spacing: 1px;
}}
QPushButton {{
    background-color: {REND_DIALOG_PANEL};
    color: {REND_DIALOG_ACCENT};
    border: 1px solid {REND_DIALOG_BORDER};
    border-left: 3px solid {REND_DIALOG_ACCENT};
    border-radius: 2px;
    padding: 6px 16px;
    letter-spacing: 1px;
}}
QPushButton:hover {{
    background-color: {REND_DIALOG_PANEL_HOVER};
    color: {REND_DIALOG_ACCENT_HOVER};
    border: 1px solid {REND_DIALOG_ACCENT};
    border-left: 3px solid {REND_DIALOG_ACCENT_ALT};
}}
QPushButton:pressed {{
    background-color: {REND_DIALOG_PANEL_PRESSED};
    color: {REND_DIALOG_ACCENT_ALT};
    border: 1px solid {REND_DIALOG_ACCENT_ALT};
    border-left: 3px solid {REND_DIALOG_ACCENT_ALT};
}}
QPushButton#primaryButton {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {REND_DIALOG_ACCENT}, stop:1 {REND_DIALOG_ACCENT_ALT});
    color: {REND_DIALOG_ACCENT_TEXT};
    border: 1px solid {REND_DIALOG_ACCENT};
    border-left: 3px solid {REND_DIALOG_ACCENT_ALT};
    font-weight: 700;
}}
QPushButton#primaryButton:hover {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {REND_DIALOG_ACCENT_HOVER}, stop:1 {REND_DIALOG_ACCENT_ALT_HOVER});
    color: {REND_DIALOG_ACCENT_TEXT};
    border: 1px solid {REND_DIALOG_ACCENT_HOVER};
}}
QPushButton#primaryButton:pressed {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {REND_DIALOG_ACCENT_PRESSED}, stop:1 {REND_DIALOG_ACCENT_ALT_PRESSED});
    color: {REND_DIALOG_ACCENT_TEXT};
    border: 1px solid {REND_DIALOG_ACCENT_PRESSED};
}}
QLineEdit, QComboBox {{
    background-color: {REND_DIALOG_PANEL};
    color: {REND_DIALOG_TEXT};
    border: 1px solid {REND_DIALOG_BORDER};
    border-bottom: 2px solid {REND_DIALOG_BORDER};
    border-radius: 2px;
    padding: 4px 8px;
}}
QLineEdit:hover, QComboBox:hover {{
    border: 1px solid {REND_DIALOG_ACCENT_PRESSED};
    border-bottom: 2px solid {REND_DIALOG_ACCENT_PRESSED};
}}
QLineEdit:focus, QComboBox:focus {{
    border: 1px solid {REND_DIALOG_ACCENT};
    border-bottom: 2px solid {REND_DIALOG_ACCENT_ALT};
    color: {REND_DIALOG_ACCENT_HOVER};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background-color: {REND_DIALOG_PANEL};
    color: {REND_DIALOG_TEXT};
    border: 1px solid {REND_DIALOG_ACCENT};
    selection-background-color: {REND_DIALOG_SELECTION};
    selection-color: {REND_DIALOG_ACCENT};
    outline: none;
}}
"""
# --- render_dialog Visual theme ---------------------------------