from pathlib import Path

from shell_jekyll.ui.opengl import OpenGLImageWidget


class OpenGLImageSingleWidget(OpenGLImageWidget):
    """Single-image viewer used for the reference frame.

    [Changed] This used to be a ~150-line copy of ``OpenGLImageWidget``.  Its
    ``paintGL`` never set the layer uniforms (the code was commented out), so
    the shader looped over zero layers and the reference view was always black.
    It is now the multi-layer widget showing exactly one layer, so it shares the
    VBO pixel storage, the shader hooks and the fixes of the main widget.
    The leftover debug ``print("HELLO")`` / ``print("@@ path")`` were dropped.
    """

    def change_image(self,
                     new_image_path: str | Path
                     ) -> None:
        super().change_image([str(new_image_path)])
