from PySide6.QtWidgets import QListWidget


class LayerListWidget(QListWidget):
    """Layer list (row 0 = top of the stack).

    [Changed] The ``keyPressEvent`` override (U / D / Shift+U / Shift+D / H / S /
    T) was a second copy of the main window's key handling and swallowed all
    other keys.  Every shortcut is now a ``QShortcut`` of the main window
    (``MainWinShortcutsMixin``); this class keeps the ``opengl_widget``
    reference the main window sets.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.opengl_widget = None
