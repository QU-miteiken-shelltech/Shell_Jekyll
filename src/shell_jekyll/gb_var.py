from pathlib import Path
from dataclasses import dataclass, field, fields
from typing import Optional, Dict, Any

from shell_jekyll.style import (
    dark_default, pure_skyblue,
    kawaii_pink, elegant_light
    )
styles = {
    "dark_default" : dark_default,
    "pure_skyblue" : pure_skyblue,
    "kawaii_pink" : kawaii_pink,
    "elegant_light" : elegant_light,
}
style_script: Any = dark_default

IS_CONFIGED: bool = False
MAX_LAYER: int = 8


def is_configured() -> bool:
    """Return True once a sequence / project has been loaded (``IS_CONFIGED``).

    [Added] Every ``GBVar`` / ``GBVar_CTX`` attribute access raises ``KeyError``
    before the first sequence is loaded.  Callers that may run in that state
    (key shortcuts, buttons, headless scripts) use this instead of reading the
    ``IS_CONFIGED`` module global or catching ``KeyError``.
    """
    return IS_CONFIGED


class TimeMap:
    time_map: list[dict[int, int]] = []

    @classmethod
    def permute(cls, perm: list[int]) -> None:
        """Reorder the per-layer dicts so that new slot ``i`` holds old slot ``perm[i]``.

        [Added] Small helper used by ``GBVar.restack_layers`` (replaces the
        numpy object-array round trip that used to live there).
        """
        cls.time_map = _permuted(cls.time_map, perm)


def _permuted(values: list, perm: list[int]) -> list:
    """Return ``[values[perm[0]], values[perm[1]], ...]`` for the first ``len(values)`` slots.

    The permutation is only applied when ``perm[:len(values)]`` is itself a
    permutation of ``range(len(values))``; otherwise ``values`` is returned
    unchanged (e.g. empty / not-yet-populated lists such as ``layer_visibility``).
    """
    n = len(values)
    sub = perm[:n]
    if sorted(sub) != list(range(n)):
        return values
    return [values[j] for j in sub]


@dataclass
class GBVar:
    base_frame_list : list[list[int]] = field(default_factory=lambda: list([[]]))
    sequence_root_dir : list[Path] = field(default_factory=list)
    mata_filename : list[str] = field(default_factory=list)
    first_sequence_idx : list[int] = field(default_factory=list)
    frame_notation_len : list[int] = field(default_factory=list)
    saving_path : Path | None = None
    ref_path: Path | None = None
    ref_video_start: int = 0
    layer_order: list[int] = field(default_factory=list)

    layer_visibility : list[int] = field(default_factory=list)

    _instance: Optional["GBVar"] = None

    @classmethod
    def get_instance(cls) -> "GBVar":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def initialize(self,
                   init_data: Optional[Dict[str, Any]]):
        global IS_CONFIGED
        valid_fields = {f.name for f in fields(self)}
        for k, v in init_data.items():
            if k in valid_fields:
                setattr(self, k, v)
            else:
                raise KeyError(f"Key : {k} not exist, so initilization failed")
        IS_CONFIGED = True
        GBVar_CTX.get_instance().initialize()

    def __getattribute__(self, name):
        global IS_CONFIGED
        if name in ("__dict__", "__class__", "__dataclass_fields__") or name.startswith("_"):
            return super().__getattribute__(name)
        attr = super().__getattribute__(name)
        if callable(attr):
            return attr
        if not IS_CONFIGED:
            if name in ["layer_visibility"]:
                return [1] * MAX_LAYER
            raise KeyError(f"Unconfiged yet: cannot access '{name}'")

        return attr

    def restack_layers(self,
                       new_layer_order: list[int],
                       new_active_layer: int):
        """Re-order every per-layer list so it follows ``new_layer_order``.

        [Changed] Fixes ``layer_order`` / data drifting apart after the 2nd
        re-stack.  Old code composed ``old_order[new_layer_order]`` and then
        permuted the data lists by the *absolute* ``layer_order`` instead of by
        the *relative* move, so after two or more moves the layer labels no
        longer matched the data (and a saved project came back scrambled).

        Now ``layer_order`` simply becomes ``new_layer_order`` (callers already
        build it by popping/inserting inside a copy of ``layer_order``), and the
        data lists / ``TimeMap`` are permuted by the relative permutation
        ``perm[i] = old_order.index(new_layer_order[i])`` ("new slot i takes the
        old slot perm[i]").  The first move gives exactly the same result as
        before.  The numpy object-array round trip (which silently turned
        equal-length nested lists into a 2-D array) and the debug ``print`` of
        the whole dataclass were removed.
        """
        old_order = list(self.layer_order)
        perm = [old_order.index(label) for label in new_layer_order]
        self.layer_order = list(new_layer_order)
        for f in fields(self):
            val = getattr(self, f.name)
            if isinstance(val, list) and f.name != "layer_order":
                setattr(self, f.name, _permuted(val, perm))
        TimeMap.permute(perm)
        get_gbvar_ctx().switch_layer(new_active_layer=new_active_layer, do_write_back=False)

    def append_info(self,
                    new_info: dict):
        """Append ``new_info[name]`` to every list field named in ``new_info``.

        [Changed] Dropped the redundant ``setattr`` (``list.append`` already
        mutates in place).
        """
        for f in fields(self):
            val = getattr(self, f.name)
            if f.name in new_info and isinstance(val, list):
                val.append(new_info[f.name])



