import locale

from PySide6.QtWidgets import (
    QWidget
)

import mpv

class PlayerWin(QWidget):
    def __init__(self, 
                 play_list: list[tuple[str, str]],
                 audio_channels: str="2.1"):
        self.audio_channels = audio_channels
        self.play_list = play_list
        locale.setlocale(locale.LC_NUMERIC, 'C')
        self.mpv_player = mpv.MPV(
            wid=str(int(self.winId())),
            log_handler=print,
            loglevel="warning"
        )


    def load_media(self):
        self.mpv_player["audio-file"] = self.audio_path
        self.mpv_player["audio-channels"] = self.audio_channels

    def play_media(self):
        self.mpv_player.play(self.video_path)

    def pause_media(self):
        self.mpv_player.stop()

    def return_media(self):
        ...