from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMenu


class MainWinEventsMixin:
    """Widget <-> controller glue.  The logic itself lives in ``shell_jekyll.api.ShellJekyll``."""

    def _bind_controller(self):
        """Subscribe to controller events so the labels / layer list follow the state.

        [Added] The controller (``self.sj``) knows nothing about widgets; it
        emits events and these handlers update the labels, exactly the ones the
        old handlers updated inline (``move_sequence``, ``open_sequence``, ...).
        """
        self.sj.on("frame_changed", self._on_frame_changed)
        self.sj.on("ref_frame_changed", self._on_ref_frame_changed)
        self.sj.on("sequence_opened", self._on_sequence_opened)
        self.sj.on("project_loaded", self._on_project_loaded)
        self.sj.on("project_saved", self._on_project_saved)
        self.sj.on("ref_fps_changed", self._on_ref_fps_changed)
        self.sj.on("active_layer_changed", self._on_active_layer_changed)
        self.sj.on("layer_moved", self._on_layer_moved)

    # ------------------------------------------------------- controller events
    def _on_frame_changed(self, seq_idx, actual_img_idx, paths):
        self.current_frame_label.setText(str(seq_idx))
        self.current_actual_img_idx_label.setText(str(actual_img_idx))

    def _on_ref_frame_changed(self, ref_seq_idx, path):
        self.ref_seq_idx_label.setText(str(ref_seq_idx))

    def _on_sequence_opened(self, layer, working_sequence):
        self.current_opened_label.setText(working_sequence)
        self.layer_list.addItem(str(self.layer_list.count()))
        appended_item = self.layer_list.item(self.layer_list.count() - 1)
        appended_item.setFlags(appended_item.flags() | Qt.ItemIsEditable)
        # [Changed] Highlight the new layer: it IS the active layer now, but the
        # old code left the selection on the previous row (or on nothing).
        self.layer_list.setCurrentRow(layer)

    def _on_project_loaded(self, working_sequence, layer_labels, ref_fps):
        self.current_opened_label.setText(working_sequence)
        self._show_expression_panel()
        # [Changed] Signals are blocked while the list is rebuilt: clear()
        # emitted currentItemChanged with row -1, which switched the active
        # layer to the LAST layer before the project was fully loaded.
        self.layer_list.blockSignals(True)
        self.layer_list.clear()
        self.layer_list.addItems(layer_labels)
        for i in range(0, self.layer_list.count()):
            item = self.layer_list.item(i)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.layer_list.blockSignals(False)
        self.layer_list.setCurrentRow(0)

    def _on_project_saved(self, path):
        self._show_expression_panel()

    def _on_ref_fps_changed(self, fps):
        self.fps_input_field.setText(str(fps))

    def _on_active_layer_changed(self, layer, actual_img_idx, working_sequence):
        self.current_actual_img_idx_label.setText(str(actual_img_idx))
        self.current_opened_label.setText(working_sequence)

    def _on_layer_moved(self, from_row, to_row):
        """Move the list item (keeping its possibly user-edited text) the same way the stack moved."""
        self.layer_list.blockSignals(True)
        item = self.layer_list.takeItem(from_row)
        self.layer_list.insertItem(to_row, item)
        self.layer_list.setCurrentRow(to_row)
        self.layer_list.blockSignals(False)

    # ---------------------------------------------------------------- UI slots
    def move_sequence(self,
                      is_foward: bool=True,
                      is_increment: bool=True,
                      increment_step: int=1
                      ):
        """Step the timeline, or the reference view while the pointer is over it.

        [Changed] Only reads the frame field and delegates to
        ``ShellJekyll.move_sequence``.  The old body also did
        ``time_map[active][actual_img_idx]`` into an unused variable, which
        raised ``KeyError`` whenever the actual number was not a key of the
        time map (e.g. ``-1`` before the first mapped frame); removed.
        An empty / invalid frame field is ignored instead of raising.
        """
        self._set_inputting(False)
        seq_idx = None
        if not is_increment:
            try:
                seq_idx = int(self.current_frame_label.text())
            except ValueError:
                return
        self.sj.move_sequence(
            is_foward=is_foward,
            is_increment=is_increment,
            increment_step=increment_step,
            on_ref=not self.is_on_main_window,
            seq_idx=seq_idx
        )

    def ref_ctx_menu(self, pos):
        menu = QMenu(self.ref_video_widget)
        action_01 = menu.addAction("Mark as Start")
        action_01.triggered.connect(
            lambda: self.sj.mark_ref_start(int(self.ref_player.position()))
        )
        action_02 = menu.addAction("Reset Starting Point")
        action_02.triggered.connect(
            lambda: self.sj.mark_ref_start(0)
        )

        menu.exec(self.ref_video_widget.mapToGlobal(pos))

    def switch_active_layer(self, *_):
        """Layer list selection changed -> make that row the working layer."""
        self.sj.switch_active_layer(self.layer_list.currentRow())