@dataclass
class GBVar_CTX:
    base_frame_list : list[int] = field(default_factory=list)
    sequence_root_dir : Path | None = None
    mata_filename : str | None = None
    first_sequence_idx : int = 0
    frame_notation_len : int = 0
    active_layer: int = 0
    saving_path : Path | None = None
    ref_path: Path | None = None
    ref_video_start: int = 0

    _instance: Optional["GBVar_CTX"] = None

    @classmethod
    def get_instance(cls) -> "GBVar_CTX":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __getattribute__(self, name):
        global IS_CONFIGED
        if name in ("__dict__", "__class__", "__dataclass_fields__") or name.startswith("_"):
            return super().__getattribute__(name)

        attr = super().__getattribute__(name)
        if callable(attr):
            return attr

        if not IS_CONFIGED:
            raise KeyError(f"Unconfiged yet: cannot access '{name}'")

        return attr

    def write_to_main(self, active_layer: int):
        """Write the active-layer working copy (and project-wide fields) back to ``GBVar``.

        [Changed] ``ref_path`` / ``ref_video_start`` / ``saving_path`` are now
        written back too.  They live in this context object (that is where the
        UI sets them) but were never copied to ``GBVar`` -- and ``save_proj``
        reads them from ``GBVar`` -- so the reference video and its "Mark as
        Start" position were silently lost on save.
        """
        gbvar = GBVar.get_instance()
        gbvar.base_frame_list[active_layer] = self.base_frame_list
        gbvar.sequence_root_dir[active_layer] = self.sequence_root_dir
        gbvar.mata_filename[active_layer] = self.mata_filename
        gbvar.first_sequence_idx[active_layer] = self.first_sequence_idx
        gbvar.frame_notation_len[active_layer] = self.frame_notation_len
        gbvar.ref_path = self.ref_path
        gbvar.ref_video_start = self.ref_video_start
        gbvar.saving_path = self.saving_path

    def switch_layer(self,
                     new_active_layer: int,
                     do_write_back: bool=True):
        """Make ``new_active_layer`` the working layer (optionally saving the old one first).

        [Changed] Removed the debug ``print`` of the whole ``GBVar`` dataclass
        that ran on every layer switch.
        """
        gbvar = GBVar.get_instance()
        if do_write_back:
            self.write_to_main(active_layer=self.active_layer)
        self.active_layer = new_active_layer
        self.base_frame_list = gbvar.base_frame_list[new_active_layer]
        self.sequence_root_dir = gbvar.sequence_root_dir[new_active_layer]
        self.mata_filename = gbvar.mata_filename[new_active_layer]
        self.first_sequence_idx = gbvar.first_sequence_idx[new_active_layer]
        self.frame_notation_len = gbvar.frame_notation_len[new_active_layer]

    def initialize(self):
        gbvar = GBVar.get_instance()
        self.switch_layer(new_active_layer=0, do_write_back=False)
        self.saving_path = gbvar.saving_path
        self.ref_path = gbvar.ref_path
        self.ref_video_start = gbvar.ref_video_start

def get_gbvar_full():
    return GBVar.get_instance()

def get_gbvar_ctx():
    return GBVar_CTX.get_instance()
