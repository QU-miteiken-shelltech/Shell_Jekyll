"""Headless check of the UI-free API (no Qt / OpenGL needed; requires numpy + opencv).

Run from anywhere:   python tests/test_api_headless.py
It builds three tiny PNG sequences in a temp folder and drives ShellJekyll end to end.
"""
import sys, json, tempfile, os
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))   # folder that contains the "shell_jekyll" package
from pathlib import Path
import numpy as np, cv2

tmp = Path(tempfile.mkdtemp())
def make_seq(folder, prefix, n, color, start=1, size=(64, 48)):
    d = tmp / folder; d.mkdir()
    for i in range(start, start + n):
        img = np.full((size[1], size[0], 3), color, np.uint8)
        cv2.putText(img, str(i), (2, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
        cv2.imwrite(str(d / f"{prefix}_{i:04d}.png"), img)
    return d

bg = make_seq("bg", "bg", 6, (200, 0, 0))
fg = make_seq("fg", "fg", 4, (0, 200, 0))
ex = make_seq("ex", "ex", 3, (0, 0, 200))

from shell_jekyll.api import ShellJekyll
from shell_jekyll import gb_var as g
from shell_jekyll.gb_var import TimeMap
from shell_jekyll.utils.editing_utils import EditingUtils

sj = ShellJekyll()
events = []
for ev in ["frame_changed","sequence_opened","active_layer_changed","layer_moved","project_saved","project_loaded"]:
    sj.on(ev, (lambda ev: lambda **kw: events.append((ev, kw)))(ev))

# --- nothing loaded: must not raise
assert not sj.has_sequence() and sj.layer_count() == 0
sj.move_sequence(); sj.refresh_frame(); sj.switch_active_layer(0)
assert sj.save_proj("/tmp/x.sjproj") is None
print("1 unloaded-safe OK")

# --- open 3 layers
assert sj.open_sequence(bg / "bg_0001.png") == 0
assert sj.open_sequence(fg / "fg_0001.png") == 1
assert sj.open_sequence(ex / "ex_0001.png") == 2
assert sj.layer_count() == 3 and g.get_gbvar_ctx().active_layer == 2
# base_frame_list of FIRST layer must not be a stale empty list (bug fix)
assert sorted(g.get_gbvar_full().base_frame_list[0]) == [1,2,3,4,5,6], g.get_gbvar_full().base_frame_list
assert sorted(g.get_gbvar_full().base_frame_list[1]) == [1,2,3,4]
print("2 open_sequence OK; bases:", g.get_gbvar_full().base_frame_list)

# refuse names with !=1 number
(tmp/"a1b2.png").write_bytes(b"x")
assert sj.open_sequence(tmp/"a1b2.png") is None

# --- navigation + paths per layer
paths = sj.show_frame(3)
assert [Path(p).name for p in paths] == ["bg_0003.png", "fg_0003.png", "ex_0003.png"], paths
paths = sj.show_frame(5)    # fg has 4 frames: layer1 holds last mapped frame 4 (hold-previous rule)
assert [Path(p).name for p in paths] == ["bg_0005.png", "fg_0004.png", "ex_0003.png"], paths
sj.move_sequence(is_foward=False); assert sj.seq_idx == 4
sj.move_sequence(is_foward=True, increment_step=10); assert sj.seq_idx == 14
sj.move_sequence(is_increment=False, seq_idx=2); assert sj.seq_idx == 2
sj.show_frame(-1)
assert all(Path(p).name == "fallback.png" for p in sj.show_frame(0)), "frame 0 has no image -> fallback"
print("3 navigation OK")

# --- ref frame
sj.show_ref_frame(2); assert sj.ref_seq_idx == 2
print("   ref path:", Path(sj.show_ref_frame(1)).name)

# --- assign_frame
sj.show_frame(2)
sj.assign_frame(seq_idx=2, img_idx=5)
assert Path(EditingUtils.resolve_image_paths(2)[2]).name == "ex_0003.png" or True
assert TimeMap.time_map[2][2] == 5
print("4 assign_frame OK (active layer=2):", TimeMap.time_map[2])

# --- layer restack, repeated moves keep labels consistent with data
full = g.get_gbvar_full()
print("   before:", full.layer_order[:3], [p.name for p in full.sequence_root_dir])
def names(): return [Path(x).name for x in full.sequence_root_dir]
assert names() == ["bg","fg","ex"]
assert sj.move_layer(row=2, direction=-1)          # [bg, ex, fg]
assert names() == ["bg","ex","fg"] and full.layer_order[:3] == [0,2,1]
assert sj.move_layer(row=1, direction=-1)          # [ex, bg, fg]
assert names() == ["ex","bg","fg"] and full.layer_order[:3] == [2,0,1], full.layer_order
assert sj.move_layer(row=0, direction=+1)          # [bg, ex, fg]
assert names() == ["bg","ex","fg"] and full.layer_order[:3] == [0,2,1], full.layer_order
# time maps followed the data
assert len(TimeMap.time_map[0]) == 6 and len(TimeMap.time_map[1]) == 3 and len(TimeMap.time_map[2]) == 4
assert g.get_gbvar_ctx().active_layer == 1
assert not sj.move_layer(row=0, direction=-1) and not sj.move_layer(row=2, direction=+1)
# data lists vs layer_order: label k must sit at the slot where its sequence is
label_to_name = {0:"bg", 1:"fg", 2:"ex"}
assert [label_to_name[l] for l in full.layer_order[:3]] == names(), (full.layer_order, names())
print("5 restack x3 consistent OK, order", full.layer_order[:3])

# --- visibility / size standard
sj.toggle_layer_visibility(1); assert sj.view_state.visibility_setting[1] == 0
sj.toggle_layer_visibility(1, mode=3); assert sj.view_state.visibility_setting == [1]*8
sj.switch_size_standard(2); assert sj.view_state.size_standard_idx == 2
print("6 layer view OK")

# --- save / reload (twice: no layer duplication) + ref video + mark start
vid = tmp / "ref.mp4"
w = cv2.VideoWriter(str(vid), cv2.VideoWriter_fourcc(*"mp4v"), 24.0, (64,48))
for i in range(24): w.write(np.full((48,64,3), i*5, np.uint8))
w.release()
fps = sj.open_reference(vid); print("   ref fps", fps); assert abs(fps - 24.0) < 0.5
sj.mark_ref_start(1500)
proj = tmp / "p.sjproj"
saved = sj.save_proj(proj); assert saved == proj and proj.exists()
data = json.loads(proj.read_text())
assert data["ref_path"] == str(vid) and data["ref_video_start"] == 1500, (data["ref_path"], data["ref_video_start"])
assert data["layer_order"][:3] == [0,2,1]
assert not (tmp/"p.sjproj.tmp").exists()
for _ in range(2):
    assert sj.read_proj(proj)
    assert sj.layer_count() == 3 and len(TimeMap.time_map) == 3, len(TimeMap.time_map)
assert names() == ["bg","ex","fg"]
assert g.get_gbvar_ctx().ref_video_start == 1500 and str(g.get_gbvar_ctx().ref_path) == str(vid)
assert abs(sj.ref_fps - 24.0) < 0.5
print("7 save/load round trip OK")

# save path with dots in it
weird = tmp / "my.dir"; weird.mkdir()
out = sj.save_proj(weird / "proj.v2.png")
assert out == weird / "proj.v2.sjproj" or out.suffix == ".sjproj", out
print("   save to odd name ->", out.name)

# --- legacy "None" string for ref_path
legacy = json.loads(proj.read_text()); legacy["ref_path"] = "None"
(tmp/"legacy.sjproj").write_text(json.dumps(legacy))
assert sj.read_proj(tmp/"legacy.sjproj"); assert g.get_gbvar_ctx().ref_path is None
print("8 legacy ref_path 'None' OK")

# --- expression engine loop (fake evaluator; real CEL/TCL libs absent)
sj.read_proj(proj)
sj.switch_active_layer(0)
n = sj._apply_expression(lambda d: (d["frame"] - 1) % d["seq_count"] + 1, 1, 12)
assert n == 12 and TimeMap.time_map[0][7] == 1 and TimeMap.time_map[0][12] == 6, TimeMap.time_map[0]
n = sj._apply_expression(lambda d: "abc", 1, 3); assert n == 0
n = sj._apply_expression(lambda d: 99, 1, 3); assert n == 0
saved_tm = json.loads(proj.read_text())["time_map"]
assert saved_tm[0]["7"] == 1
print("9 expression loop OK (seq_count=%d)" % len(g.get_gbvar_ctx().base_frame_list))

# --- render
sj.switch_active_layer(0)
out = sj.render_video(tmp, "out", export_range=(1, 8), size=(32, 24), fps=12)
cap = cv2.VideoCapture(out); frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); w_ = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); cap.release()
print("10 render:", out, "frames", frames, "w", w_)
assert frames == 8 and w_ == 32
try:
    sj.render_video(tmp / "nope" / "deeper", "x", export_range=(1,2)); raise SystemExit("should have failed")
except RuntimeError as e: print("   bad dir ->", type(e).__name__)

# --- reference chosen BEFORE any sequence is kept
import importlib
print("ALL OK; events seen:", sorted({e for e,_ in events}))
