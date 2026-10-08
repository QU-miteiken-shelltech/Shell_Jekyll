from shell_jekyll.gb_var import MAX_LAYER


class LayerViewState:
    """Per-layer display settings (visibility, size standard) -- no Qt / GL dependency.

    [Added] This state used to live inside ``OpenGLImageWidget`` only
    (``visibility_setting`` / ``size_standard_idx``), so it could not be used
    without a GL widget.  The widget and ``api.ShellJekyll`` now share one
    instance, which lets scripts change the display without any UI.

    Layer indices are *list rows*: row 0 is the topmost layer on screen.
    """

    def __init__(self) -> None:
        self.visibility_setting: list[int] = [1] * MAX_LAYER
        self.size_standard_idx: int = 0

    def toggle_layer_visibility(self,
                                target_layer: int,
                                mode: int = 1
                                ) -> None:
        """Change layer visibility.  mode 1: toggle, 2: solo / inverse-solo, 3: show all.

        Logic is the former ``OpenGLImageWidget.toggle_layer_visibility``,
        unchanged (mode 2: if the target is hidden, hide all except it;
        otherwise show all except it).
        """
        if mode == 1:
            self.visibility_setting[target_layer] = int(not self.visibility_setting[target_layer])
        elif mode == 2:
            if self.visibility_setting[target_layer] == 0:
                self.visibility_setting = [0] * MAX_LAYER
                self.visibility_setting[target_layer] = 1
            else:
                self.visibility_setting = [1] * MAX_LAYER
                self.visibility_setting[target_layer] = 0
        else:
            self.visibility_setting = [1] * MAX_LAYER

    def switch_size_standard(self, new_idx: int) -> None:
        """Choose which layer decides the on-screen image aspect ratio."""
        self.size_standard_idx = new_idx
