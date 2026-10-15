from collections import UserList
import json
import socket
import tempfile
import os
from pathlib import Path
from threading import Thread

from PySide6.QtWidgets import QFileDialog, QMainWindow
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, Slot

import qrcode

from shell_jekyll.ui.sj_player.remote_app import RequestType, run_web_remote
from shell_jekyll.ui.sj_editor.main_win.main_win import MainUserUi
from shell_jekyll.ui.sj_player.vj_win_actionman import defined_alias
from shell_jekyll.ui.sj_player.shell_eqcorrect import ShellEqcorrectPlugin
from shell_jekyll.audio.audio_processing import AudioProcessing
from shell_jekyll.ui.sj_player.download_popup import DownloadPopupDialog

class PlayListObj(UserList):
    def __init__(self, initlist, video_list, audio_list):
        super().__init__(initlist)
        self.video_list = video_list
        self.audio_list = audio_list

    def append(self, item: tuple[str, str]):
        super().append(item)
        self.video_list.addItem(item[0])
        self.audio_list.addItem(item[1])

    def update(self, index: int, item: tuple[str, str]):
        if index >= len(self):
            return
        self[index] = item
        self.video_list.item(index).setText(item[0])
        self.audio_list.item(index).setText(item[1])

    def delete(self, index):
        if index >= len(self):
            return
        self.pop(index)
        self.video_list.takeItem(index)
        self.audio_list.takeItem(index)

    def move(self, from_index, to_index):
        self.insert(to_index, self.pop(from_index))
        self.video_list.clear()
        self.audio_list.clear()
        for x in self:
            self.video_list.addItem(x[0])
            self.audio_list.addItem(x[1])
            

