from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QPushButton

from shell_jekyll import gb_var as gb_var_global


def flash_button(btn: QPushButton,
                 flash_text: str,
                 original_text: str,
                 msec: int = 2000
                 ) -> None:
    """Show ``flash_text`` in the success colour for ``msec`` ms, then restore the button.

    [Added] The same "turn green, disable, reset after 2 s" code was written
    three times (``_recover_btn`` in the main window, the TCL widget and the
    CEL widget) and called ``QTimer().singleShot`` on a throw-away instance
    instead of the static ``QTimer.singleShot``.
    """
    btn.setStyleSheet(f"color : {gb_var_global.style_script.MAIN_WIN_SUCCESS} ;")
    btn.setText(flash_text)
    btn.setEnabled(False)
    QTimer.singleShot(msec, lambda: _recover_btn(btn, original_text))


def _recover_btn(btn: QPushButton,
                 original_text: str
                 ) -> None:
    btn.setStyleSheet(f"color : {gb_var_global.style_script.MAIN_WIN_TEXT} ;")
    btn.setText(original_text)
    btn.setEnabled(True)
