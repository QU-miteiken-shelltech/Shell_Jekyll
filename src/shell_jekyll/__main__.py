import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtGui import QIcon

from shell_jekyll.api import configure_surface_format
from shell_jekyll.ui.main_win.main_win import MainUserUi
from shell_jekyll import gb_var as gb_var_global

def main():
    """Start the GUI.  Optional first argument: style name (``gb_var.styles``).

    [Changed]
    * An unknown style name stored the STRING ``"dark_default"`` in
      ``style_script`` (the ``dict.get`` default was a str, not the module), which
      crashed with ``AttributeError`` when the first stylesheet constant was read.
    * The window icon pointed at ``_resources/icon`` (no extension, file does not
      exist); it is ``icon.jpg``.
    * Removed the duplicate import alias and the unused ``QSurfaceFormat`` code
      (now ``api.configure_surface_format``, shared with the scripting API).
    """
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

    main_ui = MainUserUi()
    window.setCentralWidget(main_ui)

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
