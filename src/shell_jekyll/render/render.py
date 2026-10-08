import cv2

from shell_jekyll.utils.editing_utils import EditingUtils, FALLBACK_IMAGE
from shell_jekyll import gb_var as gb_var_script

gb_var = gb_var_script.get_gbvar_ctx()
gb_var_full = gb_var_script.get_gbvar_full()

class RenderVideo:
    def __init__(self,
                 codec_type: str,
                 saving_path: str,
                 fps: float,
                 size: tuple[int, int],
                 export_range: tuple[int, int],
                 layer: int | None = None
                 ) -> None:
        self.codec_type = codec_type
        self.saving_path = saving_path
        self.fps = fps
        self.size = size
        self.export_range = export_range
        self.layer = layer

    def get_video_writer(self) -> cv2.VideoWriter:
        fourcc_codec = cv2.VideoWriter_fourcc(*self.codec_type)
        writer = cv2.VideoWriter(str(self.saving_path), fourcc_codec, self.fps, self.size)
        return writer

    def compose_video(self) -> str:
        """Write frames ``export_range[0]..export_range[1]`` (inclusive) of one layer to a video file.

        [Changed] The old implementation could not run at all:
        * ``EditingUtils.get_actual_filepath`` was called without its required
          ``layer`` argument (``TypeError``).
        * "Is this frame in the time map?" was tested with ``i in time_map_dict``
          where ``time_map_dict`` is the *list* of per-layer dicts, so it was
          always False, and even when true it used the timeline number ``i`` as
          the file number instead of the mapped one.  It now uses
          ``EditingUtils.get_actual_img_idx`` -- the same "mapped number, else
          hold the previous frame" rule the preview uses.
        * Frames whose size differs from ``size`` were passed to
          ``VideoWriter.write`` unchanged, which makes OpenCV silently drop them
          (empty video).  They are now resized to ``size``.
        * An unusable codec / path used to fail silently; it now raises
          ``RuntimeError``.  A missing / unreadable image falls back to
          ``fallback.png`` as before (black frame if even that cannot be read).

        The layer rendered is ``layer`` (default: the active layer, which is
        what the old ``gb_var.sequence_root_dir`` meant).  Returns the path.
        """
        layer = self.layer if self.layer is not None else gb_var.active_layer
        writer = self.get_video_writer()
        if not writer.isOpened():
            raise RuntimeError(f"Cannot open video writer: {self.saving_path} (codec {self.codec_type})")
        try:
            for i in range(self.export_range[0], self.export_range[1] + 1):
                actual_idx = EditingUtils.get_actual_img_idx(seq_idx=i, layer=layer)
                image_path = EditingUtils.get_layer_image_path(img_idx=actual_idx, layer=layer)
                frame = cv2.imread(str(image_path))
                if frame is None:
                    frame = cv2.imread(str(FALLBACK_IMAGE))
                if frame is None:
                    frame = _black_frame(self.size)
                if (frame.shape[1], frame.shape[0]) != tuple(self.size):
                    frame = cv2.resize(frame, tuple(self.size), interpolation=cv2.INTER_AREA)
                writer.write(frame)
        finally:
            writer.release()
        return str(self.saving_path)


def _black_frame(size: tuple[int, int]):
    import numpy
    return numpy.zeros((size[1], size[0], 3), dtype=numpy.uint8)
