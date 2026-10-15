import os
import stat
from pathlib import Path

from PySide6.QtCore import Qt, QProcess, QTimer, QUrl, QSize
from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit,
    QHBoxLayout, QPushButton, QFileDialog,
    QLabel, QMessageBox, QProgressBar, QWidget
)


class SpinnerWidget(QWidget):
    """くるくる回るスピナー。start() で回転開始、stop() で停止して非表示。"""

    def __init__(self, parent=None, size=20):
        super().__init__(parent)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.setInterval(30)
        self._timer.timeout.connect(self._advance)
        self.setFixedSize(QSize(size, size))
        self.hide()

    def start(self):
        self._timer.start()
        self.show()

    def stop(self):
        self._timer.stop()
        self.hide()

    def _advance(self):
        self._angle = (self._angle + 12) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(self.palette().highlight().color(), 3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        margin = 3
        rect = self.rect().adjusted(margin, margin, -margin, -margin)
        # drawArc の角度は 1/16 度単位。90度分の円弧を回転させる
        painter.drawArc(rect, -self._angle * 16, 270 * 16)


class ShellEqcorrectPlugin(QDialog):

    DOWNLOAD_URL = "https://pub-7745c6e91aa147a0b81b964b501997b3.r2.dev/share/eqcorrect"

    def __init__(self, 
                 parent=None
                 ):
        super().__init__(parent)
        self.setAutoFillBackground(False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # --- 非同期処理用オブジェクト ---
        self.process = None            # QProcess（実行中のみ保持）
        self.net_manager = QNetworkAccessManager(self)
        self.download_reply = None
        self.download_file = None
        self.download_target_path = None
        self.audio_playlist = []

        dialog_lo = QVBoxLayout()

        self.executable_path = None
        exe_path_select_lo = QHBoxLayout()
        self.exe_path_select_btn = QPushButton("Select executable")
        self.exe_path_select_btn.clicked.connect(self.select_exe)
        exe_path_select_lo.addWidget(self.exe_path_select_btn)
        self.exe_path_download_btn = QPushButton("Download executable")
        self.exe_path_download_btn.clicked.connect(self.download_exe)
        exe_path_select_lo.addWidget(self.exe_path_download_btn)
        dialog_lo.addLayout(exe_path_select_lo)
        self.exe_path_label = QLabel("Executable path : --")
        dialog_lo.addWidget(self.exe_path_label)

        # ダウンロード進捗バー（ダウンロード中のみ表示）
        self.download_progress = QProgressBar()
        self.download_progress.setRange(0, 100)
        self.download_progress.setValue(0)
        self.download_progress.hide()
        dialog_lo.addWidget(self.download_progress)

        dialog_lo.addStretch()

        load_btns_lo = QHBoxLayout()
        use_playlist_as_audio = QPushButton("Use Playlist")
        use_playlist_as_audio.clicked.connect(self.use_play_list)
        load_btns_lo.addWidget(use_playlist_as_audio)
        open_audio_file = QPushButton("Add Audio")
        open_audio_file.clicked.connect(self.open_audio_file)
        self.audio_file_paths = []
        load_btns_lo.addWidget(open_audio_file)
        open_req_files = QPushButton("Open REQ")
        open_req_files.clicked.connect(self.open_req_files)
        self.req_files_path = None
        load_btns_lo.addWidget(open_req_files)
        select_out_dir_btn = QPushButton("Out dir")
        select_out_dir_btn.clicked.connect(self.select_out_dir)
        self.out_dir = None
        load_btns_lo.addWidget(select_out_dir_btn)
        dialog_lo.addLayout(load_btns_lo)

        self.audio_file_label = QLabel("Audio : --")
        dialog_lo.addWidget(self.audio_file_label)
        self.req_files_label = QLabel("REQ : --")
        dialog_lo.addWidget(self.req_files_label)
        self.out_dir_label = QLabel("Out : --")
        dialog_lo.addWidget(self.out_dir_label)

        self.options_input = QLineEdit("")
        self.options_input.setPlaceholderText("Options")
        dialog_lo.addWidget(self.options_input)

        dialog_lo.addStretch()

        # 実行ボタン + スピナー + ステータス
        self.exec_btn = QPushButton("Execute Shell EQcorrect")
        self.exec_btn.clicked.connect(self.exec_shell_eqcorrect)
        dialog_lo.addWidget(self.exec_btn)

        status_lo = QHBoxLayout()
        self.spinner = SpinnerWidget(self)
        status_lo.addWidget(self.spinner)
        self.status_label = QLabel("")
        status_lo.addWidget(self.status_label)
        status_lo.addStretch()
        dialog_lo.addLayout(status_lo)

        self.setLayout(dialog_lo)

    # ------------------------------------------------------------------
    # ファイル選択
    # ------------------------------------------------------------------
    
    def select_exe(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open an executable file", "", "Executable file (*)")
        if not filename:
            return
        self.exe_path_label.setText(f"Executable path : {filename}")
        self.executable_path = filename

    def use_play_list(self):
        self.audio_file_paths = self.audio_playlist
        if len(self.audio_file_paths) > 1:
            self.audio_file_label.setText(f"Audio : {self.audio_file_paths[0]} ,etc")
        elif len(self.audio_file_paths) == 1:
            self.audio_file_label.setText(f"Audio : {self.audio_file_paths[0]}")
        self.out_dir = str(Path(self.audio_file_paths[0]).resolve().parent)
        self.out_dir_label.setText(f"Out : {self.out_dir}")

    def open_audio_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open an audio file", "", "Audio file (*)")
        if not filename:
            return
        self.audio_file_paths.append(filename)
        if len(self.audio_file_paths) > 1:
            self.audio_file_label.setText(f"Audio : {self.audio_file_paths[0]} ,etc")
        elif len(self.audio_file_paths) == 1:
            self.audio_file_label.setText(f"Audio : {self.audio_file_paths[0]}")

    def open_req_files(self):
        req_dir = QFileDialog.getExistingDirectory(self, "Select a folder")
        if not req_dir:
            return
        self.req_files_path = req_dir
        self.req_files_label.setText(f"REQ : {self.req_files_path}")

    def select_out_dir(self):
        out_dir = QFileDialog.getExistingDirectory(self, "Select a folder")
        if not out_dir:
            return
        self.out_dir = out_dir
        self.out_dir_label.setText(f"Out : {self.out_dir}")


    def download_exe(self):
        if self.download_reply is not None:
            return
        dl_target_dir = QFileDialog.getExistingDirectory(self, "Select a folder")
        if not dl_target_dir:
            return

        self.download_target_path = Path(dl_target_dir) / "eqcorrect.exe"
        self.download_file = open(self.download_target_path, "wb")

        request = QNetworkRequest(QUrl(self.DOWNLOAD_URL))
        request.setAttribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy,
        )
        self.download_reply = self.net_manager.get(request)
        self.download_reply.readyRead.connect(self._on_download_ready_read)
        self.download_reply.downloadProgress.connect(self._on_download_progress)
        self.download_reply.finished.connect(self._on_download_finished)

        self.download_progress.setRange(0, 0)  # サイズ判明まではビジー表示
        self.download_progress.show()
        self.exe_path_download_btn.setEnabled(False)
        self.exe_path_select_btn.setEnabled(False)

    def _on_download_ready_read(self):
        # 全体をメモリに溜めず、届いた分だけ逐次ファイルに書く
        if self.download_reply and self.download_file:
            self.download_file.write(self.download_reply.readAll().data())

    def _on_download_progress(self, received, total):
        if total > 0:
            self.download_progress.setRange(0, 100)
            self.download_progress.setValue(int(received * 100 / total))
        else:
            self.download_progress.setRange(0, 0) 

    def _on_download_finished(self):
        reply = self.download_reply
        self.download_reply = None

        if self.download_file:
            self.download_file.close()
            self.download_file = None

        self.download_progress.hide()
        self.exe_path_download_btn.setEnabled(True)
        self.exe_path_select_btn.setEnabled(True)

        if reply.error() != QNetworkReply.NetworkError.NoError:
            error_text = reply.errorString()
            reply.deleteLater()
            try:
                self.download_target_path.unlink(missing_ok=True)
            except OSError:
                pass
            QMessageBox.critical(self, "Download failed", error_text)
            return

        reply.deleteLater()
        self.exe_path_label.setText(f"Executable path : {self.download_target_path}")
        self.executable_path = str(self.download_target_path)

    def exec_shell_eqcorrect(self):
        if self.process is not None:
            return 
        if self.executable_path is None or not self.audio_file_paths \
                or self.req_files_path is None or self.out_dir is None:
            return

        if os.name != "nt":
            mode = os.stat(self.executable_path).st_mode
            os.chmod(self.executable_path, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        self._queue = list(self.audio_file_paths)
        self._total = len(self._queue)
        self._done_count = 0
        self._failed = False
        self.exec_btn.setEnabled(False)
        self.spinner.start()
        self._start_next()

    def _finish_running_state(self):
        self.spinner.stop()
        self.exec_btn.setEnabled(True)

    def _start_next(self):
        if not self._queue:
            self._on_all_finished()
            return

        audio_file_path = self._queue.pop(0)
        self._done_count += 1
        options = self.options_input.text().strip()
        outfile_path = Path(self.out_dir) / f"{Path(audio_file_path).stem}.wav"
        original_renamed_path = Path(audio_file_path).resolve().parent / f"{Path(audio_file_path).stem}_original.wav"
        i = 1
        while original_renamed_path.exists():
            original_renamed_path = Path(audio_file_path).resolve().parent / f"{Path(audio_file_path).stem}_original_{i}.wav"
            i += 1
        os.rename(audio_file_path, str(original_renamed_path))

        args = [str(original_renamed_path), str(self.req_files_path), "-o", str(outfile_path)]
        if options:
            args.extend(options.split(" "))
        args.append("--protect-clip")

        proc = QProcess(self)
        self.process = proc
        proc.finished.connect(lambda code, status, p=proc: self._on_process_finished(p, code, status))
        proc.errorOccurred.connect(lambda err, p=proc: self._on_process_error(p, err))
        self.status_label.setText(f"Running {self._done_count} of {self._total}...")
        proc.start(str(self.executable_path), args)

    def _on_process_finished(self, proc, exit_code, exit_status):
        if proc is not self.process:
            return
        self.process = None
        stdout = bytes(proc.readAllStandardOutput()).decode(errors="replace")
        stderr = bytes(proc.readAllStandardError()).decode(errors="replace")
        proc.deleteLater()

        if exit_status != QProcess.ExitStatus.NormalExit or exit_code != 0:
            self._queue.clear()
            self._finish_running_state()
            self.status_label.setText(f"Failed (exit code {exit_code})")
            QMessageBox.critical(self, "Execution failed", stderr or stdout or f"Exit code: {exit_code}")
            return
        self._start_next()

    def _on_all_finished(self):
        self._finish_running_state()
        self.status_label.setText("Done")
        QMessageBox.information(self, "Execution finished", "Execution finished")

    def _on_process_error(self, proc, error):
        if error != QProcess.ProcessError.FailedToStart:
            return
        if proc is not self.process:
            return
        self.process = None
        message = proc.errorString()
        proc.deleteLater()
        self._queue.clear()
        self._finish_running_state()
        self.status_label.setText("Failed to start")
        QMessageBox.critical(self, "Execution failed", message)