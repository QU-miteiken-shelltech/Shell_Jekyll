from pathlib import Path
from PySide6.QtCore import Qt, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QMessageBox, QProgressBar


class DownloadPopupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.net_manager = QNetworkAccessManager(self)
        self.download_reply = None
        self.download_file = None
        self.download_target_path = None
        self.audio_playlist = []
        self._queue = []

        dialog_lo = QVBoxLayout(self)          
        self.download_progress = QProgressBar()
        self.download_progress.setRange(0, 100)
        self.download_progress.setValue(0)
        dialog_lo.addWidget(self.download_progress)
        self.download_label = QLabel()
        dialog_lo.addWidget(self.download_label)

    def download_from_urls(self, to_download_dict: dict[str, str]):
        self._queue = list(to_download_dict.items())
        self._start_next()

    def _start_next(self):
        if not self._queue:
            self.accept()                   
            return
        url, path = self._queue.pop(0)
        print(url)
        self.download_target_path = Path(path)
        self.download_file = open(self.download_target_path, "wb")

        request = QNetworkRequest(QUrl(url))
        request.setAttribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy,
        )
        self.download_reply = self.net_manager.get(request)
        self.download_reply.readyRead.connect(self._on_download_ready_read)
        self.download_reply.downloadProgress.connect(self._on_download_progress)
        self.download_reply.finished.connect(self._on_download_finished)

        self.download_progress.setRange(0, 0)
        self.download_label.setText(f"Downloading : {url}")

    def _on_download_ready_read(self):
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

        if reply.error() != QNetworkReply.NetworkError.NoError:
            error_text = reply.errorString()
            reply.deleteLater()
            try:
                self.download_target_path.unlink(missing_ok=True)
            except OSError:
                pass
            self._queue.clear()
            QMessageBox.critical(self, "Download failed", error_text)
            self.reject()
            return

        reply.deleteLater()
        self._start_next()                      