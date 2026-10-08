"""GPU frame store: image pixels live in buffer objects, not in textures.

[Added] Replaces the per-frame ``QOpenGLTexture`` create / destroy / bind cycle.

How it works
------------
* Every decoded frame (RGBA8, top row first) is appended to a large GPU buffer
  object ("page").  A frame is identified by a ``FrameSlot`` =
  (page, texel offset, width, height).
* The buffer is exposed to GLSL with ``glTexBuffer`` (GL_TEXTURE_BUFFER,
  GL 3.1+) and read with ``texelFetch`` -- see ``shaders/utils/alpha_blending.glsl``.
* "Switching the image" therefore only means passing a different offset / size
  uniform; nothing is uploaded, created, destroyed or re-bound per frame
  once the frame is in the store.  Real-time playback pre-loads every frame
  once (``OpenGLImageWidget.preload_frames``).
* One buffer is limited by ``GL_MAX_TEXTURE_BUFFER_SIZE`` (and is capped at
  ``MAX_PAGE_TEXELS`` here), so long sequences spill into several pages.  A
  frame never spans two pages.

All methods must be called with the owning OpenGL context current.
"""
import ctypes
import logging
from dataclasses import dataclass

import numpy
from OpenGL import GL
from PySide6.QtGui import QImage, QImageReader

logger = logging.getLogger("shell_jekyll.gl_frame_store")

BYTES_PER_TEXEL = 4
MIN_PAGE_TEXELS = 1 << 20        # 4 MiB, first allocation of a page
MAX_PAGE_TEXELS = 1 << 26        # 256 MiB per buffer object (also capped by the driver)


@dataclass(frozen=True)
class FrameSlot:
    """Location of one frame inside the store."""
    page: int
    offset: int      # first texel inside the page's buffer
    width: int
    height: int


def image_to_rgba(image: QImage) -> tuple[numpy.ndarray, int, int]:
    """Convert ``image`` to a flat uint8 RGBA (straight alpha) array: ``(pixels, width, height)``.

    RGBA8888 rows are always 4-byte aligned, so the bytes are tightly packed
    (``bytesPerLine == 4 * width``) and can be uploaded as one block.
    """
    image = image.convertToFormat(QImage.Format.Format_RGBA8888)
    width, height = image.width(), image.height()
    nbytes = width * height * BYTES_PER_TEXEL
    bits = image.constBits()
    try:
        pixels = numpy.frombuffer(bits, dtype=numpy.uint8, count=nbytes).copy()
    except (TypeError, ValueError):
        # Some PySide6 versions return a shiboken VoidPtr without a buffer size.
        pixels = numpy.frombuffer(ctypes.string_at(int(bits), nbytes), dtype=numpy.uint8).copy()
    return pixels, width, height


class _BufferPage:
    """One buffer object + the buffer texture that exposes it to GLSL."""

    def __init__(self, capacity_texels: int):
        self.vbo = 0
        self.tex = int(GL.glGenTextures(1))
        self.capacity = 0
        self.used = 0
        self._reallocate(capacity_texels)

    def _reallocate(self, new_capacity: int) -> None:
        """(Re)create the buffer with ``new_capacity`` texels, keeping the used part."""
        new_vbo = int(GL.glGenBuffers(1))
        GL.glBindBuffer(GL.GL_COPY_WRITE_BUFFER, new_vbo)
        GL.glBufferData(GL.GL_COPY_WRITE_BUFFER, new_capacity * BYTES_PER_TEXEL, None, GL.GL_DYNAMIC_DRAW)
        if self.vbo:
            if self.used:
                GL.glBindBuffer(GL.GL_COPY_READ_BUFFER, self.vbo)
                GL.glCopyBufferSubData(GL.GL_COPY_READ_BUFFER, GL.GL_COPY_WRITE_BUFFER,
                                       0, 0, self.used * BYTES_PER_TEXEL)
                GL.glBindBuffer(GL.GL_COPY_READ_BUFFER, 0)
            GL.glDeleteBuffers(1, [self.vbo])
        GL.glBindBuffer(GL.GL_COPY_WRITE_BUFFER, 0)
        self.vbo = new_vbo
        self.capacity = new_capacity
        GL.glBindTexture(GL.GL_TEXTURE_BUFFER, self.tex)
        GL.glTexBuffer(GL.GL_TEXTURE_BUFFER, GL.GL_RGBA8, self.vbo)
        GL.glBindTexture(GL.GL_TEXTURE_BUFFER, 0)

    def append(self, pixels: numpy.ndarray, texels: int, max_capacity: int) -> int | None:
        """Upload ``pixels`` at the end of the page; return its texel offset, or None if it cannot fit."""
        need = self.used + texels
        if need > max_capacity:
            return None
        if need > self.capacity:
            self._reallocate(min(max_capacity, max(need, self.capacity * 2, MIN_PAGE_TEXELS)))
        offset = self.used
        GL.glBindBuffer(GL.GL_COPY_WRITE_BUFFER, self.vbo)
        GL.glBufferSubData(GL.GL_COPY_WRITE_BUFFER, offset * BYTES_PER_TEXEL, texels * BYTES_PER_TEXEL, pixels)
        GL.glBindBuffer(GL.GL_COPY_WRITE_BUFFER, 0)
        self.used = need
        return offset

    def destroy(self) -> None:
        if self.vbo:
            GL.glDeleteBuffers(1, [self.vbo])
        if self.tex:
            GL.glDeleteTextures(1, [self.tex])
        self.vbo = self.tex = 0
        self.capacity = self.used = 0


