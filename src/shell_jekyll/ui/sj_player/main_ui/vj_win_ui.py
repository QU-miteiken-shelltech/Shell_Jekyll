from PySide6.QtCore import Qt
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton,
    QLabel, QLineEdit, QComboBox,
    QWidget, QListWidget, QSlider,
    QCheckBox, QGroupBox
)
from PySide6.QtGui import QGuiApplication, QPixmap
from PySide6.QtMultimedia import QMediaDevices
from shell_jekyll.ui.sj_player.player_win import PlayerWin

from enum import StrEnum

class PlayMethods(StrEnum):
    MPV = "ffmpeg mpv (Default)"
    NUAMIM = "nuanim (nudec)"
    QTMEDIA = "Qt MediaPlayer"


# ---- 見た目用の定数 (ロジックとは無関係) ----
_PRIMARY_BTN_STYLE = """
    QPushButton {
        background-color: #007ACC;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 6px 12px;
        font-weight: bold;
    }
    QPushButton:hover { background-color: #1C8FDD; }
    QPushButton:pressed { background-color: #005F9E; }
"""
_DANGER_BTN_STYLE = """
    QPushButton { color: #C0392B; }
"""
_GROUP_STYLE = """
    QGroupBox {
        font-weight: bold;
        border: 1px solid #C8C8C8;
        border-radius: 6px;
        margin-top: 10px;
        padding-top: 8px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 4px;
    }
"""


