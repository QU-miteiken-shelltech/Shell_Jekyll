from pathlib import Path

defined_alias = {
    "<PLAY>" : "self.play_player()",
    "<PROCEED>" : "self.move_playlist(movement=1)",
    "<RETURN>" : "self.move_playlist(movement=-1)",
    "<SET>" : "self.set_player()",
    "<DISPLAY>" : "self.display_video()",
    "<UNSET>" : "self.unset_player()",
    "<PAUSE>" : "self.pause_player()",
    "<BACK>" : "self.player_back_to_start()",
    "<WAIT5>" : "time.sleep(5)"
}

def compile_scheduler_script(script_path: str | Path):
    with open(script_path, "r", encoding="utf-8") as f:
        script_list = f.readlines()

    flattened = []
    for line in script_list:
        line = line.strip()
        line = line.strip("\n")
        line = line.strip()
        if not line: 
            continue
        elements = line.split(" ")
        for element in elements:
            if element:
                flattened.append(element)

    rtn = "import datetime.datetime\nimport time\n"
    buf = []
    var = {}
    buffering_flag = False
    to_buf_flag = False
    is_command = False
    is_waiting_time = False
    is_compiling_to_py = False
    is_recording_schedule = False
    func_count = 0
    for element in flattened:
        if element in defined_alias:
            element = defined_alias[element]
        elif element in var:
            element = var[element]
        elif "/" in element:
            element = element.split("/")

        if element == "DEF":
            if buffering_flag:
                print("Previoud definition declaration not completed before next declaration starts")
                break
            buffering_flag = True
            buf = []
        elif element == "AS":
            if not buffering_flag: 
                print("Alias defined without declaration")
                break
            buffering_flag = False
            to_buf_flag = True
        elif isinstance(element, str) and element.startswith("$") and element.endswith("$") and to_buf_flag:
            to_buf_flag = False
            var[element] = buf
            buf = []
        elif element == "CALL":
            if is_compiling_to_py:
                print("Unterminated call exist")
                break
            is_compiling_to_py = True
        elif element == "FIN":
            if not is_compiling_to_py:
                print("Nothing to terminate")
                break
            is_compiling_to_py = False
            func_count += 1
            rtn += f"\ndef action_{func_count}():"
            for code in buf:
                rtn += f"\n    {code}"
            rtn += "\n"
            buf = []
        elif element == "AT":
            if is_recording_schedule:
                print("Previous schedule unrecorded_yet")
                break
            is_recording_schedule = True
        elif is_recording_schedule:
            rtn += f"\nfor t in {element}:"
            rtn += "\n    t_now = datetime.now()"
            rtn += "\n    t_scheduled = datetime.strptime(t, '%Y%m%d%H%M%S')"
            rtn += "\n    remaining_time = (t_scheduled - t_now).total_seconds()"
            rtn += "\n    if remaining_time > 0: time.sleep(remaining_time)"
            rtn += f"\n    action_{func_count}()"
            rtn += "\n"
            is_recording_schedule = False
        else:
            if buffering_flag or is_compiling_to_py:
                if element == "DO":
                    if is_command:
                        print("Commands cannot be decleared consecutively with one DO call")
                        break
                    is_command = True
                elif element == "WAIT":
                    if is_waiting_time:
                        print("Waitings cannot be decleared consecutively with one WAIT call")
                        break
                    is_waiting_time = True
                else:
                    if is_command:
                        buf.append(element)
                        is_command = False
                    elif is_waiting_time:
                        buf.append(f"time.sleep({element})")
                    else:
                        if isinstance(element, list):
                            buf.extend(element)
                        else:
                            buf.append(element)

    print(var)

    return rtn




code = compile_scheduler_script("/Users/shiinaayame/Documents/ShellJekyll/sample_scheduler.txt")
with open("/Users/shiinaayame/Documents/ShellJekyll/sample_scheduler_compiled.py", "w", encoding="utf-8") as f:
    f.write(code)
