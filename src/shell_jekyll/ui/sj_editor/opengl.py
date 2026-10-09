import gc
import logging
import numpy
import ctypes
from pathlib import Path

from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtOpenGL import QOpenGLShaderProgram, QOpenGLShader
from OpenGL import GL

from shell_jekyll.gb_var import MAX_LAYER
from shell_jekyll.ui.sj_editor.gl_frame_store import FrameStore, FrameSlot, count_texels
from shell_jekyll.utils.editing_utils import FALLBACK_IMAGE
from shell_jekyll.utils.layer_view import LayerViewState

logger = logging.getLogger("shell_jekyll.opengl")

MAX_LAYERS : int = MAX_LAYER

SHADER_DIR = Path(__file__).resolve().parents[1] / "shaders" / "utils"
DEFAULT_VERTEX_SHADER = SHADER_DIR / "vertex_shader.glsl"
DEFAULT_FRAGMENT_SHADER = SHADER_DIR / "alpha_blending.glsl"
DEFAULT_EFFECT_SHADER = SHADER_DIR / "user_effect_default.glsl"

# In live (not pre-loaded) mode the GPU frame cache is emptied when it grows beyond this.
LIVE_CACHE_LIMIT_BYTES = 512 * 1024 * 1024


class OpenGLImageWidget(QOpenGLWidget):
    """Multi-layer image viewer.  Pixels are stored in GPU buffers (see ``gl_frame_store``).

    [Changed] Rewritten around ``FrameStore`` (VBO-style pixel storage read with
    ``texelFetch``) instead of one ``QOpenGLTexture`` per layer that was
    destroyed and re-created on every frame change.  Public method names
    (``change_image``, ``change_image_onram``, ``send_img_to_buffer``,
    ``release_buffer``, ``switch_size_standard``, ``toggle_layer_visibility``)
    are kept.  New: ``preload_frames``, ``is_preloaded``, ``set_effect_shader``,
    ``set_shader_sources``, ``set_custom_uniform``, ``shader_error`` (custom GLSL).

    Layer order: layer index 0 (top of the layer list) is drawn last, i.e. on top.
    """

    def __init__(self, image_path: str | list = "", parent=None):
        """``image_path``: image (or list of images, one per layer) shown until real frames are set.

        [Changed] ``texture`` / ``ram_img_buffer`` / ``visibility_setting`` /
        ``size_standard_idx`` attributes became ``_store`` / ``_layer_slots`` /
        ``view_state`` (properties keep the two settings readable under the old names).
        """
        super().__init__(parent)
        self.image_path = image_path
        self.view_state = LayerViewState()
        self.program = None
        self.vao = None
        self.vbo = None

        self._store: FrameStore | None = None
        self._layer_slots: list[FrameSlot | None] = []
        self._requested_paths: list[str] = []
        self._pending_preload: list[str] | None = None
        self._preloaded = False

        self._vertex_src: str | None = None
        self._fragment_src: str | None = None
        self._effect_src: str | None = None
        self._custom_uniforms: dict[str, object] = {}
        self.shader_error: str = ""

    # ------------------------------------------------------------------ state
    @property
    def visibility_setting(self) -> list[int]:
        return self.view_state.visibility_setting

    @property
    def size_standard_idx(self) -> int:
        return self.view_state.size_standard_idx

    @property
    def is_preloaded(self) -> bool:
        """True while every frame of the project is held in GPU buffers (real-time preview mode)."""
        return self._preloaded

    @property
    def image_ratio(self) -> float:
        """Aspect ratio (w/h) of the size-standard layer's current frame."""
        slot = self._standard_slot()
        return slot.width / slot.height if slot else 1.0

    def _standard_slot(self) -> FrameSlot | None:
        slots = self._layer_slots
        idx = self.view_state.size_standard_idx
        if 0 <= idx < len(slots) and slots[idx] is not None:
            return slots[idx]
        return next((s for s in slots if s is not None), None)

    # --------------------------------------------------------------- GL set-up
    def initializeGL(self):
        """Set up GL state, the quad, the shader program and the GPU frame store.

        [Changed] Instead of loading one ``QOpenGLTexture`` here, a ``FrameStore``
        is created and the pending / initial image paths are put into it.  Shader
        files are read through ``_rebuild_program`` (shared with the custom shader
        hooks); if a custom shader set before the context existed does not compile
        the defaults are used.  The old early ``return`` on a missing shader file
        (which left a blank widget and no ``vao``) is now an error message in
        ``shader_error``.  The quad's second attribute was not enabled in the
        reference widget copy; it is one code path now.
        """
        GL.glClearColor(0, 0, 0, 1.0)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

        self._store = FrameStore()
        self._build_quad()
        if not self._rebuild_program() and (self._vertex_src or self._fragment_src or self._effect_src):
            # Custom shader given before the context existed failed: use the defaults.
            error = self.shader_error
            self._vertex_src = self._fragment_src = self._effect_src = None
            self._rebuild_program()
            self.shader_error = error
        self.context().aboutToBeDestroyed.connect(self._release_gl_resources)

        if self._pending_preload is not None:
            paths, self._pending_preload = self._pending_preload, None
            self._preload(paths)
        initial = self._requested_paths or self._initial_paths()
        self._apply_paths(initial)

    def _initial_paths(self) -> list[str]:
        if isinstance(self.image_path, (list, tuple)):
            return [str(p) for p in self.image_path]
        return [str(self.image_path if self.image_path else FALLBACK_IMAGE)]

    def _build_quad(self) -> None:
        """Create the full-screen quad (interleaved position + uv) in a VAO / VBO."""
        vertices = numpy.array(
            [
                -1.0, -1.0, 0.0, 1.0,
                1.0, -1.0, 1.0, 1.0,
                -1.0,  1.0, 0.0, 0.0,
                1.0, -1.0, 1.0, 1.0,
                1.0,  1.0, 1.0, 0.0,
                -1.0,  1.0, 0.0, 0.0,
            ],
            dtype=numpy.float32,
        )
        self.vao = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.vao)
        self.vbo = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
        GL.glBufferData(
            GL.GL_ARRAY_BUFFER,
            vertices.nbytes,
            vertices,
            GL.GL_STATIC_DRAW
        )
        st = 4 * 4
        GL.glVertexAttribPointer(
            0, 2,
            GL.GL_FLOAT, GL.GL_FALSE, st,
            ctypes.c_void_p(0)
        )
        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(
            1, 2,
            GL.GL_FLOAT, GL.GL_FALSE, st,
            ctypes.c_void_p(8)
        )
        GL.glEnableVertexAttribArray(1)
        GL.glBindVertexArray(0)

    def _release_gl_resources(self) -> None:
        """Free GPU objects when the GL context is about to be destroyed."""
        try:
            if self._store is not None:
                self._store.clear()
            if self.vbo:
                GL.glDeleteBuffers(1, [self.vbo])
            if self.vao:
                GL.glDeleteVertexArrays(1, [self.vao])
        except Exception:
            logger.exception("GL cleanup failed")
        self._layer_slots = []
        self.program = None
        self.vao = self.vbo = None

    # ----------------------------------------------------------------- shaders
    @staticmethod
    def _read_shader(path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def _rebuild_program(self) -> bool:
        """Compile and link the shader program from the current sources (context must be current).

        The compositing fragment shader and the *effect* fragment shader
        (defines ``vec4 userEffect(vec4 color, vec2 uv)``) are two shader
        objects of the same program.  On failure the previous program is kept
        and the compiler log is stored in ``shader_error``.
        """
        try:
            vertex = self._vertex_src or self._read_shader(DEFAULT_VERTEX_SHADER)
            fragment = self._fragment_src or self._read_shader(DEFAULT_FRAGMENT_SHADER)
            program = QOpenGLShaderProgram()
            ok = (
                program.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Vertex, vertex)
                and program.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Fragment, fragment)
            )
            # A fully custom fragment shader owns its own userEffect unless an effect is set explicitly.
            if ok and (self._fragment_src is None or self._effect_src is not None):
                effect = self._effect_src or self._read_shader(DEFAULT_EFFECT_SHADER)
                ok = program.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Fragment, effect)
            ok = ok and program.link()
        except OSError as e:
            self.shader_error = f"shader file error: {e}"
            logger.error(self.shader_error)
            return False
        if not ok:
            self.shader_error = program.log()
            logger.error("shader error: %s", self.shader_error)
            return False
        self.program = program
        self.shader_error = ""
        return True

    def _apply_shader_sources(self, vertex, fragment, effect) -> bool:
        """Switch to new shader sources; revert and return False when they do not compile."""
        previous = (self._vertex_src, self._fragment_src, self._effect_src)
        self._vertex_src, self._fragment_src, self._effect_src = vertex, fragment, effect
        ok = True
        if self.isValid():
            self.makeCurrent()
            try:
                ok = self._rebuild_program()
            finally:
                self.doneCurrent()
            if not ok:
                self._vertex_src, self._fragment_src, self._effect_src = previous
        self.update()
        return ok

    def set_effect_shader(self, source: str | None = None, path: str | Path | None = None) -> bool:
        """Apply a custom GLSL post effect on top of the composited image.

        [Added] The hook for arbitrary GLSL.  ``source`` (or the contents of
        the file ``path``) must define ``vec4 userEffect(vec4 color, vec2 uv)``
        (see ``shaders/utils/user_effect_default.glsl``); a missing
        ``#version`` line is added.  Call with no arguments to go back to the
        identity effect.  Returns False (and keeps the old shader) when it does
        not compile; the compiler log is then in ``shader_error``.
        """
        if path is not None:
            source = self._read_shader(Path(path))
        if source is not None and not source.lstrip().startswith("#version"):
            source = "#version 330 core\n" + source
        return self._apply_shader_sources(self._vertex_src, self._fragment_src, source)

    def set_shader_sources(self, vertex: str | None = None, fragment: str | None = None) -> bool:
        """Replace the vertex and/or compositing fragment shader (``None`` = built-in default).

        [Added] Full-control hook.  A custom vertex shader must provide
        ``location 0`` position / ``location 1`` uv inputs and a ``vTex``
        output; a custom fragment shader should follow the uniform contract of
        ``alpha_blending.glsl`` (``uFrameBuf`` / ``uFrameOffset`` /
        ``uFrameSize`` / ``uLayerEnabled`` / ``uLayerCount`` / ``uBgColor``) to
        keep showing the layers, and either defines ``userEffect`` itself or is
        combined with ``set_effect_shader``.  Returns False (old shaders kept)
        when it does not compile.
        """
        return self._apply_shader_sources(vertex, fragment, self._effect_src)

    def set_custom_uniform(self, name: str, value) -> None:
        """Set a uniform used by a custom shader; it is re-applied on every paint.

        [Added] ``value``: bool/int -> int, float -> float, sequence of 2-4
        numbers -> ivecN (all ints) or vecN.  Unknown / optimised-out names are
        ignored.  ``None`` removes the uniform.
        """
        if value is None:
            self._custom_uniforms.pop(name, None)
        else:
            self._custom_uniforms[name] = value
        self.update()

    def clear_custom_uniforms(self) -> None:
        self._custom_uniforms.clear()
        self.update()

    def _apply_custom_uniforms(self, program_id: int) -> None:
        for name, value in self._custom_uniforms.items():
            loc = GL.glGetUniformLocation(program_id, name)
            if loc < 0:
                continue
            if isinstance(value, (bool, int)):
                GL.glUniform1i(loc, int(value))
            elif isinstance(value, float):
                GL.glUniform1f(loc, value)
            else:
                values = list(value)
                is_int = all(isinstance(v, int) and not isinstance(v, bool) for v in values)
                setter = {
                    (True, 2): GL.glUniform2i, (True, 3): GL.glUniform3i, (True, 4): GL.glUniform4i,
                    (False, 2): GL.glUniform2f, (False, 3): GL.glUniform3f, (False, 4): GL.glUniform4f,
                }.get((is_int, len(values)))
                if setter is None:
                    logger.warning("unsupported uniform value for %s: %r", name, value)
                    continue
                setter(loc, *values)

    # ------------------------------------------------------------ frame control
    def _apply_paths(self, paths: list[str]) -> None:
        """Make sure every path is in the store and remember each layer's slot (context must be current)."""
        store = self._store
        if not self._preloaded and store.used_bytes > LIVE_CACHE_LIMIT_BYTES:
            store.clear()
        slots = []
        for path in paths[:MAX_LAYERS]:
            slots.append(store.ensure(path) or store.ensure(str(FALLBACK_IMAGE)))
        self._layer_slots = slots

    def change_image(self,
                     new_image_paths: list[str] | list[Path]
                     ) -> None:
        """Show ``new_image_paths`` (one file per layer, layer 0 on top).

        [Changed] One code path for live and pre-loaded mode: frames already in
        the GPU store are shown with no upload at all; others are decoded and
        appended to the store.  This replaces the old pair ``change_image``
        (re-create textures) / ``change_image_onram`` (broken lookup).  An
        unreadable file now shows ``fallback.png`` in its layer instead of
        silently dropping the layer (which shifted all following layers).
        Safe to call before the widget has been shown: the paths are applied
        when OpenGL is initialised.
        """
        self._requested_paths = [str(x) for x in new_image_paths]
        if self.isValid():
            self.makeCurrent()
            try:
                self._apply_paths(self._requested_paths)
            finally:
                self.doneCurrent()
        self.update()

    def change_image_onram(self,
                           next_image_paths: list[str] | list[Path]
                           ) -> None:
        """Same as ``change_image`` (kept for the real-time playback call site).

        [Changed] The old version could never work: it used the *list* of
        paths as a dict key (``TypeError`` swallowed by a bare ``except: pass``),
        so nothing was ever drawn during playback; its fallback value was a
        ``str`` that was then indexed like a tuple.
        """
        self.change_image(new_image_paths=next_image_paths)

    def preload_frames(self, paths, progress=None) -> int:
        """Load all ``paths`` into GPU buffers once so playback needs no further uploads.

        ``progress(done, total)`` is called after every file if given.
        Returns the number of frames now stored.  Replaces the old
        ``send_img_to_buffer`` body, which iterated over the *characters* of a
        path string (``img_file_path_list[i][j]``) and therefore buffered nothing.
        """
        paths = [str(p) for p in paths]
        if not self.isValid():
            self._pending_preload = paths
            return 0
        self.makeCurrent()
        try:
            return self._preload(paths, progress)
        finally:
            self.doneCurrent()

    def _preload(self, paths: list[str], progress=None) -> int:
        if self._preloaded:
            return len(self._store)
        self._store.reserve(count_texels(paths))
        self._store.ensure(str(FALLBACK_IMAGE))     # frames with no image show it: keep playback upload-free
        for i, path in enumerate(paths):
            self._store.ensure(path)
            if progress is not None:
                progress(i + 1, len(paths))
        self._preloaded = len(self._store) > 0
        self._apply_paths(self._requested_paths)
        return len(self._store)

    def send_img_to_buffer(self):
        """Pre-load every image used by the project (kept name; see ``preload_frames``)."""
        from shell_jekyll.utils.editing_utils import EditingUtils
        if self._preloaded:
            return
        self.preload_frames(EditingUtils.used_image_paths())

    def release_buffer(self):
        """Free the pre-loaded frames (GPU memory) and go back to live mode.

        The currently shown frames are re-loaded so the picture does not change.
        """
        if not self._preloaded:
            return
        self._preloaded = False
        if self._store is not None and self.isValid():
            self.makeCurrent()
            try:
                self._store.clear()
                self._apply_paths(self._requested_paths)
            finally:
                self.doneCurrent()
        self.update()
        gc.collect()
        try:
            import platform
            if platform.system() == "Linux":
                ctypes.CDLL("libc.so.6").malloc_trim(0)
        except Exception:
            pass

    # ----------------------------------------------------------- view settings
    def switch_size_standard(self, new_idx: int):
        """[Changed] State moved to ``LayerViewState`` (shared with ``api.ShellJekyll``); same behaviour."""
        self.view_state.switch_size_standard(new_idx)
        self.update()

    def toggle_layer_visibility(self,
                                target_layer: int,
                                mode: int=1
                                ) -> None:
        """[Changed] Logic moved unchanged to ``LayerViewState.toggle_layer_visibility``.

        mode 1: toggle, 2: hide all except selected (solo / inverse solo), 3: show all.
        """
        self.view_state.toggle_layer_visibility(target_layer, mode)
        self.update()

    # ------------------------------------------------------------------ paint
    def paintGL(self):
        """Draw the layers.

        [Changed]
        * The old code did ``self.texture = self.texture[::-1]`` on EVERY
          paint, so merely resizing / exposing the window flipped the layer
          order, and visibility / "size standard" (indexed by list row) hit the
          mirrored layer.  The order is now fixed in the shader (layer 0 on top)
          and nothing is mutated while painting.
        * No per-paint texture ``bind`` / ``release``: each layer just binds its
          buffer page and passes (offset, size) uniforms.
        * ``glViewport`` is no longer touched by us: ``QOpenGLWidget`` sets it
          (in device pixels) before ``paintGL``; the old ``resizeGL`` override
          used logical pixels and was wrong on HiDPI screens.
        """
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        slots = self._layer_slots
        if self.program is None or self._store is None or not slots:
            return
        n = min(len(slots), MAX_LAYERS)
        if self.view_state.size_standard_idx >= n:
            self.view_state.size_standard_idx = 0
        ref = self._standard_slot()
        if ref is None:
            return

        self.program.bind()
        pid = self.program.programId()

        widget_w, widget_h = max(self.width(), 1), max(self.height(), 1)
        img_aspect = ref.width / ref.height if ref.height else 1.0
        widget_aspect = widget_w / widget_h if widget_h else 1.0
        if widget_aspect > img_aspect:
            scale_x, scale_y = img_aspect / widget_aspect, 1.0
        else:
            scale_x, scale_y = 1.0, widget_aspect / img_aspect
        GL.glUniform2f(GL.glGetUniformLocation(pid, "uScale"), scale_x, scale_y)

        # [Added] every sampler unit gets a valid buffer texture (unused ones: 1 dummy texel)
        dummy = self._store.dummy_texture()
        for i in range(MAX_LAYERS):
            GL.glActiveTexture(GL.GL_TEXTURE0 + i)
            GL.glBindTexture(GL.GL_TEXTURE_BUFFER, dummy)

        offsets = [0] * MAX_LAYERS
        sizes = [0] * (2 * MAX_LAYERS)
        enabled = [0] * MAX_LAYERS
        for i in range(n):
            slot = slots[i]
            if slot is None:
                continue
            GL.glActiveTexture(GL.GL_TEXTURE0 + i)
            GL.glBindTexture(GL.GL_TEXTURE_BUFFER, self._store.texture_id(slot))
            offsets[i] = slot.offset
            sizes[2 * i], sizes[2 * i + 1] = slot.width, slot.height
            enabled[i] = self.view_state.visibility_setting[i]

        GL.glUniform1iv(GL.glGetUniformLocation(pid, "uFrameBuf"), MAX_LAYERS, numpy.arange(MAX_LAYERS, dtype=numpy.int32))
        GL.glUniform1iv(GL.glGetUniformLocation(pid, "uFrameOffset"), MAX_LAYERS, numpy.array(offsets, dtype=numpy.int32))
        GL.glUniform2iv(GL.glGetUniformLocation(pid, "uFrameSize"), MAX_LAYERS, numpy.array(sizes, dtype=numpy.int32))
        GL.glUniform1iv(GL.glGetUniformLocation(pid, "uLayerEnabled"), MAX_LAYERS, numpy.array(enabled, dtype=numpy.int32))
        GL.glUniform1i(GL.glGetUniformLocation(pid, "uLayerCount"), n)
        GL.glUniform3f(GL.glGetUniformLocation(pid, "uBgColor"), 0.0, 0.0, 0.0)
        self._apply_custom_uniforms(pid)

        GL.glBindVertexArray(self.vao)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 6)
        GL.glBindVertexArray(0)

        for i in range(MAX_LAYERS):
            GL.glActiveTexture(GL.GL_TEXTURE0 + i)
            GL.glBindTexture(GL.GL_TEXTURE_BUFFER, 0)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        self.program.release()
