import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtGui import QIcon

from shell_jekyll.api import configure_surface_format
from shell_jekyll.ui.sj_editor.main_win.main_win import MainUserUi
from shell_jekyll.ui.launcher import LauncherUi
from shell_jekyll import gb_var as gb_var_global

def main():
    configure_surface_format()

    app = QApplication(sys.argv)
    app.setApplicationDisplayName("Shell Jekyll")
    app.setApplicationName("Shell_Jekyll")
    app.setWindowIcon(QIcon(str(Path(__file__).resolve().parent / "_resources/icon.jpg")))

    use_style = sys.argv[1] if len(sys.argv) > 1 else "dark_default"
    gb_var_global.style_script = gb_var_global.styles.get(use_style, gb_var_global.styles["dark_default"])

    window = QMainWindow()
    window.setWindowTitle("Shell Jekyll")
    window.resize(860, 600)
    
    main_ui = LauncherUi()
    window.setCentralWidget(main_ui)

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
