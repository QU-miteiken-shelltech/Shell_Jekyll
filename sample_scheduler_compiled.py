import datetime.datetime
import time

def action_1():
    self.set_player()
    self.display_video()
    self.play_player()
    self.move_playlist(movement=1)
    self.play_player()
    time.sleep(5)
    self.move_playlist(movement=1)
    self.play_player()
    unset_player()

for t in ['20261011035', '202610101150']:
    t_now = datetime.now()
    t_scheduled = datetime.strptime(t, '%Y%m%d%H%M%S')
    remaining_time = (t_scheduled - t_now).total_seconds()
    if remaining_time > 0: time.sleep(remaining_time)
    action_1()

def action_2():
    self.display_video()
    self.play_player()
    self.move_playlist(movement=-1)
    self.play_player()
    time.sleep(5)
    self.set_player()
    self.display_video()
    self.play_player()
    self.move_playlist(movement=1)
    self.play_player()
    time.sleep(5)
    self.move_playlist(movement=1)
    self.play_player()
    unset_player()

for t in ['202610101105', '202610101320', '202610101405']:
    t_now = datetime.now()
    t_scheduled = datetime.strptime(t, '%Y%m%d%H%M%S')
    remaining_time = (t_scheduled - t_now).total_seconds()
    if remaining_time > 0: time.sleep(remaining_time)
    action_2()
