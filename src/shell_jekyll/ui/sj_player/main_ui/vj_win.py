from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from shell_jekyll.ui.sj_player.main_ui.vj_win_ui import VjWinUIMixin
from shell_jekyll.ui.sj_player.main_ui.vj_win_events import VjWinEventsMixin, PlayListObj
from shell_jekyll import gb_var as gb_var_global

class VjUserUi(QWidget,
               VjWinUIMixin,
               VjWinEventsMixin
               ):

    def __init__(self):
        super().__init__()

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)

        self.setStyleSheet(gb_var_global.style_script.MAIN_WIN_STYLESHEET)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.current_playlist: PlayListObj = PlayListObj(
            [], video_list=None, audio_list=None
        )

        self._init_ui()
