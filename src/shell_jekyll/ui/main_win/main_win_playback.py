from PySide6.QtMultimedia import QMediaPlayer, QVideoFrame
from PySide6.QtWidgets import QDialog
import psutil

from shell_jekyll.ui.render_dialog import RenderDialog
from shell_jekyll.ui.ui_utils import flash_button

class MainWinPlaybackMixin:

    def _update_mem_label(self):
        mem = round(psutil.virtual_memory().percent)
        self.release_buff_btn.setText(f"Release Buff. ({mem}%)")

    def play_sequence(self):
        """Pre-load all frames into GPU buffers (first time only), then play the reference video.

        [Changed] Playback works again: the video frame callback
        (``ref_video_proceed``) now drives the preview through the frames held
        in the VBO store.  See ``ShellJekyll.play_sequence``.
        """
        self.sj.preload_frames()
        self._update_mem_label()
        self.play_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.sj.play_sequence()
        self.back_to_start_btn.setEnabled(False)

    def pause_sequence(self, *_):
        """Pause the reference video.  [Changed] ``*_`` replaces the unused ``arrived_idx`` parameter that only swallowed the ``clicked(bool)`` argument."""
        self.sj.pause_sequence()
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.back_to_start_btn.setEnabled(True)

    def back_to_start(self):
        self.sj.back_to_start()

    def release_buffer(self):
        """Free the pre-loaded frames.  [Changed] Delegates to ``ShellJekyll.release_buffer`` (``is_preloaded`` replaces the ``ram_img_buffer`` check)."""
        if self.gl_widget.is_preloaded:
            self.sj.release_buffer()
            self._update_mem_label()

    def on_finished(self):
        """The video ended.  [Changed] Also re-enables "Back" (``play_sequence`` disables it and only Pause re-enabled it)."""
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.back_to_start_btn.setEnabled(True)

    def on_media_status_changed(self, status):
        """[Added] ``on_finished`` existed but was never connected; call it when the video ends."""
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.on_finished()

    def ref_video_proceed(self, frame: QVideoFrame):
        """A reference-video frame was shown: show the matching timeline frame."""
        if not frame.isValid():
            return
        self.sj.ref_video_proceed(frame.startTime())

    def render_sequence(self):
        """Open the render dialog.

        [Changed] ``int(self.fps_input_field.text())`` raised ``ValueError`` for
        any fractional frame rate such as ``29.97`` (the field is a
        ``QDoubleValidator`` and is filled from the video's fps); ``float`` now.
        """
        try:
            fps = float(self.fps_input_field.text())
        except ValueError:
            return
        render_dialog_call = RenderDialog(fps=fps, controller=self.sj).exec()
        if render_dialog_call == QDialog.Accepted:
            flash_button(self.render_btn, flash_text="Rendered", original_text="Render")

    def switch_expression_lang(self):
        lang = self.expression_lang_combo.currentText()
        if lang == "TCL":
            self.expression_widgets.setCurrentIndex(0)
        elif lang == "CEL":
            self.expression_widgets.setCurrentIndex(1)
        else:
            self.expression_widgets.setCurrentIndex(0)
