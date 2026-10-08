import re
from pathlib import Path

from shell_jekyll.gb_var import TimeMap as time_map
from shell_jekyll import gb_var as gb_var_script

gb_var = gb_var_script.get_gbvar_ctx()
gb_var_full = gb_var_script.get_gbvar_full()

FALLBACK_IMAGE: Path = Path(__file__).resolve().parents[1] / "_resources" / "fallback.png"


class EditingUtils:
    @classmethod
    def has_sequence(cls) -> bool:
        """Return True when at least one sequence is loaded.

        [Added] ``gb_var_full.mata_filename`` raises ``KeyError`` before the
        first sequence is loaded, so the old ``if not gb_var_full.mata_filename``
        checks crashed instead of returning.  This is the safe replacement.
        """
        return gb_var_script.is_configured() and bool(gb_var_full.mata_filename)

    @classmethod
    def layer_count(cls) -> int:
        """Return the number of loaded layers (0 before anything is loaded)."""
        return len(gb_var_full.first_sequence_idx) if gb_var_script.is_configured() else 0

    @classmethod
    def get_actual_img_idx(cls,
                           seq_idx: int,
                           layer: int
                           ) -> int:
        actual_img_idx = time_map.time_map[layer].get(seq_idx, None)
        if actual_img_idx is not None:
            return actual_img_idx
        checking_idx = seq_idx - 1
        while actual_img_idx is None and checking_idx >= 0:
            actual_img_idx = time_map.time_map[layer].get(checking_idx, None)
            checking_idx -= 1
        return actual_img_idx if actual_img_idx is not None else -1

    @classmethod
    def get_actual_filepath(cls,
                            img_idx: int,
                            layer: int
                            ) -> str:
        actual_filename = gb_var_full.mata_filename[layer].replace(
            '#' * gb_var_full.frame_notation_len[layer],
            f"{img_idx:0{gb_var_full.frame_notation_len[layer]}d}"
            )
        return actual_filename

    @classmethod
    def get_base_frames(cls,
                        layer: int
                        ) -> list[int]:
        """Return the frame numbers found on disk for ``layer``.

        [Changed] Returns ``[]`` (not ``None``) when the directory is missing,
        and the dead ``root_dir is None`` check (``Path(...)`` is never None)
        was removed.  ``None`` used to flow into ``int(x) in base_frame_list``
        / ``len(base_frame_list)`` and crash.
        """
        root_dir = Path(gb_var_full.sequence_root_dir[layer])
        if not root_dir.exists():
            return []
        template = gb_var_full.mata_filename[layer]
        placeholder_template = re.sub(r"#+", "___DIGIT_PLACEHOLDER___", template)
        escaped_template = re.escape(placeholder_template)
        regex_pattern = escaped_template.replace("___DIGIT_PLACEHOLDER___", r"(\d+)")
        compiled_regex = re.compile(f"^{regex_pattern}$")
        glob_pattern = re.sub(r"#+", "*", template)
        base_frames = []
        for file_path in root_dir.glob(glob_pattern):
            match = compiled_regex.match(file_path.name)
            if match:
                base_frames.append(int(match.group(1)))
        return base_frames

    @classmethod
    def get_layer_image_path(cls,
                             img_idx: int,
                             layer: int
                             ) -> Path:
        """Return the image path of ``img_idx`` on ``layer``, or the fallback image if missing.

        [Added] The "build path -> if missing use fallback.png" block was
        copy-pasted in 6 places (move_sequence, Return key, read_proj,
        open_sequence, ref_video_proceed, ...).  They all call this now.
        """
        path = Path(gb_var_full.sequence_root_dir[layer]) / cls.get_actual_filepath(img_idx=img_idx, layer=layer)
        return path if path.exists() else FALLBACK_IMAGE

    @classmethod
    def resolve_image_paths(cls,
                            seq_idx: int
                            ) -> list[str]:
        """Return one image path per layer for timeline position ``seq_idx``.

        [Added] Shared "seq_idx -> time_map -> file name -> path" loop (see
        ``get_layer_image_path``).  Note: the old ``ref_video_proceed`` copy
        of this loop used ``gb_var.sequence_root_dir`` (the *active* layer's
        folder) for every layer, so layers living in different folders
        showed the fallback image during playback; that is fixed by using
        each layer's own folder here.
        """
        return [
            str(cls.get_layer_image_path(
                img_idx=cls.get_actual_img_idx(seq_idx=seq_idx, layer=l), layer=l))
            for l in range(cls.layer_count())
        ]

    @classmethod
    def used_image_paths(cls) -> list[str]:
        """Return every existing image file referenced by ``time_map`` (unique, layer by layer).

        [Added] The "which files does real-time playback need" part of the old
        ``OpenGLImageWidget.send_img_to_buffer``, moved out of the GL widget
        so the widget no longer reads global project state.
        """
        paths: list[str] = []
        seen: set[str] = set()
        for layer in range(min(cls.layer_count(), len(time_map.time_map))):
            for img_idx in sorted(set(int(v) for v in time_map.time_map[layer].values())):
                path = Path(gb_var_full.sequence_root_dir[layer]) / cls.get_actual_filepath(img_idx=img_idx, layer=layer)
                key = str(path)
                if key not in seen and path.exists():
                    seen.add(key)
                    paths.append(key)
        return paths
