import json
import os
from pathlib import Path
from typing import Any

from shell_jekyll import gb_var as gb_var_script
from shell_jekyll.gb_var import TimeMap as time_map, MAX_LAYER

gb_var = gb_var_script.get_gbvar_ctx()
gb_var_full = gb_var_script.get_gbvar_full()

class IO_sjproj:
    def __init__(self):
        pass

    @classmethod
    def write_sjproj(cls,
                    saving_path: str | Path,
                    writing_info: dict
                    ) -> Path:
        """Merge ``writing_info`` into the .sjproj file at ``saving_path`` and return the real path.

        [Changed]
        * Extension handling: the old code removed the last extension with
          ``"".join(split("."))`` which also deleted every other dot in the
          path (``/a.b/x.v2.png`` -> ``/ab/x`` ...).  ``Path.with_suffix`` is
          used instead.  ``Path`` and ``str`` are both accepted (callers pass
          either).
        * The file is written to a temporary file and moved over the target
          (``os.replace``), so a crash while writing can no longer leave a
          half-written / empty project file.
        * Returns the final path (was ``None``).
        """
        saving_path = Path(saving_path)
        if saving_path.suffix != ".sjproj":
            saving_path = saving_path.with_suffix(".sjproj")
        if saving_path.exists():
            with open(saving_path, "r", encoding="utf-8") as f:
                current_sjproj = json.load(f)
            for writing_attr in writing_info:
                current_sjproj[writing_attr] = writing_info[writing_attr]
        else:
            current_sjproj = writing_info
        tmp_path = saving_path.with_name(saving_path.name + ".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(current_sjproj, f, indent=3, ensure_ascii=False)
        os.replace(tmp_path, saving_path)
        gb_var_full.saving_path = saving_path
        gb_var.saving_path = gb_var_full.saving_path
        return saving_path

    @classmethod
    def load_sjproj(cls,
                   reading_path: str | Path
                   ) -> None:
        """Load a .sjproj file into ``TimeMap`` and ``GBVar``.

        [Changed]
        * ``TimeMap.time_map`` is now cleared first.  It used to be *appended
          to*, so opening a project a second time (or after adding a
          sequence) stacked extra layers on top of the old ones and every
          layer index pointed at the wrong time map.
        * Layers without a saved time map get an identity map built from
          ``base_frame_list``, so ``time_map[layer]`` can never be missing.
        * ``ref_path`` stored as ``null`` / ``"None"`` (older files wrote the
          string ``"None"`` when no reference video was set) loads as ``None``.
        * Removed the unused ``from dataclasses import asdict``.
        """
        if reading_path is None or not Path(reading_path).exists():
            return
        with open(reading_path, "r", encoding="utf-8") as f:
            current_sjproj = json.load(f)
        base_frame_list = [[int(i) for i in sublist] for sublist in current_sjproj.get("base_frame_list", [])]
        time_map.time_map = [
            {int(k) : int(v) for k, v in time_map_i.items()}
            for time_map_i in current_sjproj.get("time_map", [])
        ]
        for layer in range(len(time_map.time_map), len(base_frame_list)):
            time_map.time_map.append({i : i for i in base_frame_list[layer]})
        ref_path = current_sjproj.get("ref_path")
        data = {
            "base_frame_list" : base_frame_list,
            "sequence_root_dir" : [Path(x) for x in current_sjproj["sequence_root_dir"]] if "sequence_root_dir" in current_sjproj else [],
            "mata_filename" : current_sjproj.get("mata_filename", []),
            "first_sequence_idx" : current_sjproj.get("first_sequence_idx", []),
            "frame_notation_len" : current_sjproj.get("frame_notation_len", []),
            "ref_video_start" : current_sjproj.get("ref_video_start", 0),
            "ref_path" : Path(ref_path) if ref_path not in (None, "", "None") else None,
            "saving_path" : Path(reading_path),
            "layer_order" : current_sjproj.get("layer_order", [i for i in range(0, MAX_LAYER)])
        }
        gb_var_full.initialize(init_data=data)

    @classmethod
    def read_sjproj(cls,
                   reading_path: str | Path,
                   reading_attr: str
                   ) -> Any:
        if reading_path is None or not Path(reading_path).exists():
            return
        with open(reading_path, "r", encoding="utf-8") as f:
            current_sjproj = json.load(f)
        return current_sjproj.get(reading_attr, None)
