import math
import time
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
                 do_mute_video=True,
                 do_mute_audio=False,
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
        self.do_mute_audio = do_mute_audio
        self.norm_loudness_coe = {}

        # [Added] Per-material timing shift state (see the "timing shift" section below).
        self._pending_ms = {"video": 0, "audio": 0}   # start delay still to wait (ms)
        self._delay_timers = {}                       # kind -> running single-shot QTimer
        self._delay_t0 = {}                           # kind -> time.monotonic() when that timer started
        self._seek_on_load = {}                       # kind -> position to apply once the media is loaded
        self.video_player.mediaStatusChanged.connect(self._on_video_status)
        self.audio_player.mediaStatusChanged.connect(self._on_audio_status)

        self.media_timer = QTimer()
        self.media_timer.setInterval(300)
        self.media_timer.timeout.connect(self.sync_audio)
        self.media_timer.start()

    def sync_audio(self, threshold: int=100000):
        if not self.is_prepared: return
        if not self.video_player.isPlaying() or not self.audio_player.isPlaying(): return
        video_pos = self.video_player.position()
        audio_pos = self.audio_player.position()
        # [Changed] The per-material shifts make (audio_pos - video_pos) intentionally
        # non-zero.  Drift is measured against that intended difference; with both
        # shifts at 0 this is exactly the old behaviour.
        vs, as_ = self._entry_shifts()
        expected = as_ - vs
        diff = abs((audio_pos - video_pos) - expected)
        if diff >= threshold:
            self.audio_player.setPosition(max(0, video_pos + expected))
        debugger_val = int((audio_pos - video_pos) - expected)
        self.media_pos_changed_sig.emit((debugger_val, video_pos, audio_pos))

    def set_media(self, index: int | None):
        if not self.is_prepared or self.playlist is None: return
        if index is not None:
            if index >= len(self.playlist): return
        if index is not None:
            self.current_index = index
        video_path = self.playlist[self.current_index][0]
        audio_path = self.playlist[self.current_index][1]
        if video_path and Path(video_path).exists():
            self.video_player.pause()
            self.video_player.setPosition(0)
            self.video_player.setSource(QUrl.fromLocalFile(video_path))
            self.video_audio_outputer.setMuted(self.do_mute_video)
            if not self.do_mute_video and self.norm_loudness_coe:
                self.video_audio_outputer.setVolume(self.norm_loudness_coe.get(audio_path, 1.0))
            self.is_video_available = True
        if audio_path and Path(audio_path).exists():
            self.audio_player.setPosition(0)
            self.audio_player.pause()
            self.audio_player.setSource(QUrl.fromLocalFile(audio_path))
            if self.norm_loudness_coe:
                self.audio_audio_outputer.setVolume(self.norm_loudness_coe.get(audio_path, 1.0))
            self.is_audio_available = True
        self._seek_timeline(0)      # [Added] start positions / start delays for this material's shifts
        self.playlist_index_changed_sig.emit(
            self.current_index, min(self.video_player.duration(), self.audio_player.duration())
        )

    def play_media(self):
        if not self.is_prepared or self.playlist is None: return
        # [Changed] A material whose shift is negative starts after a delay; every
        # other player starts immediately exactly as before.
        for kind, player in self._active_players():
            remaining = self._pending_ms.get(kind, 0)
            if remaining > 0:
                self._start_delayed(kind, player, remaining)
            else:
                player.play()

    def pause_media(self):
        if not self.is_prepared or self.playlist is None: return
        self._freeze_delays()       # [Added] remember how long a delayed start still had to wait
        if self.is_video_available: self.video_player.pause()
        if self.is_audio_available: self.audio_player.pause()

    def back_to_start(self):
        if not self.is_prepared or self.playlist is None: return
        self._seek_timeline(0)      # [Changed] was: setPosition(0) on both (same when shifts are 0)

    def move_playlist(self, movement: int=1):
        if not self.is_prepared or self.playlist is None: return
        new_index = self.current_index + movement
        if new_index < 0 or new_index >= len(self.playlist): return
        self.set_media(index=new_index)

    def set_pos(self, newpos: int):
        if newpos > self.video_player.duration() or newpos > self.audio_player.duration():
            return
        # [Changed] ``newpos`` is the video position (audio position if there is no video);
        # the other material follows according to the shifts.  With shifts at 0 both get
        # ``newpos`` as before.  (The old code tested ``is_audio_available`` twice, so a
        # video-only item was never seeked.)
        self._freeze_delays()
        if self.is_video_available: self.video_player.pause()
        if self.is_audio_available: self.audio_player.pause()
        vs, as_ = self._entry_shifts()
        if self.is_video_available:
            self._seek_timeline(newpos - vs)
        elif self.is_audio_available:
            self._seek_timeline(newpos - as_)

    # ------------------------------------------------------------------
    # [Added] Timing shift (per material, in ms)
    #
    # Common timeline T (ms since the start of the item).  A material with shift
    # ``s`` is at position ``T + s``:   s > 0 -> plays earlier (first s ms skipped),
    #                                   s < 0 -> plays later   (starts |s| ms after T=0).
    # With both shifts 0 every position equals T, i.e. the old behaviour.
    # ------------------------------------------------------------------
    # Media states in which setPosition() takes effect immediately.
    _LOADED = (QMediaPlayer.MediaStatus.LoadedMedia, QMediaPlayer.MediaStatus.BufferedMedia,
               QMediaPlayer.MediaStatus.EndOfMedia)
    # States that announce "loading finished" (used to apply a seek requested too early).
    _JUST_LOADED = (QMediaPlayer.MediaStatus.LoadedMedia, QMediaPlayer.MediaStatus.BufferedMedia)

    def _entry_shifts(self) -> tuple[int, int]:
        """(video_shift_ms, audio_shift_ms) of the current playlist item (0, 0 if none)."""
        try:
            e = self.playlist[self.current_index]
        except (TypeError, IndexError):
            return 0, 0
        return int(getattr(e, "video_shift_ms", 0)), int(getattr(e, "audio_shift_ms", 0))

    def _active_players(self):
        out = []
        if self.is_video_available: out.append(("video", self.video_player))
        if self.is_audio_available: out.append(("audio", self.audio_player))
        return out

    def _cancel_delays(self):
        for t in self._delay_timers.values():
            t.stop()
        self._delay_timers.clear()
        self._delay_t0.clear()

    def _remaining(self, kind: str) -> float:
        """Delay (ms) that ``kind`` still has to wait before it starts."""
        rem = float(self._pending_ms.get(kind, 0))
        if kind in self._delay_timers:
            rem -= (time.monotonic() - self._delay_t0[kind]) * 1000.0
        return max(0.0, rem)

    def _freeze_delays(self):
        """Stop running delay timers, keeping the time each one still had to wait."""
        for kind in list(self._delay_timers):
            self._pending_ms[kind] = int(round(self._remaining(kind)))
            self._delay_timers.pop(kind).stop()
            self._delay_t0.pop(kind, None)

    def _start_delayed(self, kind: str, player, ms: float):
        if kind in self._delay_timers:
            return                      # already waiting (e.g. Play pressed twice)
        t = QTimer(self)
        t.setSingleShot(True)
        t.setTimerType(Qt.TimerType.PreciseTimer)
        t.timeout.connect(self._on_video_delay_done if kind == "video" else self._on_audio_delay_done)
        self._delay_timers[kind] = t
        self._delay_t0[kind] = time.monotonic()
        t.start(int(round(ms)))

    def _on_video_delay_done(self):
        self._delay_done("video", self.video_player)

    def _on_audio_delay_done(self):
        self._delay_done("audio", self.audio_player)

    def _delay_done(self, kind: str, player):
        self._delay_timers.pop(kind, None)
        self._delay_t0.pop(kind, None)
        self._pending_ms[kind] = 0
        player.play()

    def _seek(self, kind: str, player, pos: int):
        """setPosition now; if the media is not loaded yet, also re-apply when it is."""
        pos = int(pos)
        player.setPosition(pos)
        if player.mediaStatus() in self._LOADED:
            self._seek_on_load.pop(kind, None)
        else:
            self._seek_on_load[kind] = pos

    def _on_video_status(self, status):
        self._apply_seek_on_load("video", self.video_player, status)

    def _on_audio_status(self, status):
        self._apply_seek_on_load("audio", self.audio_player, status)

    def _apply_seek_on_load(self, kind: str, player, status):
        if status in self._JUST_LOADED and kind in self._seek_on_load:
            player.setPosition(self._seek_on_load.pop(kind))

    def _seek_timeline(self, T: int, extra_audio: int = 0):
        """Put every material at timeline time ``T`` (without starting playback).

        A material whose position would be negative is parked at 0 with a start delay.
        ``extra_audio`` is an additional one-shot audio shift (the old "Shift Audio" box).
        """
        self._cancel_delays()
        self._pending_ms = {"video": 0, "audio": 0}
        vs, as_ = self._entry_shifts()
        shifts = {"video": vs, "audio": as_ + int(extra_audio)}
        for kind, player in self._active_players():
            p = int(T) + shifts[kind]
            if p >= 0:
                self._seek(kind, player, p)
            else:
                self._pending_ms[kind] = -p
                self._seek(kind, player, 0)

    def _current_T(self) -> int:
        """Current timeline time, taken from a material that has already started."""
        vs, as_ = self._entry_shifts()
        shifts = {"video": vs, "audio": as_}
        players = self._active_players()
        for kind, player in players:
            if self._remaining(kind) <= 0:
                return int(player.position()) - shifts[kind]
        for kind, player in players:        # nobody started yet: derive T from the waiting time
            return int(round(-(self._remaining(kind) + shifts[kind])))
        return 0

    def nudge_audio_start(self, ms: int):
        """One-shot extra audio shift used by "Load and Play" (the old "Shift Audio" box)."""
        if ms:
            self._seek_timeline(0, extra_audio=int(ms))

    def change_shift(self, entry, kind: str, ms: int) -> bool:
        """Set ``kind`` ("video"/"audio") shift of ``entry`` to ``ms`` and send it to the player.

        If ``entry`` is the item currently loaded in a prepared player, the timeline
        position is kept: playback is paused, both materials are re-aligned, and playback
        resumes if it was running.  Otherwise the value is just stored and used the next
        time the item is loaded.  Returns True if the live player was re-aligned.
        """
        attr = f"{kind}_shift_ms"
        ms = int(ms)
        try:
            current = self.playlist[self.current_index]
        except (TypeError, IndexError):
            current = None
        if not (self.is_prepared and current is entry):
            setattr(entry, attr, ms)
            return False
        T = self._current_T()
        was_playing = bool(self._delay_timers) or self.video_player.isPlaying() or self.audio_player.isPlaying()
        self.pause_media()
        setattr(entry, attr, ms)
        self._seek_timeline(T)
        if was_playing:
            self.play_media()
        return True

    def mute_video(self, do_mute_video: bool):
        self.do_mute_video = do_mute_video
        self.video_audio_outputer.setMuted(self.do_mute_video)

    def mute_audio(self, do_mute_audio: bool):
        self.do_mute_audio = do_mute_audio
        self.audio_audio_outputer.setMuted(self.do_mute_audio)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

