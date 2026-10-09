from collections import UserList

from PySide6.QtWidgets import QFileDialog

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
    def add_video_to_playlist(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open a video file", "", "All files (*)")
        if not filename:
            return
        self.current_playlist.append((str(filename), ""))

    def config_audio_to_video(self):
        current_selected_index = self.video_list.currentRow()
        if current_selected_index <= 0:
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
        if current_selected_index <= 0:
            return
        self.current_playlist.delete(index=current_selected_index)

    def move_playlist_up(self):
        current_selected_index = self.video_list.currentRow()
        if current_selected_index <= 0:
            return
        self.current_playlist.move(
            from_index=current_selected_index, 
            to_index=current_selected_index - 1
        )

    def move_playlist_down(self):
        current_selected_index = self.video_list.currentRow()
        if current_selected_index >= len(self.current_playlist) - 1:
            return
        self.current_playlist.move(
            from_index=current_selected_index, 
            to_index=current_selected_index + 1
        )

    def sync_audio_config_selection_to_video(self):
        current_selected_video_row = self.video_list.currentRow()
        self.audio_list.setCurrentRow(current_selected_video_row)

    def sync_video_selection_to_audio_config(self):
        current_selected_audio_row = self.audio_list.currentRow()
        self.video_list.setCurrentRow(current_selected_audio_row)