class VjWinEventsMixin:
    def go_to_editor(self):
        editor_ui = MainUserUi()
        win = self.window()
        if isinstance(win, QMainWindow):
            win.setCentralWidget(editor_ui)

    def open_eqcorrect_plugin(self):
        shell_eqcorrect_plugin = ShellEqcorrectPlugin(
            parent=self
        )
        shell_eqcorrect_plugin.audio_playlist = [x[1] for x in self.current_playlist]
        shell_eqcorrect_plugin.exec()

    def add_video_to_playlist(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open a video file", "", "All files (*)")
        if not filename:
            return
        self.current_playlist.append((str(filename), ""))

    def config_audio_to_video(self):
        current_selected_index = self.video_list.currentRow()
        if current_selected_index < 0:
            return
        filename, _ = QFileDialog.getOpenFileName(self, "Open a video file", "", "All files (*)")
        if not filename:
            return
        new_item = (self.current_playlist[current_selected_index][0], str(filename))
        self.current_playlist.update(
            index=current_selected_index, item=new_item
        )

    def delete_video_to_playlist(self):
        current_selected_index = self.video_list.currentRow()
        if current_selected_index < 0:
            return
        self.current_playlist.delete(index=current_selected_index)

    def explode_video(self):
        current_selected_index = self.video_list.currentRow()
        new_item = AudioProcessing.explode_mov(original_mov_path=self.current_playlist[current_selected_index][0])
        self.current_playlist.update(
            index=current_selected_index, item=new_item
        )

    def merge_audio(self):
        current_selected_index = self.video_list.currentRow()
        new_item = AudioProcessing.merge_wav(
            wav_audio_path=self.current_playlist[current_selected_index][1],
            mov_movie_path=self.current_playlist[current_selected_index][0]
        )
        self.current_playlist.update(
            index=current_selected_index, item=new_item
        )

    def move_playlist_up(self):
        current_selected_index = self.video_list.currentRow()
        if current_selected_index <= 0:
            return
        self.current_playlist.move(
            from_index=current_selected_index, 
            to_index=current_selected_index - 1
        )
        self.audio_list.setCurrentRow(current_selected_index - 1)

    def move_playlist_down(self):
        current_selected_index = self.video_list.currentRow()
        if current_selected_index >= len(self.current_playlist) - 1:
            return
        self.current_playlist.move(
            from_index=current_selected_index, 
            to_index=current_selected_index + 1
        )
        self.audio_list.setCurrentRow(current_selected_index + 1)

    def _resolve_path_notation(self, 
                               k: str,
                               my_dir: str
                               ):
        if k.startswith("URL==="):
            k_splitted = k.split("===")
            if len(k_splitted) != 3:
                k = ""
            else:
                url = k_splitted[1]
                download_target_path = k_splitted[2].replace("$SELF$", my_dir)
                download_popup_dialog = DownloadPopupDialog(self)
                download_popup_dialog.download_from_urls(
                    to_download_dict={url : download_target_path}
                )
                download_popup_dialog.exec()
                k = download_target_path
        else:
            k = k.replace("$SELF$", my_dir)
        return k


    def open_playlist(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open playlist", "", "sjplay file (*.sjplay)")
        if not filename:
            return
        with open(filename, "r", encoding="utf-8") as f:
            sjlist = json.load(f)
        for k, v in sjlist.items():
            my_dir = str(Path(filename).resolve().parent)
            self.current_playlist.append(
                (self._resolve_path_notation(k=k, my_dir=my_dir), self._resolve_path_notation(k=v, my_dir=my_dir))
            )


    def save_playlist(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save file", "", "sjplay file (*.sjplay)")
        if not filename:
            return
        if "." in filename:
            filename = f"{filename.split(".")[0]}.sjplay"
        sjplay = {}
        for x in self.current_playlist:
            sjplay[x[0]] = x[1]
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(sjplay, f, ensure_ascii=False, indent=2)

        

    def sync_audio_config_selection_to_video(self):
        current_selected_video_row = self.video_list.currentRow()
        self.audio_list.setCurrentRow(current_selected_video_row)

    def sync_video_selection_to_audio_config(self):
        current_selected_audio_row = self.audio_list.currentRow()
        self.video_list.setCurrentRow(current_selected_audio_row)

    def toggle_video_muting(self):
        self.main_player_window_widget.mute_video(do_mute_video=self.do_mute_video_check.isChecked())

    def toggle_audio_muting(self):
        self.main_player_window_widget.mute_audio(do_mute_audio=self.do_mute_audio_check.isChecked())

    def set_mpv_player(self):
        if self.set_btn.text() == "Set":
            self.set_player()
        else:
            self.unset_player()

    def set_player(self):
        if self.do_normalize_loudness_check.isChecked():
            norm_coe_dict = AudioProcessing.norm_loudness(
                paths=[x[0] for x in list(self.current_playlist)] + [x[1] for x in list(self.current_playlist)]
            )
            self.main_player_window_widget.norm_loudness_coe = norm_coe_dict
            print(norm_coe_dict)
        else:
            self.main_player_window_widget.norm_loudness_coe = {}
        self.video_list.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.video_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.audio_list.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.audio_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_player_window_widget.playlist = list(self.current_playlist)
        self.main_player_window_widget.audio_channels = self.audio_channel_input.text().strip()
        self.main_player_window_widget.is_prepared = True
        self.main_player_window_widget.set_media(index=0)
        self.main_player_window_widget.video_audio_outputer.setDevice(self.audio_devices_dict[self.audio_device_selection_combo.currentText()])
        self.main_player_window_widget.audio_audio_outputer.setDevice(self.audio_devices_dict[self.audio_device_selection_combo.currentText()])
        self.main_player_window_widget.do_mute_video = self.do_mute_video_check.isChecked()
        self.main_player_window_widget.do_mute_audio = self.do_mute_audio_check.isChecked()
        self.play_btn.show(); self.play_btn.setEnabled(True)
        self.reload_and_play_btn.show(); self.reload_and_play_btn.setEnabled(True)
        self.pause_btn.show(); self.pause_btn.setEnabled(False)
        self.back_btn.show(); self.back_btn.setEnabled(False)
        self.proceed_btn.show(); self.proceed_btn.setEnabled(True)
        self.return_btn.show(); self.return_btn.setEnabled(True)
        self.use_web_btn.show(); self.use_web_btn.setEnabled(True)
        self.qrcode_image_label.show()
        self.debug_shift_slider.show()
        self.video_pos_label.show()
        self.audio_pos_label.show()
        self.video_pos_input.show()
        self.audio_pos_input.show()
        self.debug_shift_label.show()
        self.debug_shift_slider.setValue(0)
        self.set_btn.setText("Unset")

    def unset_player(self):
        self.main_player_window_widget.pause_media()
        self.video_list.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.video_list.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.audio_list.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.audio_list.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.main_player_window_widget.playlist = []
        self.main_player_window_widget.is_prepared = False
        self.play_btn.hide(); self.play_btn.setEnabled(False)
        self.reload_and_play_btn.hide(); self.reload_and_play_btn.setEnabled(False)
        self.pause_btn.hide(); self.pause_btn.setEnabled(False)
        self.back_btn.hide(); self.back_btn.setEnabled(False)
        self.proceed_btn.hide(); self.proceed_btn.setEnabled(False)
        self.return_btn.hide(); self.return_btn.setEnabled(False)
        self.use_web_btn.hide(); self.use_web_btn.setEnabled(False)
        self.qrcode_image_label.hide()
        self.debug_shift_slider.hide()
        self.video_pos_label.hide()
        self.audio_pos_label.hide()
        self.video_pos_input.hide()
        self.audio_pos_input.hide()
        self.debug_shift_label.hide()
        self.set_btn.setText("Set")

    def display_video(self):
        w = self.main_player_window_widget
        display_selected = self.screen_dict[self.display_selection_combo.currentText()]
        w.setScreen(display_selected)
        w.move(display_selected.geometry().topLeft())  
        w.showFullScreen()
        w.raise_()
        w.activateWindow()

    def play_player(self, do_reload: bool=False):
        if do_reload:
            self.main_player_window_widget.playlist = list(self.current_playlist)
            self.main_player_window_widget.set_media(index=None)
            self.main_player_window_widget.audio_player.setPosition(int(self.shift_audio_forward_input.text()))
        self.play_btn.setEnabled(False)
        self.reload_and_play_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.back_btn.setEnabled(True)
        self.proceed_btn.setEnabled(True)
        self.return_btn.setEnabled(True)
        self.main_player_window_widget.play_media()

    def pause_player(self):
        self.play_btn.setEnabled(True)
        self.reload_and_play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.back_btn.setEnabled(True)
        self.proceed_btn.setEnabled(True)
        self.return_btn.setEnabled(True)
        self.main_player_window_widget.pause_media()

    def player_back_to_start(self):
        self.main_player_window_widget.playlist = list(self.current_playlist)
        self.main_player_window_widget.set_media(index=None)
        self.play_btn.setEnabled(True)
        self.reload_and_play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.back_btn.setEnabled(False)
        self.proceed_btn.setEnabled(True)
        self.return_btn.setEnabled(True)
        self.main_player_window_widget.back_to_start()

    def move_playlist(self, movement: int=1):
        self.play_btn.setEnabled(True)
        self.reload_and_play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.back_btn.setEnabled(False)
        self.proceed_btn.setEnabled(True)
        self.return_btn.setEnabled(True)
        self.main_player_window_widget.move_playlist(movement=movement)


    def on_media_pos_changed(self, positions: tuple[int, int, int]):
        self.debug_shift_slider.setValue(int(positions[0]))
        self.debug_shift_label.setText(f"Shift : {positions[0]}")
        self.video_pos_input.setText(f"{positions[1]}")
        self.audio_pos_input.setText(f"{positions[2]}")
        is_alert = positions[0] < self.low_tolerence or positions[0] > self.up_tolerence
        if self.debug_shift_slider.property("alert") != is_alert:
            self.debug_shift_slider.setProperty("alert", is_alert)
            self.debug_shift_slider.style().unpolish(self.debug_shift_slider)
            self.debug_shift_slider.style().polish(self.debug_shift_slider)

    def define_tolerence(self, standard: str):
        if standard == "ITU-R BT.1359-1":
            self.low_tolerence = -125
            self.up_tolerence = 45
        elif standard == "EBU R37":
            self.low_tolerence = -60
            self.up_tolerence = 40
        elif standard == "ATSC IS-191":
            self.low_tolerence = -45
            self.up_tolerence = 15

    def on_playlist_index_changed(self, current_index: int, media_duration: int):
        self.video_list.setCurrentRow(current_index)
        self.audio_list.setCurrentRow(current_index)

    def sync_all_media_timeline_input(self):
        val = int(self.sender().text())
        if self.sender() != self.audio_pos_input: self.audio_pos_input.setText(str(val))
        if self.sender() != self.video_pos_input: self.video_pos_input.setText(str(val))
        self.main_player_window_widget.set_pos(val)
        self.debug_shift_label.setText("0")

    def start_web_server(self):
        self.flask_thread = Thread(target=run_web_remote, daemon=True)
        self.flask_thread.start()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = "127.0.0.1"
        finally:
            s.close()
        qrcode_img = qrcode.make(f"http://{ip}:5000")
        with tempfile.TemporaryDirectory() as temp_dir:
            qrcode_path = os.path.join(temp_dir, "qrcode.png")
            qrcode_img.save(qrcode_path)
            qrcode_pixmap = QPixmap(qrcode_path).scaled(
                180, 180, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self.qrcode_image_label.setPixmap(qrcode_pixmap)
        self.qrcode_image_label.show()
        self.use_web_btn.setText("End Web Remote")

    def terminate_web_server(self):
        ...
        self.qrcode_image_label.hide()
        self.use_web_btn.setText("Start Web Remote")

    def use_web_server(self):
        if self.use_web_btn.text() == "Start Web Remote":
            self.start_web_server()
        else:
            self.terminate_web_server()

    @Slot(RequestType)
    def web_request_handler(self, request_type: RequestType):
        if request_type == RequestType.PLAY:
            self.play_player(do_reload=False)
        elif request_type == RequestType.PAUSE:
            self.pause_player()
        elif request_type == RequestType.PROCEED:
            self.move_playlist(movement=1)
        elif request_type == RequestType.RETURN:
            self.move_playlist(movement=-1)

    @Slot(str)
    def scheduler_command_handler(self, command: str):
        print(defined_alias.get(command, command))
        exec(defined_alias.get(command, command))



