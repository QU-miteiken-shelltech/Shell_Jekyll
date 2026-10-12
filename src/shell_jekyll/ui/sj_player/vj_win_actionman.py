import json

from PySide6.QtCore import (
    Qt, QStringListModel, QDateTime,
    Signal, QObject, QTimer
)
from PySide6.QtWidgets import (
    QDialog, QListWidget, QVBoxLayout,
    QLineEdit, QCompleter, QHBoxLayout,
    QPushButton, QDateTimeEdit, QFileDialog
)
from PySide6.QtMultimedia import QMediaPlayer

defined_alias = {
    "<PLAY>" : "self.play_player(do_reload=False)",
    "<RELOAD>" : "self.play_player(do_reload=True)",
    "<PROCEED>" : "self.move_playlist(movement=1)",
    "<RETURN>" : "self.move_playlist(movement=-1)",
    "<SET>" : "self.set_player()",
    "<DISPLAY>" : "self.display_video()",
    "<UNSET>" : "self.unset_player()",
    "<PAUSE>" : "self.pause_player()",
    "<BACK>" : "self.player_back_to_start()",
    "<WAIT>" : "pass"
}

class ActionManagerBridge(QObject):
    command_issued_sig = Signal(str)

actionman_bridge = ActionManagerBridge()

class ActionManagerDialog(QDialog):

    def __init__(self, parent=None, player_widget=None):
        super().__init__(parent)
        self.setAutoFillBackground(False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.iterator = None
        self.player_widget = player_widget

        dialog_lo = QVBoxLayout()
        action_setting_lo = QHBoxLayout()

        actionman_lo = QVBoxLayout()
        self.task_list = QListWidget()
        self.task_list.setFixedHeight(350)
        actionman_lo.addWidget(self.task_list)

        self.add_action_input = QLineEdit()
        action_cmd_completer = QCompleter(self)
        action_cmd_completer.setModel(
            QStringListModel([k for k in defined_alias])
        )
        action_cmd_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.add_action_input.setCompleter(action_cmd_completer)
        actionman_lo.addWidget(self.add_action_input)

        btns_lo = QHBoxLayout()
        add_action_btn = QPushButton("Add")
        add_action_btn.clicked.connect(self.add_action)
        btns_lo.addWidget(add_action_btn)
        del_action_btn = QPushButton("Delete")
        del_action_btn.clicked.connect(self.delete_action)
        btns_lo.addWidget(del_action_btn)
        reset_action_btn = QPushButton("Reset")
        reset_action_btn.clicked.connect(self.reset_action)
        btns_lo.addWidget(reset_action_btn)
        actionman_lo.addLayout(btns_lo)
        action_setting_lo.addLayout(actionman_lo)

        schedule_lo = QVBoxLayout()
        self.schedule_list = QListWidget()
        self.schedule_list.setFixedHeight(350)
        schedule_lo.addWidget(self.schedule_list)

        self.time_selection_ui = QDateTimeEdit(QDateTime.currentDateTime(), self)
        self.time_selection_ui.setCalendarPopup(True)
        schedule_lo.addWidget(self.time_selection_ui)

        btns_lo2 = QHBoxLayout()
        add_schedule_btn = QPushButton("Add")
        add_schedule_btn.clicked.connect(self.add_schedule)
        btns_lo2.addWidget(add_schedule_btn)
        del_schedule_btn = QPushButton("Delete")
        del_schedule_btn.clicked.connect(self.delete_schedule)
        btns_lo2.addWidget(del_schedule_btn)
        reset_schedule_btn = QPushButton("Reset")
        reset_schedule_btn.clicked.connect(self.reset_schedule)
        btns_lo2.addWidget(reset_schedule_btn)
        schedule_lo.addLayout(btns_lo2)
        action_setting_lo.addLayout(schedule_lo)
        dialog_lo.addLayout(action_setting_lo)

        dialog_lo.addStretch()

        dialog_btns_lo = QHBoxLayout()
        self.execute_btn = QPushButton("Run Schedule")
        self.execute_btn.clicked.connect(self.execute_schedule)
        dialog_btns_lo.addWidget(self.execute_btn)
        self.is_in_schedule = False
        save_btn = QPushButton("Save Schedule")
        save_btn.clicked.connect(self.save_schedule)
        dialog_btns_lo.addWidget(save_btn)
        open_btn = QPushButton("Open Schedule")
        open_btn.clicked.connect(self.open_schedule)
        dialog_btns_lo.addWidget(open_btn)
        dialog_lo.addLayout(dialog_btns_lo)

        self.setLayout(dialog_lo)

    def add_action(self):
        action = self.add_action_input.text()
        if not action:
            return
        self.task_list.addItem(self.add_action_input.text())
        self.add_action_input.clear()

    def delete_action(self):
        selected_row = self.task_list.currentRow()
        self.task_list.takeItem(selected_row)

    def reset_action(self):
        new_action = self.add_action_input.text()
        if not new_action:
            return
        selected_item = self.task_list.currentItem()
        selected_item.setText(new_action)
        self.add_action_input.clear()

    def add_schedule(self):
        timing = self.time_selection_ui.dateTime()
        self.schedule_list.addItem(timing.toString())

    def delete_schedule(self):
        selected_row = self.schedule_list.currentRow()
        self.schedule_list.takeItem(selected_row)

    def reset_schedule(self):
        new_timing = self.time_selection_ui.dateTime()
        selected_item = self.schedule_list.currentItem()
        selected_item.setText(new_timing.toString())

    def execute_schedule(self):
        if not self.is_in_schedule:
            self.iterator = iter([self.task_list.item(i).text() for i in range(self.task_list.count())])
            self.execute_btn.setText("Kill Schedule")
            self.is_in_schedule = True
            self.next_step()
        else:
            self.execute_btn.setText("Run Schedule")
            self.is_in_schedule = False
            try:
                self.player_widget.video_player.mediaStatusChanged.disconnect(self._on_wait_media_end)
            except:
                print("Cannot disconnect")

    def open_schedule(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open a schedule file", "", "Schedule File (*.sjschedule)")
        if not filename:
            return
        with open(filename, "r", encoding="utf-8") as f:
            schedule = json.load(f)
        self.task_list.addItems(schedule.get("tasks", []))
        self.schedule_list.addItems(schedule.get("timings", []))

    def save_schedule(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save schedule file", "", "Schedule File (*.sjschedule)")
        if not filename:
            return
        schedule = {
            "tasks" : [self.task_list.item(i).text() for i in range(self.task_list.count())],
            "timings" : [self.schedule_list.item(i).text() for i in range(self.schedule_list.count())]
        }
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(schedule, f, ensure_ascii=False, indent=3)

    def _on_wait_media_end(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.player_widget.video_player.mediaStatusChanged.disconnect(self._on_wait_media_end)
            self.next_step()

    def next_step(self):
        try:
            command = next(self.iterator)

            if command == "<WAIT>":
                self.player_widget.video_player.mediaStatusChanged.connect(self._on_wait_media_end)
            else:
                actionman_bridge.command_issued_sig.emit(command)
                QTimer.singleShot(0, self.next_step)
                
        except StopIteration:
            print("Schedule completed")
