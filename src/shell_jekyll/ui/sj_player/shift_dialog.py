"""Timing-shift UI for the Player: a Shift+double-click aware list and the adjust dialog.

[Added] New module.

Sign convention (same for video and audio):
    +N ms  ->  the material plays N ms *earlier* ("advance"; the first N ms are skipped)
    -N ms  ->  the material plays N ms *later*   ("delay"; it starts N ms after the other one)

The dialog only edits a number; the value is handed to the player when the user
presses "Apply" (signal ``shift_applied``).  Nothing is saved to disk.
"""
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QListWidget, QPushButton, QSpinBox, QVBoxLayout
)

SHIFT_RANGE_MS = 60000          # dialog accepts -60000 .. +60000 ms
STEP_BUTTONS = (-100, -10, -1, 1, 10, 100)
KIND_LABEL = {"video": "映像 / Video", "audio": "音声 / Audio"}


class GuardedListWidget(QListWidget):
    """QListWidget that can be *locked* against mouse input, except Shift+double-click.

    Replaces the old ``WA_TransparentForMouseEvents`` trick used while the player is
    "Set": a transparent widget never receives any event, so Shift+double-click
    could not be detected.  When locked, press/release/move/wheel are ignored
    (they fall through to the parent exactly like before); a double-click is
    delivered only when Shift is held, and then it emits ``shift_double_clicked(row)``.
    When unlocked, behaviour is the stock QListWidget plus the same Shift signal.
    """

    shift_double_clicked = Signal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._locked = False

    def set_locked(self, locked: bool):
        self._locked = bool(locked)

    def is_locked(self) -> bool:
        return self._locked

    def mousePressEvent(self, event):
        if self._locked:
            event.ignore()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self._locked:
            event.ignore()
            return
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self._locked:
            event.ignore()
            return
        super().mouseMoveEvent(event)

    def wheelEvent(self, event):
        if self._locked:
            event.ignore()
            return
        super().wheelEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            item = self.itemAt(event.position().toPoint())
            if item is not None:
                self.shift_double_clicked.emit(self.row(item))
                event.accept()
                return
        if self._locked:
            event.ignore()
            return
        super().mouseDoubleClickEvent(event)


class ShiftDialog(QDialog):
    """Modeless dialog to adjust the start timing (ms) of one playlist material.

    Modeless on purpose: the user has to press Play in the main window and listen
    while adjusting.  One instance is re-used (``retarget``) for every material.
    """

    shift_applied = Signal(object, str, int)     # (playlist entry, "video"|"audio", ms)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.entry = None
        self.kind = "video"
        self._applied_ms = 0
        self.setWindowTitle("Timing Adjust")
        self.setModal(False)

        lo = QVBoxLayout(self)
        self.target_label = QLabel("")
        self.target_label.setWordWrap(True)
        lo.addWidget(self.target_label)
        hint = QLabel("＋ = 早く再生（進める） / − = 遅れて再生（遅らせる）\n単位: ミリ秒 (ms)。Apply でプレイヤーに送ります。")
        hint.setWordWrap(True)
        lo.addWidget(hint)

        self.spin = QSpinBox()
        self.spin.setRange(-SHIFT_RANGE_MS, SHIFT_RANGE_MS)
        self.spin.setSingleStep(1)
        self.spin.setSuffix(" ms")
        self.spin.valueChanged.connect(self._refresh_status)
        lo.addWidget(self.spin)

        step_lo = QHBoxLayout()
        for d in STEP_BUTTONS:
            b = QPushButton(f"{d:+d}")
            b.clicked.connect(lambda _checked=False, d=d: self.spin.setValue(self.spin.value() + d))
            step_lo.addWidget(b)
        lo.addLayout(step_lo)

        self.status_label = QLabel("")
        lo.addWidget(self.status_label)

        btn_lo = QHBoxLayout()
        reset_btn = QPushButton("Reset (0)")
        reset_btn.clicked.connect(lambda _checked=False: self.spin.setValue(0))
        btn_lo.addWidget(reset_btn)
        self.apply_btn = QPushButton("Apply (send to player)")
        self.apply_btn.setDefault(True)
        self.apply_btn.clicked.connect(self.apply)
        btn_lo.addWidget(self.apply_btn)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_lo.addWidget(close_btn)
        lo.addLayout(btn_lo)

    def retarget(self, entry, kind: str, path: str, current_ms: int = 0):
        """Point the dialog at another material (``kind`` is "video" or "audio")."""
        self.entry = entry
        self.kind = kind
        self._applied_ms = int(current_ms)
        self.setWindowTitle(f"Timing Adjust — {KIND_LABEL.get(kind, kind)}")
        self.target_label.setText(f"{KIND_LABEL.get(kind, kind)}:  {Path(path).name}")
        self.target_label.setToolTip(path)
        self.spin.setValue(int(current_ms))
        self._refresh_status()

    def apply(self):
        if self.entry is None:
            return
        self._applied_ms = int(self.spin.value())
        self.shift_applied.emit(self.entry, self.kind, self._applied_ms)
        self._refresh_status()

    def _refresh_status(self, *_):
        v = int(self.spin.value())
        if v == self._applied_ms:
            self.status_label.setText(f"プレイヤーに送信済み: {self._applied_ms:+d} ms")
        else:
            self.status_label.setText(f"未送信の変更あり（送信済み {self._applied_ms:+d} ms → 入力 {v:+d} ms）")
