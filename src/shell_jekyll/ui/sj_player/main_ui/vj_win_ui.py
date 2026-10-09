from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QComboBox,
    QWidget, QListWidget
)

from enum import StrEnum

class PlayMethods(StrEnum):
    MPV = "ffmpeg mpv (Default)"
    NUAMIM = "nuanim (nudec)"
    QTMEDIA = "Qt MediaPlayer"

class VjWinUIMixin:
    def _init_ui(self):
        main_lo = QHBoxLayout()

        self.main_player_window_widget = QWidget()
        main_lo.addWidget(self.main_player_window_widget)

        control_panel_lo = QVBoxLayout()

        play_list_lo = QHBoxLayout()
        self.video_list = QListWidget()
        self.video_list.clear()
        self.current_playlist.video_list = self.video_list
        self.video_list.currentItemChanged.connect(self.sync_audio_config_selection_to_video)
        play_list_lo.addWidget(self.video_list)
        self.audio_list = QListWidget()
        self.audio_list.clear()
        self.current_playlist.audio_list = self.audio_list
        self.audio_list.currentItemChanged.connect(self.sync_video_selection_to_audio_config)
        play_list_lo.addWidget(self.audio_list)
        control_panel_lo.addLayout(play_list_lo)

        video_list_op_lo = QHBoxLayout()
        add_item_btn = QPushButton("Add")
        add_item_btn.clicked.connect(self.add_video_to_playlist)
        video_list_op_lo.addWidget(add_item_btn)
        config_item_btn = QPushButton("Config")
        config_item_btn.clicked.connect(self.config_audio_to_video)
        video_list_op_lo.addWidget(config_item_btn)
        delete_item_btn = QPushButton("Delete")
        delete_item_btn.clicked.connect(self.delete_video_to_playlist)
        video_list_op_lo.addWidget(delete_item_btn)
        to_up_btn = QPushButton("↑")
        to_up_btn.clicked.connect(self.move_playlist_up)
        video_list_op_lo.addWidget(to_up_btn)
        to_down_btn = QPushButton("↓")
        to_down_btn.clicked.connect(self.move_playlist_down)
        video_list_op_lo.addWidget(to_down_btn)
        control_panel_lo.addLayout(video_list_op_lo)

        control_panel_lo.addStretch()

        playmethod_lo = QHBoxLayout()
        playmethod_label = QLabel("Play Method")
        playmethod_lo.addWidget(playmethod_label)
        playmethod_combo = QComboBox()
        playmethod_combo.clear()
        playmethod_combo.addItems(
            [PlayMethods.MPV, PlayMethods.NUAMIM, PlayMethods.QTMEDIA]
        )
        playmethod_lo.addWidget(playmethod_combo)
        control_panel_lo.addLayout(playmethod_lo)

        audio_channel_lo = QHBoxLayout()
        audio_channel_label = QLabel("Audio Channels")
        audio_channel_lo.addWidget(audio_channel_label)
        audio_channel_input = QLineEdit("2.1")
        audio_channel_lo.addWidget(audio_channel_input)
        control_panel_lo.addLayout(audio_channel_lo)

        control_panel_lo.addStretch()

        self.play_btn = QPushButton("Play")
        control_panel_lo.addWidget(self.play_btn)
        self.pause_btn = QPushButton("Pause")
        control_panel_lo.addWidget(self.pause_btn)
        self.back_btn = QPushButton("Back to start")
        control_panel_lo.addWidget(self.back_btn)

        self.proceed_btn = QPushButton("Proceed")
        control_panel_lo.addWidget(self.proceed_btn)
        self.return_btn = QPushButton("Return")
        control_panel_lo.addWidget(self.return_btn)

        main_lo.addLayout(control_panel_lo)
        self.setLayout(main_lo)