from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut


class MainWinShortcutsMixin:
    """All keyboard shortcuts, registered as ``QShortcut`` objects.

    [Added] Replaces the two copies of the ``keyPressEvent`` if/elif chains
    (``MainUserUi.keyPressEvent`` and ``LayerListWidget.keyPressEvent``) with
    one table.  Keys and behaviour are the old ones::

        Right / Left            next / previous frame
        Shift+Right / Left      +10 / -10 frames
        0-9                     type an image number for the current frame
        Return                  apply the typed number (only active while typing)
        U / D                   select the layer above / below
        Shift+U / Shift+D       move the selected layer up / down the stack
        H                       toggle visibility of the selected layer
        Shift+H                 solo / inverse solo     Alt+H   show all
        S                       selected layer decides the displayed aspect ratio

    The shortcuts work while this widget or any child has focus
    (``WidgetWithChildrenShortcut``), like the old key events that bubbled
    up to the main widget.  Line edits keep priority for the keys they type
    (digits, letters, arrows), so typing in the FPS / frame fields still works.
    Fixed on the way: the old layer-list key handler swallowed every other key,
    so Left / Right (and Up / Down) did nothing while the list had focus; the
    stub ``T`` key (``print("Hello")``) was dropped.
    """

    def _add_shortcut(self, key: str, slot) -> QShortcut:
        shortcut = QShortcut(QKeySequence(key), self)
        shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        shortcut.activated.connect(slot)
        return shortcut

    def _init_shortcuts(self):
        self.shortcuts: dict[str, QShortcut] = {}
        bindings = {
            "Right": lambda: self.move_sequence(is_foward=True),
            "Left": lambda: self.move_sequence(is_foward=False),
            "Shift+Right": lambda: self.move_sequence(is_foward=True, is_increment=True, increment_step=10),
            "Shift+Left": lambda: self.move_sequence(is_foward=False, is_increment=True, increment_step=10),
            "U": lambda: self.select_layer_relative(-1),
            "D": lambda: self.select_layer_relative(+1),
            "Shift+U": lambda: self.move_selected_layer(-1),
            "Shift+D": lambda: self.move_selected_layer(+1),
            "H": lambda: self.toggle_selected_layer_visibility(mode=1),
            "Shift+H": lambda: self.toggle_selected_layer_visibility(mode=2),
            "Alt+H": lambda: self.toggle_selected_layer_visibility(mode=3),
            "S": self.set_size_standard_to_selected,
        }
        for digit in range(10):
            bindings[str(digit)] = lambda digit=digit: self.input_frame_digit(digit)
        for key, slot in bindings.items():
            self.shortcuts[key] = self._add_shortcut(key, slot)

        # Return must reach line edits (editingFinished) unless a frame number is being typed.
        self.shortcuts["Return"] = self._add_shortcut("Return", self.commit_frame_input)
        self.shortcuts["Return"].setEnabled(False)

    # ------------------------------------------------------- frame number input
    def _set_inputting(self, flag: bool):
        """Track "a frame number is being typed" and enable the Return shortcut only then."""
        self.inputting = flag
        shortcut = getattr(self, "shortcuts", {}).get("Return")
        if shortcut is not None:
            shortcut.setEnabled(flag)

    def input_frame_digit(self, digit: int):
        """Append ``digit`` to the image number being typed (shown in the left label)."""
        if not self.sj.has_sequence():
            return
        if not self.inputting:
            self._set_inputting(True)
            self.input_frame_num_str = ""
        self.input_frame_num_str += str(digit)
        self.current_actual_img_idx_label.setText(self.input_frame_num_str)

    def commit_frame_input(self):
        """Return: make the current timeline position show the typed image number."""
        if not self.inputting:
            return
        self._set_inputting(False)
        typed, self.input_frame_num_str = self.input_frame_num_str, ""
        self.sj.assign_frame(seq_idx=self.sj.seq_idx, img_idx=int(typed))

    # ---------------------------------------------------------------- layer keys
    def select_layer_relative(self, delta: int):
        row = self.layer_list.currentRow()
        if row < 0:
            return
        if 0 <= row + delta < self.layer_list.count():
            self.layer_list.setCurrentRow(row + delta)

    def move_selected_layer(self, direction: int):
        row = self.layer_list.currentRow()
        if row < 0:
            return
        self.sj.move_layer(row=row, direction=direction)

    def toggle_selected_layer_visibility(self, mode: int):
        row = self.layer_list.currentRow()
        if row < 0:
            return
        self.sj.toggle_layer_visibility(target_layer=row, mode=mode)

    def set_size_standard_to_selected(self):
        row = self.layer_list.currentRow()
        if row < 0:
            return
        self.sj.switch_size_standard(layer=row)