class VjWinUIMixin:
    def _make_group(self, title: str) -> tuple[QGroupBox, QVBoxLayout]:
        """見た目用: タイトル付きの枠とその中身用レイアウトを作る"""
        group = QGroupBox(title)
        group.setStyleSheet(_GROUP_STYLE)
        inner_lo = QVBoxLayout(group)
        inner_lo.setContentsMargins(10, 8, 10, 10)
        inner_lo.setSpacing(8)
        return group, inner_lo

    def _init_ui(self):
        main_lo = QHBoxLayout()
        main_lo.setContentsMargins(12, 12, 12, 12)

        self.main_player_window_widget = PlayerWin(
            playlist=self.current_playlist, 
            audio_channels="2.1",
            do_mute_video=True
        )
        self.main_player_window_widget.media_pos_changed_sig.connect(self.on_media_pos_changed)
        self.main_player_window_widget.playlist_index_changed_sig.connect(self.on_playlist_index_changed)
        # main_lo.addWidget(self.main_player_window_widget, stretch=2)

        control_panel_lo = QVBoxLayout()
        control_panel_lo.setSpacing(12)

        go_to_editor_btn = QPushButton("← Go to Jekyll Editor")
        go_to_editor_btn.setToolTip("Jekyll エディタ画面へ戻ります")
        go_to_editor_btn.clicked.connect(self.go_to_editor)
        control_panel_lo.addWidget(go_to_editor_btn)

        # ---------------- Playlist ----------------
        playlist_group, playlist_inner_lo = self._make_group("Playlist")

        play_list_lo = QHBoxLayout()
        play_list_lo.setSpacing(8)

        video_col_lo = QVBoxLayout()
        video_col_lo.addWidget(QLabel("Video"))
        self.video_list = QListWidget()
        self.video_list.clear()
        self.video_list.setMinimumHeight(140)
        self.current_playlist.video_list = self.video_list
        self.video_list.currentItemChanged.connect(self.sync_audio_config_selection_to_video)
        video_col_lo.addWidget(self.video_list)
        play_list_lo.addLayout(video_col_lo)

        audio_col_lo = QVBoxLayout()
        audio_col_lo.addWidget(QLabel("Audio"))
        self.audio_list = QListWidget()
        self.audio_list.clear()
        self.audio_list.setMinimumHeight(140)
        self.current_playlist.audio_list = self.audio_list
        self.audio_list.currentItemChanged.connect(self.sync_video_selection_to_audio_config)
        audio_col_lo.addWidget(self.audio_list)
        play_list_lo.addLayout(audio_col_lo)

        playlist_inner_lo.addLayout(play_list_lo)

        video_list_op_lo = QHBoxLayout()
        video_list_op_lo.setSpacing(6)

        add_item_btn = QPushButton("Add")
        add_item_btn.setToolTip("動画をプレイリストに追加")
        add_item_btn.clicked.connect(self.add_video_to_playlist)
        video_list_op_lo.addWidget(add_item_btn)
        config_item_btn = QPushButton("Config")
        config_item_btn.setToolTip("選択中の動画に音声を設定")
        config_item_btn.clicked.connect(self.config_audio_to_video)
        video_list_op_lo.addWidget(config_item_btn)
        delete_item_btn = QPushButton("Delete")
        delete_item_btn.setToolTip("選択中の動画をプレイリストから削除")
        delete_item_btn.setStyleSheet(_DANGER_BTN_STYLE)
        delete_item_btn.clicked.connect(self.delete_video_to_playlist)
        video_list_op_lo.addWidget(delete_item_btn)

        video_list_op_lo.addSpacing(10)

        to_up_btn = QPushButton("↑")
        to_up_btn.setToolTip("1つ上へ移動")
        to_up_btn.setFixedWidth(50)
        to_up_btn.clicked.connect(self.move_playlist_up)
        video_list_op_lo.addWidget(to_up_btn)
        to_down_btn = QPushButton("↓")
        to_down_btn.setToolTip("1つ下へ移動")
        to_down_btn.setFixedWidth(50)
        to_down_btn.clicked.connect(self.move_playlist_down)
        video_list_op_lo.addWidget(to_down_btn)

        video_list_op_lo.addSpacing(10)

        save_playlist_btn = QPushButton("Save")
        save_playlist_btn.setToolTip("プレイリストを保存")
        save_playlist_btn.clicked.connect(self.save_playlist)
        video_list_op_lo.addWidget(save_playlist_btn)
        open_playlist_btn = QPushButton("Open")
        open_playlist_btn.setToolTip("保存済みプレイリストを開く")
        open_playlist_btn.clicked.connect(self.open_playlist)
        video_list_op_lo.addWidget(open_playlist_btn)
        playlist_inner_lo.addLayout(video_list_op_lo)

        control_panel_lo.addWidget(playlist_group)

        # ---------------- Settings ----------------
        settings_group, settings_inner_lo = self._make_group("Settings")

        settings_form_lo = QGridLayout()
        settings_form_lo.setHorizontalSpacing(10)
        settings_form_lo.setVerticalSpacing(8)
        settings_form_lo.setColumnStretch(1, 1)

        playmethod_label = QLabel("Play Method")
        settings_form_lo.addWidget(playmethod_label, 0, 0)
        playmethod_combo = QComboBox()
        playmethod_combo.clear()
        playmethod_combo.addItems(
            [PlayMethods.MPV, PlayMethods.NUAMIM, PlayMethods.QTMEDIA]
        )
        settings_form_lo.addWidget(playmethod_combo, 0, 1)

        audio_channel_label = QLabel("Audio Channels")
        settings_form_lo.addWidget(audio_channel_label, 1, 0)
        self.audio_channel_input = QLineEdit("2.1")
        self.audio_channel_input.setPlaceholderText("例: 2.1")
        settings_form_lo.addWidget(self.audio_channel_input, 1, 1)

        display_selection_label = QLabel("Display to Use")
        settings_form_lo.addWidget(display_selection_label, 2, 0)
        self.display_selection_combo = QComboBox()
        self.display_selection_combo.clear()
        screens = QGuiApplication.screens()
        self.screen_dict = {}
        for screen in screens:
            self.screen_dict[screen.name()] = screen
            self.display_selection_combo.addItem(screen.name())
        settings_form_lo.addWidget(self.display_selection_combo, 2, 1)

        audio_device_selection_label = QLabel("Audio Device to Use")
        settings_form_lo.addWidget(audio_device_selection_label, 3, 0)
        self.audio_device_selection_combo = QComboBox()
        self.audio_device_selection_combo.clear()
        audio_devices = QMediaDevices.audioOutputs()
        self.audio_devices_dict = {}
        for audio_device in audio_devices:
            self.audio_devices_dict[audio_device.description()] = audio_device
            self.audio_device_selection_combo.addItem(audio_device.description())
        settings_form_lo.addWidget(self.audio_device_selection_combo, 3, 1)

        shift_audio_label = QLabel("Shift Audio")
        settings_form_lo.addWidget(shift_audio_label, 4, 0)
        self.shift_audio_forward_input = QLineEdit("0")
        self.shift_audio_forward_input.setValidator(QIntValidator())
        settings_form_lo.addWidget(self.shift_audio_forward_input, 4, 1)
        settings_inner_lo.addLayout(settings_form_lo)

        self.do_mute_video_check = QCheckBox("Mute Video")
        self.do_mute_video_check.setChecked(True)
        self.do_mute_video_check.checkStateChanged.connect(self.toggle_video_muting)
        settings_inner_lo.addWidget(self.do_mute_video_check)

        control_panel_lo.addWidget(settings_group)

        # ---------------- Player controls ----------------
        # Set / Display は常に表示。主要操作なので強調スタイルにする
        setter_lo = QHBoxLayout()
        setter_lo.setSpacing(8)
        self.set_btn = QPushButton("Set")
        self.set_btn.setToolTip("プレイヤーを設定")
        self.set_btn.clicked.connect(self.set_mpv_player)
        setter_lo.addWidget(self.set_btn)
        self.display_btn = QPushButton("Display")
        self.display_btn.setToolTip("選択したディスプレイに映像を表示")
        self.display_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
        self.display_btn.clicked.connect(self.display_video)
        setter_lo.addWidget(self.display_btn)
        control_panel_lo.addLayout(setter_lo)

        # 以下は他の処理で show() されるため、枠(GroupBox)には入れず
        # 非表示のときに空の枠が残らないようにしている
        transport_lo = QHBoxLayout()
        transport_lo.setSpacing(8)
        self.reload_and_play_btn = QPushButton("↻▶ Load and Play")
        transport_lo.addWidget(self.reload_and_play_btn)
        self.reload_and_play_btn.clicked.connect(lambda: self.play_player(do_reload=True))
        self.reload_and_play_btn.hide()
        self.play_btn = QPushButton("▶ Play")
        transport_lo.addWidget(self.play_btn)
        self.play_btn.clicked.connect(lambda: self.play_player(do_reload=False))
        self.play_btn.hide()
        self.pause_btn = QPushButton("⏸ Pause")
        transport_lo.addWidget(self.pause_btn)
        self.pause_btn.clicked.connect(self.pause_player)
        self.pause_btn.hide()
        self.back_btn = QPushButton("⏮ Back to start")
        transport_lo.addWidget(self.back_btn)
        self.back_btn.clicked.connect(self.player_back_to_start)
        self.back_btn.hide()
        control_panel_lo.addLayout(transport_lo)

        navigate_lo = QHBoxLayout()
        navigate_lo.setSpacing(8)
        self.return_btn = QPushButton("◀ Return")
        navigate_lo.addWidget(self.return_btn)
        self.return_btn.clicked.connect(lambda: self.move_playlist(movement=-1))
        self.return_btn.hide()
        self.proceed_btn = QPushButton("Proceed ▶")
        navigate_lo.addWidget(self.proceed_btn)
        self.proceed_btn.clicked.connect(lambda: self.move_playlist(movement=1))
        self.proceed_btn.hide()
        control_panel_lo.addLayout(navigate_lo)

        # ---------------- Web remote ----------------
        self.use_web_btn = QPushButton("Start Web Remote")
        self.use_web_btn.setToolTip("スマホ等から操作できる Web リモコンを起動")
        self.use_web_btn.clicked.connect(self.use_web_server)
        self.use_web_btn.hide()
        control_panel_lo.addWidget(self.use_web_btn)
        self.qrcode_image_label = QLabel()
        self.qrcode_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qrcode_image_label.hide()
        control_panel_lo.addWidget(self.qrcode_image_label)

        # ---------------- Debug ----------------
        debug_group, debug_inner_lo = self._make_group("Debug")

        media_pos_lo = QHBoxLayout()
        self.video_pos_label = QLabel("V ")
        self.video_pos_label.hide()
        media_pos_lo.addWidget(self.video_pos_label)
        self.video_pos_input = QLineEdit("0")
        self.video_pos_input.setFixedWidth(65)
        self.video_pos_input.setValidator(QIntValidator())
        self.video_pos_input.editingFinished.connect(self.sync_all_media_timeline_input)
        self.video_pos_input.hide()
        media_pos_lo.addWidget(self.video_pos_input)
        self.audio_pos_label = QLabel("A ")
        self.audio_pos_label.hide()
        media_pos_lo.addWidget(self.audio_pos_label)
        self.audio_pos_input = QLineEdit("0")
        self.audio_pos_input.setFixedWidth(65)
        self.audio_pos_input.setValidator(QIntValidator())
        self.audio_pos_input.editingFinished.connect(self.sync_all_media_timeline_input)
        self.audio_pos_input.hide()
        media_pos_lo.addWidget(self.audio_pos_input)
        media_pos_lo.addStretch()
        self.debug_shift_label = QLabel("0")
        self.debug_shift_label.hide()
        media_pos_lo.addWidget(self.debug_shift_label)
        debug_inner_lo.addLayout(media_pos_lo)
        debug_shift_lo = QHBoxLayout()
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
                background: #CCCCCC; 
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
                margin: -6px 0;
                border-radius: 8px; 
            }
            QSlider::handle:horizontal[alert="true"] {
                background: #FF0000;
                border: none;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px; 
            }
        """)
        self.debug_shift_slider.hide()
        debug_shift_lo.addWidget(self.debug_shift_slider)
        shift_standard_combo = QComboBox()
        shift_standard_combo.clear()
        shift_standard_combo.addItems(
            ["ITU-R BT.1359-1", "EBU R37", "ATSC IS-191"]
        )
        shift_standard_combo.currentTextChanged.connect(self.define_tolerence)
        self.low_tolerence = -125; self.up_tolerence = 45
        debug_shift_lo.addWidget(shift_standard_combo)
        debug_inner_lo.addLayout(debug_shift_lo)
        sync_audio_lo = QHBoxLayout()
        sync_audio_lo.setSpacing(8)
        sync_audio_btn = QPushButton("Debug Shift")
        sync_audio_btn.setToolTip("音声のズレを補正します (しきい値は右の入力欄)")
        sync_audio_lo.addWidget(sync_audio_btn)
        sync_threshold_input = QLineEdit("10000")
        sync_threshold_input.setValidator(QIntValidator())
        sync_threshold_input.setPlaceholderText("Threshold")
        sync_threshold_input.setToolTip("Threshold (整数)")
        sync_audio_lo.addWidget(sync_threshold_input)
        sync_audio_btn.clicked.connect(
            lambda: self.main_player_window_widget.sync_audio(threshold=int(sync_threshold_input.text()))
        )
        debug_inner_lo.addLayout(sync_audio_lo)
        control_panel_lo.addWidget(debug_group)

        control_panel_lo.addStretch()

        main_lo.addLayout(control_panel_lo)
        self.setLayout(main_lo)