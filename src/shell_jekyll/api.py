"""UI-free access to every Shell Jekyll operation.

[Added] Every action that used to exist only inside a button / key handler
(open a sequence, move through frames, edit the time map, re-stack layers,
run an expression, play the preview, save, render, ...) is a plain method of
``ShellJekyll``.  The main window is now a thin shell that asks the user
(file dialogs, key presses) and calls these methods; the data flow is the
same as before::

    seq_idx --time_map--> actual image number --file name template--> path per layer
            --> OpenGL widget (preview)

Nothing in here imports Qt at module level, so the project logic can be
scripted without a window::

    from shell_jekyll.api import ShellJekyll

    sj = ShellJekyll()
    sj.open_sequence("/shots/bg/bg_0001.png")       # layer 0
    sj.open_sequence("/shots/fg/fg_0001.png")       # layer 1
    sj.run_cel_expression("(frame - 1) % seq_count + 1", 1, 48)
    sj.assign_frame(seq_idx=10, img_idx=3)           # what typing "3" + Return does
    sj.move_layer(row=1, direction=-1)               # Shift+U
    sj.toggle_layer_visibility(target_layer=0)       # H
    sj.save_proj("/shots/test.sjproj")
    sj.render_video("/shots", "out", export_range=(1, 48))

    # real-time preview without the main window (needs PySide6 / OpenGL):
    preview = sj.create_preview()
    sj.show_frame(5)
    sj.preload_frames()                              # frames -> GPU buffers
    sj.ref_video_proceed(time_us=500_000)            # what one video frame does
    sj.grab_preview().save("/tmp/frame.png")

State (``gb_var`` / ``TimeMap``) is process-wide, as before: there is one
project per process, shared by every ``ShellJekyll`` object.

Events: ``sj.on(event, callback)``; callbacks receive keyword arguments.
    frame_changed(seq_idx, actual_img_idx, paths)
    ref_frame_changed(ref_seq_idx, path)
    sequence_opened(layer, working_sequence)
    project_loaded(working_sequence, layer_labels, ref_fps)
    project_saved(path)
    ref_fps_changed(fps)
    active_layer_changed(layer, actual_img_idx, working_sequence)
    layer_moved(from_row, to_row)
"""
import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable

import cv2

from shell_jekyll import gb_var as gb_var_script
from shell_jekyll.gb_var import TimeMap as time_map, MAX_LAYER
from shell_jekyll.io.io_sjproj import IO_sjproj
from shell_jekyll.render import render_formats
from shell_jekyll.render.render import RenderVideo
from shell_jekyll.utils.editing_utils import EditingUtils, FALLBACK_IMAGE
from shell_jekyll.utils.layer_view import LayerViewState

logger = logging.getLogger("shell_jekyll.api")

gb_var = gb_var_script.get_gbvar_ctx()
gb_var_full = gb_var_script.get_gbvar_full()


def configure_surface_format() -> None:
    """Request the OpenGL 3.3 core profile (needed by the shaders).  Call before creating QApplication."""
    from PySide6.QtGui import QSurfaceFormat
    fmt = QSurfaceFormat()
    fmt.setVersion(3, 3)
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    QSurfaceFormat.setDefaultFormat(fmt)