class FrameStore:
    """Cache of decoded frames, keyed by file path, stored in GPU buffer pages."""

    def __init__(self) -> None:
        self.pages: list[_BufferPage] = []
        self.slots: dict[str, FrameSlot] = {}
        self._max_page_texels: int | None = None

    @property
    def max_page_texels(self) -> int:
        """Largest page this driver allows (``GL_MAX_TEXTURE_BUFFER_SIZE``, capped)."""
        if self._max_page_texels is None:
            self._max_page_texels = min(int(GL.glGetIntegerv(GL.GL_MAX_TEXTURE_BUFFER_SIZE)), MAX_PAGE_TEXELS)
        return self._max_page_texels

    @property
    def used_bytes(self) -> int:
        return sum(page.used for page in self.pages) * BYTES_PER_TEXEL

    def __len__(self) -> int:
        return len(self.slots)

    def texture_id(self, slot: FrameSlot) -> int:
        """Buffer-texture name to bind (GL_TEXTURE_BUFFER) when drawing ``slot``."""
        return self.pages[slot.page].tex

    def reserve(self, total_texels: int) -> None:
        """Pre-allocate the first page so a bulk pre-load does not re-allocate / copy repeatedly."""
        if total_texels > 0 and not self.pages:
            self.pages.append(_BufferPage(min(max(total_texels, MIN_PAGE_TEXELS), self.max_page_texels)))

    def ensure(self, path: str) -> FrameSlot | None:
        """Return the slot of ``path``, decoding and uploading it first if it is not stored yet.

        Returns None if the file cannot be read or is larger than one page.
        """
        slot = self.slots.get(path)
        if slot is not None:
            return slot
        image = QImage(path)
        if image.isNull():
            logger.warning("cannot read image: %s", path)
            return None
        pixels, width, height = image_to_rgba(image)
        texels = width * height
        if texels > self.max_page_texels:
            logger.warning("image too large for one buffer (%dx%d): %s", width, height, path)
            return None
        offset = self.pages[-1].append(pixels, texels, self.max_page_texels) if self.pages else None
        if offset is None:
            self.pages.append(_BufferPage(min(max(texels, MIN_PAGE_TEXELS), self.max_page_texels)))
            offset = self.pages[-1].append(pixels, texels, self.max_page_texels)
        slot = FrameSlot(page=len(self.pages) - 1, offset=offset, width=width, height=height)
        self.slots[path] = slot
        return slot

    def clear(self) -> None:
        """Free every GPU buffer.  All previously returned slots become invalid."""
        for page in self.pages:
            page.destroy()
        self.pages.clear()
        self.slots.clear()


def count_texels(paths) -> int:
    """Total pixel count of ``paths`` using only the image headers (no full decode)."""
    total = 0
    for path in paths:
        size = QImageReader(str(path)).size()
        if size.isValid():
            total += size.width() * size.height()
    return total
