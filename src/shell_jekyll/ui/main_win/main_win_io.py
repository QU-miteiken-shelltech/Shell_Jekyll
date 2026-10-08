from PySide6.QtWidgets import QFileDialog


class MainWinIOMixin:
    """File dialogs only; opening / saving is done by ``ShellJekyll`` (``self.sj``)."""

    def _show_expression_panel(self):
        """Reveal the expression panel and fill the proc list.  [Changed] The proc list comes from ``ShellJekyll.get_tcl_procs`` (which no longer lets a missing Tk / broken script abort loading)."""
        self.expression_widgets.show()
        self.expression_lang_combo.show()
        self.tcl_widget.command_func_combo.clear()
        self.tcl_widget.command_func_combo.addItems(self.sj.get_tcl_procs())

    def read_proj(self):
        """[Changed] Dialog only; loading is ``ShellJekyll.read_proj`` and the widgets follow its events (see ``MainWinEventsMixin``)."""
        filename, _ = QFileDialog.getOpenFileName(self, "Open Sequence", "", "Shell Jekyll proj. (*.sjproj)")
        if not filename:
            return
        self._set_inputting(False)
        self.sj.read_proj(filename)

    def save_proj(self):
        """Save the project; ask for a file only if it has none yet.

        [Changed] The "ask for a file" case used ``getOpenFileName``, which can
        only pick an EXISTING file, so a new project could never be saved.
        It is ``getSaveFileName`` now.  Saving with nothing loaded does nothing
        (the old code raised ``KeyError``).
        """
        if not self.sj.has_sequence():
            return
        filename = None
        if self.sj.saving_path is None:
            filename, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "Shell Jekyll proj. (*.sjproj)")
            if not filename:
                return
        self.sj.save_proj(filename)

    def open_sequence(self):
        """[Changed] Dialog only; the work is ``ShellJekyll.open_sequence`` (see its docstring for the fixes)."""
        filename, _ = QFileDialog.getOpenFileName(self, "Open Sequence", "", "PNG (*.png)")

        if not filename:
            return
        self._set_inputting(False)
        self.sj.open_sequence(filename)

    def open_reference(self):
        """[Changed] Dialog only; the work is ``ShellJekyll.open_reference``."""
        filename, _ = QFileDialog.getOpenFileName(self, "Open Sequence", "", "Video (*.mp4)")
        if not filename:
            return
        self.sj.open_reference(filename)