def ensure_qapplication():
    """Return the running ``QApplication``, creating one (with the GL format) if there is none."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        configure_surface_format()
        app = QApplication([])
    return app


class ShellJekyll:
    def __init__(self) -> None:
        self.seq_idx: int = 0
        self.ref_seq_idx: int = 0
        self.ref_fps: float = 0.0
        self.ref_frame_offset: int = 0
        self.view_state = LayerViewState()
        self.preview = None          # OpenGLImageWidget (main, multi-layer view)
        self.ref_preview = None      # OpenGLImageSingleWidget (reference frame view)
        self.ref_player = None       # QMediaPlayer (reference video)
        self._listeners: dict[str, list[Callable]] = defaultdict(list)
        # Reference video chosen before any sequence exists (GBVar is not configured yet).
        self._pending_ref_path: Path | None = None
        self._pending_ref_start: int = 0

    # ------------------------------------------------------------------ events
    def on(self, event: str, callback: Callable) -> Callable:
        """Register ``callback(**info)`` for ``event`` (see module docstring)."""
        self._listeners[event].append(callback)
        return callback

    def off(self, event: str, callback: Callable) -> None:
        if callback in self._listeners[event]:
            self._listeners[event].remove(callback)

    def _emit(self, event: str, **info: Any) -> None:
        for callback in list(self._listeners[event]):
            callback(**info)

    # ------------------------------------------------------------------- state
    def has_sequence(self) -> bool:
        return EditingUtils.has_sequence()

    def layer_count(self) -> int:
        return EditingUtils.layer_count()

    @property
    def active_layer(self) -> int:
        return gb_var.active_layer if gb_var_script.is_configured() else 0

    @property
    def saving_path(self) -> Path | None:
        """Path of the project file (None until the project was opened / saved)."""
        return gb_var.saving_path if gb_var_script.is_configured() else None

    @property
    def ref_video_start(self) -> int:
        """Start position (ms) of the reference video, set by "Mark as Start"."""
        return gb_var.ref_video_start if gb_var_script.is_configured() else self._pending_ref_start

    def working_sequence(self) -> str:
        """Text of the "Working Sequence" label for the active layer."""
        return f"Working Sequence : {gb_var.sequence_root_dir / gb_var.mata_filename}"

    # ------------------------------------------------------------------ attach
    def attach_preview(self, widget) -> None:
        """Use ``widget`` (an ``OpenGLImageWidget``) as the preview and share the layer view settings with it."""
        self.preview = widget
        widget.view_state = self.view_state

    def attach_ref_preview(self, widget) -> None:
        self.ref_preview = widget

    def attach_ref_player(self, player) -> None:
        """Use ``player`` (a ``QMediaPlayer``) for the reference video."""
        self.ref_player = player

    def create_preview(self, parent=None, width: int = 640, height: int = 360):
        """Create a stand-alone preview widget (no main window) and attach it."""
        ensure_qapplication()
        from shell_jekyll.ui.sj_editor.opengl import OpenGLImageWidget
        widget = OpenGLImageWidget(str(FALLBACK_IMAGE), parent)
        widget.resize(width, height)
        self.attach_preview(widget)
        return widget

    def grab_preview(self):
        """Render the preview and return it as a ``QImage`` (works without showing a window)."""
        from PySide6.QtWidgets import QApplication
        if self.preview is None:
            raise RuntimeError("No preview attached: call create_preview() or attach_preview() first")
        self.preview.show()
        QApplication.processEvents()
        return self.preview.grabFramebuffer()

    def _refresh_preview(self) -> None:
        if self.preview is not None:
            self.preview.update()

    # ---------------------------------------------------------- project / files
    def open_sequence(self, filename: str | Path) -> int | None:
        """Add the PNG sequence containing ``filename`` as a new layer.  Returns the layer index, or None.

        Logic of the former ``MainWinIOMixin.open_sequence`` minus the file dialog.

        [Changed]
        * The new layer's ``base_frame_list`` used to be overwritten with a stale
          empty list for the first layer (``switch_layer`` wrote the old working
          copy back over it), which made ``seq_count`` 0 and every expression
          result be rejected until the project was saved and re-opened.  The
          write-back is now skipped when there is no previous layer.
        * A 9th layer (more than ``MAX_LAYER``) is refused; before it broke the
          fixed-size ``layer_order`` / shader arrays.
        * A reference video chosen before the first sequence is kept
          (``initialize`` used to reset it).
        """
        path = Path(filename)
        matches = re.findall(r'\d+', path.name)
        if len(matches) != 1:
            logger.warning("file name must contain exactly one number: %s", path.name)
            return None
        if self.layer_count() >= MAX_LAYER:
            logger.warning("cannot add more than %d layers", MAX_LAYER)
            return None

        sequence_root_dir = path.resolve().parent
        first_sequence_idx = int(matches[0])
        frame_notation_len = len(matches[0])
        sharps = '#' * frame_notation_len
        mata_filename = re.sub(r'\d+', sharps, path.name)

        if gb_var_script.is_configured():
            info = {
                "sequence_root_dir" : sequence_root_dir,
                "mata_filename" : mata_filename,
                "first_sequence_idx" : first_sequence_idx,
                "frame_notation_len" : frame_notation_len
            }
            gb_var_full.append_info(new_info=info)
        else:
            time_map.time_map = []
            data = {
                "base_frame_list" : [[]],
                "sequence_root_dir" : [sequence_root_dir],
                "mata_filename" : [mata_filename],
                "first_sequence_idx" : [first_sequence_idx],
                "frame_notation_len" : [frame_notation_len],
                "ref_video_start" : self._pending_ref_start,
                "ref_path" : self._pending_ref_path,
                "saving_path" : None,
                "layer_order" : [i for i in range(0, MAX_LAYER)]
            }
            gb_var_full.initialize(init_data=data)

        parts = [re.escape(p) for p in mata_filename.split(sharps)]
        regex_pattern = "^" + r"(\d+)".join(parts) + "$"
        numbers = [
            m.group(1)
            for item in sequence_root_dir.iterdir()
            if item.is_file() and (m := re.match(regex_pattern, item.name))
        ]
        layer = len(gb_var_full.first_sequence_idx) - 1
        time_map.time_map.append({})
        for num in numbers:
            num = int(num)
            time_map.time_map[layer][num] = num

        base_frame_list = EditingUtils.get_base_frames(layer=layer)
        if len(gb_var_full.base_frame_list) >= layer + 1:
            gb_var_full.base_frame_list[layer] = base_frame_list
        else:
            gb_var_full.base_frame_list.append(base_frame_list)

        gb_var.switch_layer(new_active_layer=layer, do_write_back=layer > 0)

        self.show_frame(first_sequence_idx)
        if self.ref_preview is not None:
            self.ref_preview.change_image(new_image_path=str(filename))
        self._emit("sequence_opened", layer=layer,
                   working_sequence=f"Working Sequence : {sequence_root_dir / mata_filename}")
        return layer

    def open_reference(self, filename: str | Path) -> float:
        """Set the reference video.  Returns its frame rate (0.0 when it cannot be read).

        [Changed] The path is now kept in a place that is saved with the
        project (it only reached ``GBVar_CTX`` before and never ``GBVar``).
        """
        filename = Path(filename)
        if gb_var_script.is_configured():
            gb_var.ref_path = filename
        else:
            self._pending_ref_path = filename
        return self._set_ref_video(filename)

    def _set_ref_video(self, path: Path | None) -> float:
        """Load ``path`` into the player and read its fps with OpenCV (as before)."""
        fps = 0.0
        if path is not None:
            if self.ref_player is not None:
                from PySide6.QtCore import QUrl
                self.ref_player.setSource(QUrl.fromLocalFile(str(path)))
            cv2_videocap = cv2.VideoCapture(str(path))
            fps = cv2_videocap.get(cv2.CAP_PROP_FPS) if cv2_videocap.isOpened() else 0.0
            cv2_videocap.release()
        self.ref_fps = fps
        self._emit("ref_fps_changed", fps=fps)
        return fps

    def mark_ref_start(self, position_ms: int = 0) -> None:
        """Remember ``position_ms`` as the start of the reference video ("Mark as Start" / "Reset Starting Point")."""
        if gb_var_script.is_configured():
            gb_var.ref_video_start = int(position_ms)
        else:
            self._pending_ref_start = int(position_ms)

    def read_proj(self, filename: str | Path) -> bool:
        """Load a .sjproj project.  Returns False when it holds no sequence.

        Logic of the former ``MainWinIOMixin.read_proj`` minus dialog / widgets.
        [Changed] A project without a reference video no longer tries to open
        the path ``"None"`` in the player.
        """
        IO_sjproj.load_sjproj(reading_path=str(filename))
        self.seq_idx = 1
        if not self.has_sequence():
            return False
        self.show_frame(self.seq_idx)
        if self.ref_preview is not None:
            self.ref_preview.change_image(
                new_image_path=EditingUtils.get_layer_image_path(
                    img_idx=EditingUtils.get_actual_img_idx(seq_idx=self.seq_idx, layer=0), layer=0))
        self._set_ref_video(gb_var.ref_path)
        self._emit("project_loaded",
                   working_sequence=self.working_sequence(),
                   layer_labels=[str(i) for i in gb_var_full.layer_order[0 : self.layer_count()]],
                   ref_fps=self.ref_fps)
        return True

    def save_proj(self, filename: str | Path | None = None) -> Path | None:
        """Save the project (to ``filename``, else to the path it was opened from / saved to).

        Returns the written path, or None when nothing is loaded.  Raises
        ``ValueError`` when no path is known.  [Changed] ``ref_path`` is saved
        as ``null`` when there is none (it used to be the string ``"None"``).
        """
        if not self.has_sequence():
            return None
        if filename is None:
            filename = gb_var.saving_path
        if filename is None:
            raise ValueError("No saving path: pass a file name")
        gb_var.write_to_main(active_layer=gb_var.active_layer)
        ref_path = gb_var_full.ref_path
        writing_info = {
            "base_frame_list" : [EditingUtils.get_base_frames(layer=l) for l in range(0, self.layer_count())],
            "time_map" : time_map.time_map,
            "sequence_root_dir" : [str(x) for x in gb_var_full.sequence_root_dir],
            "mata_filename" : gb_var_full.mata_filename,
            "first_sequence_idx" : gb_var_full.first_sequence_idx,
            "frame_notation_len" : gb_var_full.frame_notation_len,
            "ref_video_start": gb_var_full.ref_video_start,
            "ref_path" : str(ref_path) if ref_path else None,
            "layer_order" : [int(i) for i in gb_var_full.layer_order]
        }
        saved = IO_sjproj.write_sjproj(saving_path=filename, writing_info=writing_info)
        self._emit("project_saved", path=saved)
        return saved

    # -------------------------------------------------------------- navigation
    def show_frame(self, seq_idx: int) -> list[str]:
        """Go to timeline position ``seq_idx``: update the preview and emit ``frame_changed``.  Returns the layer paths."""
        self.seq_idx = int(seq_idx)
        paths = EditingUtils.resolve_image_paths(self.seq_idx)
        actual_img_idx = EditingUtils.get_actual_img_idx(seq_idx=self.seq_idx, layer=self.active_layer)
        if self.preview is not None:
            self.preview.change_image(new_image_paths=paths)
        self._emit("frame_changed", seq_idx=self.seq_idx, actual_img_idx=actual_img_idx, paths=paths)
        return paths

    def refresh_frame(self) -> None:
        """Re-resolve and redraw the current frame (after layers / time map changed)."""
        if self.has_sequence():
            self.show_frame(self.seq_idx)

    def show_ref_frame(self, ref_seq_idx: int) -> Path:
        """Show raw file number ``ref_seq_idx`` of the active layer in the reference view."""
        self.ref_seq_idx = int(ref_seq_idx)
        path = EditingUtils.get_layer_image_path(img_idx=self.ref_seq_idx, layer=self.active_layer)
        if self.ref_preview is not None:
            self.ref_preview.change_image(new_image_path=path)
        self._emit("ref_frame_changed", ref_seq_idx=self.ref_seq_idx, path=path)
        return path

    def move_sequence(self,
                      is_foward: bool=True,
                      is_increment: bool=True,
                      increment_step: int=1,
                      on_ref: bool=False,
                      seq_idx: int | None=None
                      ) -> None:
        """Step the timeline (``on_ref=False``) or the reference frame (``on_ref=True``).

        With ``is_increment=False`` the timeline jumps to ``seq_idx`` (the
        frame field).  Same rules as the former ``move_sequence`` handler.
        """
        if not self.has_sequence():
            return
        delta = increment_step if is_foward else -increment_step
        if not on_ref:
            if is_increment:
                self.show_frame(self.seq_idx + delta)
            else:
                self.show_frame(self.seq_idx if seq_idx is None else seq_idx)
        else:
            if is_increment:
                self.show_ref_frame(self.ref_seq_idx + delta)
            else:
                self.show_ref_frame(self.ref_seq_idx)

    def assign_frame(self, seq_idx: int, img_idx: int, layer: int | None = None) -> None:
        """Make timeline position ``seq_idx`` show image number ``img_idx`` (digits + Return in the UI).

        Edits the time map of ``layer`` (default: the active layer).  The preview is
        refreshed when ``seq_idx`` is the current position.
        """
        layer = self.active_layer if layer is None else layer
        time_map.time_map[layer][int(seq_idx)] = int(img_idx)
        if int(seq_idx) == self.seq_idx:
            self.refresh_frame()

    # ------------------------------------------------------------------ layers
    def switch_active_layer(self, row: int) -> None:
        """Make layer ``row`` the working layer and emit ``active_layer_changed``.

        [Changed] The "actual image number" shown is now simply the one the
        time map gives for the current position.  The old handler looked that
        number up in the time map a second time
        (``time_map[layer][actual_img_idx]``), which is a different number as
        soon as the map is edited and raised ``KeyError`` when it is not a
        key.  Rows < 0 (the list is being cleared) are ignored; before they
        silently selected the *last* layer through Python's negative index.
        """
        if not self.has_sequence() or not 0 <= row < self.layer_count():
            return
        if row != gb_var.active_layer:
            gb_var.switch_layer(new_active_layer=row)
        self._emit("active_layer_changed", layer=row,
                   actual_img_idx=EditingUtils.get_actual_img_idx(seq_idx=self.seq_idx, layer=row),
                   working_sequence=self.working_sequence())

    def move_layer(self, row: int, direction: int) -> bool:
        """Move layer ``row`` one step up (``direction=-1``) or down (``+1``) in the stack (Shift+U / Shift+D)."""
        if not self.has_sequence():
            return False
        target = row + direction
        if not 0 <= row < self.layer_count() or not 0 <= target < self.layer_count():
            return False
        layer_order = gb_var_full.layer_order.copy()
        layer_order.insert(target, layer_order.pop(row))
        gb_var_full.restack_layers(new_layer_order=layer_order, new_active_layer=target)
        self._emit("layer_moved", from_row=row, to_row=target)
        self.refresh_frame()
        return True

    def toggle_layer_visibility(self, target_layer: int | None = None, mode: int = 1) -> None:
        """Layer visibility.  mode 1: toggle, 2: solo / inverse solo, 3: show all.  Default layer: the active one."""
        self.view_state.toggle_layer_visibility(self.active_layer if target_layer is None else target_layer, mode)
        self._refresh_preview()

    def switch_size_standard(self, layer: int | None = None) -> None:
        """Let ``layer`` (default: the active one) decide the displayed aspect ratio."""
        self.view_state.switch_size_standard(self.active_layer if layer is None else layer)
        self._refresh_preview()

    # ---------------------------------------------------------------- playback
    def preload_frames(self, progress: Callable[[int, int], None] | None = None) -> int:
        """Load every frame of the project into GPU buffers (needed once before real-time playback)."""
        if self.preview is None:
            raise RuntimeError("No preview attached")
        if self.preview.is_preloaded:
            return 0
        return self.preview.preload_frames(EditingUtils.used_image_paths(), progress)

    def release_buffer(self) -> None:
        """Free the pre-loaded frames."""
        if self.preview is not None:
            self.preview.release_buffer()

    def play_sequence(self) -> bool:
        """Pre-load the frames and start the reference video (the video drives the preview).

        [Changed] Playback now works: the pre-load (``send_img_to_buffer``) and
        the per-frame lookup (``change_image_onram``) were both broken -- see
        ``OpenGLImageWidget``.  Returns False when no reference player is attached.
        """
        if self.preview is not None and not self.preview.is_preloaded:
            self.preload_frames()
        if self.ref_player is None:
            return False
        if self.ref_player.position() == 0:
            self.ref_player.setPosition(self.ref_video_start)
            self.ref_frame_offset = int((self.ref_video_start / 1000.0) * self.ref_fps)
        self.ref_player.play()
        return True

    def pause_sequence(self) -> None:
        if self.ref_player is not None:
            self.ref_player.pause()

    def back_to_start(self) -> None:
        if self.ref_player is not None:
            self.ref_player.setPosition(0)

    def ref_video_proceed(self, time_us: int) -> None:
        """React to a reference-video frame shown at ``time_us`` microseconds: show the matching timeline frame.

        [Changed] Receives the frame time instead of a ``QVideoFrame`` so it can
        be driven from scripts too.  Uses each layer's own folder (see
        ``EditingUtils.resolve_image_paths``) and reports the *active* layer's
        number (the old loop left the last layer's number in the label).
        """
        if not self.has_sequence() or time_us < 0 or self.ref_fps <= 0:
            return
        current_frame = int(round((time_us / 1000000.0) * self.ref_fps))
        self.show_frame(current_frame - self.ref_frame_offset)

    # -------------------------------------------------------------- expression
    def get_expression(self) -> str | None:
        """TCL script stored in the project (None if none / not saved yet)."""
        saving_path = self.saving_path
        if saving_path is None:
            return None
        return IO_sjproj.read_sjproj(reading_path=str(saving_path), reading_attr="expression")

    def save_expression(self, expression: str) -> bool:
        """Store the TCL script in the project file.  False if the project has not been saved yet."""
        saving_path = self.saving_path
        if saving_path is None:
            return False
        IO_sjproj.write_sjproj(saving_path=str(saving_path), writing_info={"expression" : expression})
        return True

    def get_tcl_procs(self) -> list[str]:
        """Names of the procs defined by the stored TCL script ([] if none, or TCL is unavailable / broken)."""
        try:
            from shell_jekyll.expression.tcl_engine import TCLEngine
            return TCLEngine().get_procs()
        except Exception as e:
            logger.warning("cannot list TCL procs: %s", e)
            return []

    def run_tcl_expression(self, func_name: str, from_frame: int, to_frame: int) -> int:
        """Run TCL proc ``func_name`` for frames ``from_frame..to_frame`` and write the results into the time map.

        [Changed] The old widget built the argument dict BEFORE the loop
        using the loop variable ``frame`` (``UnboundLocalError``: running a
        TCL expression never worked), and created a new engine (re-reading
        the project file) for every frame.
        """
        from shell_jekyll.expression.tcl_engine import TCLEngine
        engine = TCLEngine()
        return self._apply_expression(lambda data: engine.run_tcl(func_name=func_name, **data), from_frame, to_frame)

    def run_cel_expression(self, expression: str, from_frame: int, to_frame: int) -> int:
        """Evaluate CEL ``expression`` for frames ``from_frame..to_frame`` and write the results into the time map."""
        from shell_jekyll.expression.cel_engine import CELEngine
        engine = CELEngine(cel_expression=expression.strip())
        return self._apply_expression(lambda data: engine.run_cel(data=data), from_frame, to_frame)

    def _apply_expression(self, evaluate: Callable[[dict], Any], from_frame: int, to_frame: int) -> int:
        """Shared loop of the TCL / CEL widgets.  Returns how many frames were changed.

        A result is applied only if it is a frame that exists on disk
        (``base_frame_list``); anything else (including a non-number) is skipped,
        as before -- only the non-number case used to raise.  The time map is
        saved to the project afterwards when the project has a path.
        """
        layer = gb_var.active_layer
        base_frames = set(gb_var.base_frame_list)
        loop_count = to_frame - from_frame + 1
        changed = 0
        for frame in range(from_frame, to_frame + 1):
            data = {
                "frame" : frame,
                "seq_count" : len(gb_var.base_frame_list),
                "loop_count" : loop_count,
                "cframe" : int(time_map.time_map[layer].get(frame, frame))
            }
            try:
                result = int(evaluate(data))
            except (TypeError, ValueError):
                continue
            if result in base_frames:
                time_map.time_map[layer][frame] = result
                changed += 1
        if gb_var.saving_path is not None:
            IO_sjproj.write_sjproj(
                saving_path=gb_var.saving_path,
                writing_info={"time_map" : time_map.time_map}
            )
        return changed

    # ------------------------------------------------------------------ render
    def render_video(self,
                     directory: str | Path,
                     name: str,
                     codec: str = "MPEG-4 Video",
                     container: str = "MPEG-4 Part 14",
                     fps: float | None = None,
                     size: tuple[int, int] = (1920, 1080),
                     export_range: tuple[int, int] = (0, 1),
                     layer: int | None = None
                     ) -> str:
        """Write frames ``export_range`` (inclusive) of ``layer`` (default: the active one) to ``directory/name<ext>``.

        ``codec`` / ``container`` are the names shown in the render dialog
        (``render_formats``) or a raw FourCC / extension.  Returns the file path.
        """
        codec_4cc = render_formats.codec_type_list.get(codec, codec)
        extension = render_formats.container_type_list.get(container, container)
        if not extension.startswith("."):
            extension = "." + extension
        render_video = RenderVideo(
            codec_type=codec_4cc,
            saving_path=str(Path(directory) / f"{name}{extension}"),
            fps=float(fps) if fps else (self.ref_fps or 30.0),
            size=tuple(size),
            export_range=tuple(export_range),
            layer=layer
        )
        return render_video.compose_video()
