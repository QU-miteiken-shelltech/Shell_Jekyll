from PySide6.QtCore import Qt, QEvent
from PySide6.QtWidgets import QWidget, QApplication

from shell_jekyll.api import ShellJekyll
from shell_jekyll.ui.sj_editor.main_win.main_win_ui import MainWinUIMixin
from shell_jekyll.ui.sj_editor.main_win.main_win_io import MainWinIOMixin
from shell_jekyll.ui.sj_editor.main_win.main_win_playback import MainWinPlaybackMixin
from shell_jekyll.ui.sj_editor.main_win.main_win_events import MainWinEventsMixin
from shell_jekyll.ui.sj_editor.main_win.main_win_shortcuts import MainWinShortcutsMixin


class MainUserUi(QWidget,
                 MainWinUIMixin,
                 MainWinIOMixin,
                 MainWinPlaybackMixin,
                 MainWinEventsMixin,
                 MainWinShortcutsMixin
                 ):
    """Main window.  All project logic is in ``self.sj`` (``shell_jekyll.api.ShellJekyll``).

    [Changed] ``keyPressEvent`` (about 140 lines of if/elif) is gone -- see
    ``MainWinShortcutsMixin``.  The frame counters (``seq_idx`` ...) moved to the
    controller.  Mouse-hover tracking of the reference view is extended with an
    event filter (see ``eventFilter``).
    """

    def __init__(self):
        """[Changed] Creates the controller, registers shortcuts and subscribes to controller events.
        The stray ``gb_var_full.frame_notation_len = 0`` (it put an int into a list field before
        anything was loaded) was removed."""
        super().__init__()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.sj = ShellJekyll()
        self.is_on_main_window = True
        self.inputting = False
        self.input_frame_num_str = ""

        self._init_ui()
        self._init_shortcuts()
        self._bind_controller()

    def _set_pointer_target(self, on_ref: bool):
        """Arrow keys act on the reference view while the pointer is over it (label turns green)."""
        self.is_on_main_window = not on_ref
        self.ref_seq_idx_label.setStyleSheet("color : green ;" if on_ref else "color : white ;")

    def _is_over_ref(self, widget) -> bool:
        return widget is not None and (
            widget is self.ref_gl_widget or self.ref_gl_widget.isAncestorOf(widget)
        )

    def mouseMoveEvent(self, event):
        """[Changed] The reference view's own child widgets (the index label) count as "over the reference view"."""
        widget_on = QApplication.widgetAt(event.globalPosition().toPoint())
        self._set_pointer_target(self._is_over_ref(widget_on))

    def eventFilter(self, obj, event):
        """[Added] Hover tracking through Enter / Leave of the reference view.

        ``mouseMoveEvent`` above is only delivered while the pointer is over
        the bare parent area (child widgets have no mouse tracking), so the
        switch to "reference mode" could not happen when the pointer simply
        moved onto the reference view.
        """
        if obj is self.ref_gl_widget:
            if event.type() == QEvent.Type.Enter:
                self._set_pointer_target(True)
            elif event.type() == QEvent.Type.Leave:
                self._set_pointer_target(False)
        return super().eventFilter(obj, event)
