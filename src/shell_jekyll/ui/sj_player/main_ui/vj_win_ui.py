from PySide6.QtCore import Qt
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QComboBox,
    QWidget, QListWidget, QSlider,
    QCheckBox
)
from PySide6.QtGui import QGuiApplication
from shell_jekyll.ui.sj_player.player_win import PlayerWin

from enum import StrEnum

class PlayMethods(StrEnum):
    MPV = "ffmpeg mpv (Default)"
    NUAMIM = "nuanim (nudec)"
    QTMEDIA = "Qt MediaPlayer"

class VjWinUIMixin:
    def _init_ui(self):
        main_lo = QHBoxLayout()

        self.main_player_window_widget = PlayerWin(
            playlist=self.current_playlist, 
            audio_channels="2.1",
            do_mute_video=True
        )
        self.main_player_window_widget.media_pos_changed_sig.connect(self.on_media_pos_changed)
        self.main_player_window_widget.playlist_index_changed_sig.connect(self.on_playlist_index_changed)
        # main_lo.addWidget(self.main_player_window_widget, stretch=2)

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
        save_playlist_btn = QPushButton("Save")
        save_playlist_btn.clicked.connect(self.save_playlist)
        video_list_op_lo.addWidget(save_playlist_btn)
        open_playlist_btn = QPushButton("Open")
        open_playlist_btn.clicked.connect(self.open_playlist)
        video_list_op_lo.addWidget(open_playlist_btn)
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
        self.audio_channel_input = QLineEdit("2.1")
        audio_channel_lo.addWidget(self.audio_channel_input)
        control_panel_lo.addLayout(audio_channel_lo)

        self.is_audio_separeted_check = QCheckBox("Audio Separated")
        self.is_audio_separeted_check.setChecked(True)
        self.is_audio_separeted_check.checkStateChanged.connect(self.set_audio_separation)
        control_panel_lo.addWidget(self.is_audio_separeted_check)

        display_selection_lo = QHBoxLayout()
        display_selection_label = QLabel("Display to Use")
        display_selection_lo.addWidget(display_selection_label)
        self.display_selection_combo = QComboBox()
        self.display_selection_combo.clear()
        screens = QGuiApplication.screens()
        self.screen_dict = {}
        for screen in screens:
            self.screen_dict[screen.name()] = screen
            self.display_selection_combo.addItem(screen.name())
        display_selection_lo.addWidget(self.display_selection_combo)
        control_panel_lo.addLayout(display_selection_lo)

        control_panel_lo.addStretch()

        self.set_btn = QPushButton("Set")
        control_panel_lo.addWidget(self.set_btn)
        self.set_btn.clicked.connect(self.set_mpv_player)
        self.display_btn = QPushButton("Display")
        control_panel_lo.addWidget(self.display_btn)
        self.display_btn.clicked.connect(self.display_video)

        self.play_btn = QPushButton("Play")
        control_panel_lo.addWidget(self.play_btn)
        self.play_btn.clicked.connect(self.play_player)
        self.play_btn.hide()
        self.pause_btn = QPushButton("Pause")
        control_panel_lo.addWidget(self.pause_btn)
        self.pause_btn.clicked.connect(self.pause_player)
        self.pause_btn.hide()
        self.back_btn = QPushButton("Back to start")
        control_panel_lo.addWidget(self.back_btn)
        self.back_btn.clicked.connect(self.player_back_to_start)
        self.back_btn.hide()

        self.proceed_btn = QPushButton("Proceed")
        control_panel_lo.addWidget(self.proceed_btn)
        self.proceed_btn.clicked.connect(lambda: self.move_playlist(movement=1))
        self.proceed_btn.hide()
        self.return_btn = QPushButton("Return")
        control_panel_lo.addWidget(self.return_btn)
        self.return_btn.clicked.connect(lambda: self.move_playlist(movement=-1))
        self.return_btn.hide()

        control_panel_lo.addStretch()

        media_pos_lo = QHBoxLayout()
        self.video_pos_label = QLabel("0")
        self.video_pos_label.hide()
        media_pos_lo.addWidget(self.video_pos_label)
        self.audio_pos_label = QLabel("0")
        self.audio_pos_label.hide()
        media_pos_lo.addWidget(self.audio_pos_label)
        self.debug_shift_label = QLabel("0")
        self.debug_shift_label.hide()
        media_pos_lo.addWidget(self.debug_shift_label)
        control_panel_lo.addLayout(media_pos_lo)
        self.debug_shift_slider = QSlider()
        self.debug_shift_slider.setMinimum(-160)
        self.debug_shift_slider.setMaximum(160)
        self.debug_shift_slider.setValue(0)
        self.debug_shift_slider.setOrientation(Qt.Orientation.Horizontal)
        self.debug_shift_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.debug_shift_slider.setTickInterval(20)
        self.debug_shift_slider.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.debug_shift_slider.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.debug_shift_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: none;
                height: 4px;
                background: #CCCCCC; /* レール全体の色 */
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #CCCCCC;
            }
            QSlider::add-page:horizontal {
                background: #CCCCCC;
            }
            QSlider::handle:horizontal {
                background: #007ACC;
                border: none;
                width: 16px;
                height: 16px;
                margin: -6px 0; /* レールの中心にツマミを配置 */
                border-radius: 8px; /* 丸型ツマミ */
            }
        """)
        self.debug_shift_slider.hide()
        control_panel_lo.addWidget(self.debug_shift_slider)
        sync_audio_lo = QHBoxLayout()
        sync_audio_btn = QPushButton("Debug Shift")
        sync_audio_lo.addWidget(sync_audio_btn)
        sync_threshold_input = QLineEdit("10000")
        sync_threshold_input.setValidator(QIntValidator())
        sync_audio_lo.addWidget(sync_threshold_input)
        sync_audio_btn.clicked.connect(
            lambda: self.main_player_window_widget.sync_audio(threshold=int(sync_threshold_input.text()))
        )
        control_panel_lo.addLayout(sync_audio_lo)

        main_lo.addLayout(control_panel_lo)
        self.setLayout(main_lo)