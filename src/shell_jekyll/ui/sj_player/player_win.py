import math
from pathlib import Path

from PySide6.QtCore import QUrl, Signal, QTimer
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget

class PlayerWin(QWidget):
    media_pos_changed_sig = Signal(tuple)
    playlist_index_changed_sig = Signal(int, int)

    def __init__(self, 
                 playlist: list[tuple[str, str]] | None,
                 audio_channels: str="2.1",
                 do_mute_video=True
                 ):
        super().__init__()
        self.setWindowFlags(Qt.Window)
        self.setWindowTitle("Media Display")
        self.resize(960, 540)   
        self.setMinimumSize(360, 640)

        video_widget_lo = QVBoxLayout()
        video_widget_lo.setContentsMargins(0, 0, 0, 0)
        self.video_widget = QVideoWidget()
        video_widget_lo.addWidget(self.video_widget)
        self.video_widget.setMinimumSize(360, 640)
        self.setLayout(video_widget_lo)

        self.video_player = QMediaPlayer()
        self.video_audio_outputer = QAudioOutput()
        self.video_player.setAudioOutput(self.video_audio_outputer)
        self.video_player.setVideoOutput(self.video_widget)
        self.video_audio_outputer.setMuted(do_mute_video)
        self.audio_player = QMediaPlayer()
        self.audio_audio_outputer = QAudioOutput()
        self.audio_player.setAudioOutput(self.audio_audio_outputer)

        self.is_prepared = False
        self.is_video_available = False
        self.is_audio_available = False
        self.playlist = playlist
        self.current_index = 0
        self.do_mute_video = do_mute_video

        self.media_timer = QTimer()
        self.media_timer.setInterval(300)
        self.media_timer.timeout.connect(self.sync_audio)
        self.media_timer.start()

    def sync_audio(self, threshold: int=100000):
        if not self.is_prepared: return
        if not self.video_player.isPlaying() or not self.audio_player.isPlaying(): return
        video_pos = self.video_player.position()
        audio_pos = self.audio_player.position()
        diff = abs(video_pos - audio_pos)
        if diff >= threshold:
            self.audio_player.setPosition(video_pos)
        debugger_val = int(audio_pos - video_pos)
        self.media_pos_changed_sig.emit((debugger_val, video_pos, audio_pos))

    def set_media(self, index: int | None):
        if not self.is_prepared or self.playlist is None: return
        if index is not None:
            if index >= len(self.playlist): return
        if index is not None:
            self.current_index = index
        video_path = self.playlist[self.current_index][0]
        if video_path and Path(video_path).exists():
            self.video_player.pause()
            self.video_player.setPosition(0)
            self.video_player.setSource(QUrl.fromLocalFile(video_path))
            self.video_audio_outputer.setMuted(self.do_mute_video)
            self.is_video_available = True
        audio_path = self.playlist[self.current_index][1]
        if audio_path and Path(audio_path).exists():
            self.audio_player.setPosition(0)
            self.audio_player.pause()
            self.audio_player.setSource(QUrl.fromLocalFile(audio_path))
            self.is_audio_available = True
        self.playlist_index_changed_sig.emit(
            self.current_index, min(self.video_player.duration(), self.audio_player.duration())
        )

    def play_media(self):
        if not self.is_prepared or self.playlist is None: return
        if self.is_video_available: self.video_player.play()
        if self.is_audio_available: self.audio_player.play()

    def pause_media(self):
        if not self.is_prepared or self.playlist is None: return
        if self.is_video_available: self.video_player.pause()
        if self.is_audio_available: self.audio_player.pause()

    def back_to_start(self):
        if not self.is_prepared or self.playlist is None: return
        if self.is_video_available: self.video_player.setPosition(0)
        if self.is_audio_available: self.audio_player.setPosition(0)

    def move_playlist(self, movement: int=1):
        if not self.is_prepared or self.playlist is None: return
        new_index = self.current_index + movement
        if new_index < 0 or new_index >= len(self.playlist): return
        self.set_media(index=new_index)

    def set_pos(self, newpos: int):
        if newpos > self.video_player.duration() or newpos > self.audio_player.duration():
            return
        if self.is_audio_available: 
            self.video_player.pause()
            self.video_player.setPosition(newpos)
        if self.is_audio_available: 
            self.audio_player.pause()
            self.audio_player.setPosition(newpos)

    def mute_video(self, do_mute_video: bool):
        self.do_mute_video = do_mute_video
        self.video_audio_outputer.setMuted(self.do_mute_video)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

