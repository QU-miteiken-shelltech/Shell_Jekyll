import json
from pathlib import Path
from typing import Any

from shell_jekyll import gb_var as gb_var_script
from shell_jekyll.gb_var import TimeMap as time_map

gb_var = gb_var_script.get_gbvar_ctx()
gb_var_full = gb_var_script.get_gbvar_full()

MAX_LAYER : int = 8

class IO_sjproj:
    def __init__(self):
        pass

    @classmethod
    def write_sjproj(cls, 
                    saving_path: str,
                    writing_info: dict
                    ) -> None:
        if not str(saving_path).endswith(".sjproj"):
            if "." in saving_path:
                saving_path_split = saving_path.split(".")
                saving_path_split.pop(-1)
                saving_path = "".join(saving_path_split)
            saving_path += ".sjproj"
        if saving_path is not None and Path(saving_path).exists():
            with open(saving_path, "r", encoding="utf-8") as f:
                current_sjproj = json.load(f)
            for writing_attr in writing_info:
                current_sjproj[writing_attr] = writing_info[writing_attr]
        else:
            current_sjproj = writing_info
        with open(saving_path, "w", encoding="utf-8") as f:
            json.dump(current_sjproj, f, indent=3, ensure_ascii=False)
        gb_var_full.saving_path = Path(saving_path)
        gb_var.saving_path = gb_var_full.saving_path

    @classmethod
    def load_sjproj(cls,
                   reading_path: str
                   ) -> None:
        if reading_path is None or not Path(reading_path).exists():
            return
        with open(reading_path, "r", encoding="utf-8") as f:
            current_sjproj = json.load(f)
        current_time_map = current_sjproj.get("time_map", [])
        for time_map_i in current_time_map:
            time_map.time_map.append({int(k) : int(v) for k, v in time_map_i.items()})
        data = {
            "base_frame_list" : [[int(i) for i in sublist] for sublist in current_sjproj.get("base_frame_list", [])],
            "sequence_root_dir" : [Path(x) for x in current_sjproj["sequence_root_dir"]] if "sequence_root_dir" in current_sjproj else [],
            "mata_filename" : current_sjproj.get("mata_filename", []),
            "first_sequence_idx" : current_sjproj.get("first_sequence_idx", []),
            "frame_notation_len" : current_sjproj.get("frame_notation_len", []),
            "ref_video_start" : current_sjproj.get("ref_video_start", 0),
            "ref_path" : Path(current_sjproj["ref_path"]) if "ref_path" in current_sjproj else None,
            "saving_path" : Path(reading_path),
            "layer_order" : current_sjproj.get("layer_order", [i for i in range(0, MAX_LAYER)])
        }
        gb_var_full.initialize(init_data=data)
        from dataclasses import asdict

    @classmethod
    def read_sjproj(cls,
                   reading_path: str,
                   reading_attr: str
                   ) -> Any:
        if reading_path is None or not Path(reading_path).exists():
            return
        with open(reading_path, "r", encoding="utf-8") as f:
            current_sjproj = json.load(f)
        return current_sjproj.get(reading_attr, None)


        