#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shell Jekyll Player — 上映前 最終点検スクリプト（読み取り専用）

目的:
    上映直前に「このPCで Jekyll Player が正常に動く状態か」を確認する。
    デバッグ用ではなく、go / no-go の最終確認用。

絶対ルール: 何も変更しない
    * ファイルの作成・書き込み・削除・リネーム・権限変更をしない。
    * .pyc も作らない（-B 相当）。点検対象コードの import で生じうる書き込みも、
      Python の監査フック(sys.addaudithook)で「実行時に拒否」する。
      拒否が起きた場合は結果に必ず表示される（何も書き込まれていない）。
    * 再生・ウィンドウ表示・Flask起動・ポートbind・ダウンロード・ffmpeg変換はしない。
    * scheduler_compiler.py は import 時に固定パスへファイルを書き出す実装のため、
      絶対に import しない。
    ※ 制御できない範囲: Qt/OS 自身が内部で作りうる一時キャッシュ（フォントキャッシュ等）。

使い方:
    python3 preshow_check.py [shell_jekyll フォルダ]  [オプション]

    ※ 上映に使う Python（venv など）で実行すること。別の Python だと
      ライブラリ有無の判定が実機とずれる。

主なオプション:
    --playlist FILE.sjplay    プレイリストを点検（ファイル存在・ffprobe・Qtで実際に読込）。複数なら繰り返し指定
    --schedule FILE.sjschedule  スケジュールを点検（未定義コマンド=exec()される文字列を検出）。同上
    --expect-displays N       接続ディスプレイ数がN未満ならNG
    --expect-display NAME     名前にNAMEを含むディスプレイが無ければNG
    --expect-audio NAME       名前にNAMEを含む音声出力が無ければNG
    --expect-digest HEX       ソース一式のダイジェスト（先頭8桁以上）が違えばNG
                              （リハーサル時の値を控えておけば「その後に改変されていないか」が分かる）
    --soak SEC                プレイヤー画面を生成したままイベントループをSEC秒回す（既定3）
    --no-qt                   Qtを使う検査（実機ディスプレイ/音声/画面生成）を省略
    --json                    結果をJSONで出力
    -v                        詳細表示

終了コード: 0=OK / 1=要確認(WARNあり) / 2=NG(FAILあり)
"""
import sys
import os

sys.dont_write_bytecode = True  # 何よりも先に: .pyc を作らない

# このスクリプトのあるフォルダを import 検索パスから外す。
# （shell_jekyll フォルダ内に置かれても、io/ や api.py 等が標準ライブラリ・他ライブラリを隠さないため）
try:
    _self_dir = os.path.dirname(os.path.realpath(__file__))
    sys.path[:] = [_p for _p in sys.path if not (_p and os.path.isdir(_p) and os.path.samefile(_p, _self_dir))]
except Exception:
    pass

import argparse
import ast
import datetime
import hashlib
import importlib
import importlib.machinery
import importlib.util
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import time
import traceback
from pathlib import Path

PKG = "shell_jekyll"
MARK = "@@SJCHK@@"
OK, INFO, WARN, FAIL, SKIP = "OK", "INFO", "WARN", "FAIL", "SKIP"

# import 時に副作用（ファイル書き込み）があると判明している／疑わしいモジュール。決して import しない。
DANGEROUS_MODULES = {f"{PKG}.ui.sj_player.scheduler_compiler"}

# 起動に最低限必要なファイル（パッケージ直下からの相対パス）
CORE_FILES = [
    "__main__.py",
    "api.py",
    "gb_var.py",
    "ui/launcher.py",
    "ui/sj_player/main_ui/vj_win.py",
    "ui/sj_player/main_ui/vj_win_ui.py",
    "ui/sj_player/main_ui/vj_win_events.py",
    "ui/sj_player/player_win.py",
    "ui/sj_player/remote_app.py",
    "ui/sj_player/web_ui.html",
    "ui/sj_player/vj_win_actionman.py",
]

GROUPS = [
    "環境", "ソース整合性", "依存ライブラリ", "外部ツール",
    "システム状態", "ネットワーク", "Qt実機検査", "上映データ", "点検自身の安全性",
]

# =============================================================================
# 書き込みガード（絶対に何も変更しないための実行時強制）
# =============================================================================
_VIOLATIONS: list = []
_GUARD_ON = False


def install_write_guard():
    """監査フックで「書き込み系の操作」をすべて拒否する。一度入れると外せない（Python仕様）。"""
    global _GUARD_ON
    if _GUARD_ON:
        return
    _GUARD_ON = True
    write_bits = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
    devnull = os.devnull.lower()
    blocked = {
        "os.remove", "os.rename", "os.rmdir", "os.mkdir", "os.truncate", "os.chmod",
        "os.chown", "os.utime", "os.symlink", "os.link", "os.mkfifo", "os.mknod",
        "os.setxattr", "os.removexattr",
        "shutil.copyfile", "shutil.copymode", "shutil.copystat", "shutil.copytree",
        "shutil.move", "shutil.rmtree", "shutil.chown", "shutil.make_archive",
        "shutil.unpack_archive", "tempfile.mkstemp", "tempfile.mkdtemp",
        "socket.bind",
    }

    def deny(event, args):
        _VIOLATIONS.append((event, repr(args)[:200]))
        raise PermissionError(f"preshow_check: write blocked ({event})")

    def hook(event, args):
        if event == "open":
            path, mode, flags = args
            if not isinstance(path, (str, bytes, os.PathLike)):
                return  # fd 指定など
            p = os.fsdecode(path).lower() if not isinstance(path, os.PathLike) else str(path).lower()
            if p.startswith("/dev/") or p in (devnull, "nul"):
                return
            if isinstance(flags, int):
                is_write = bool(flags & write_bits)
            else:
                is_write = bool(mode) and any(c in str(mode) for c in "wax+")
            if is_write:
                deny(event, args)
        elif event in blocked:
            deny(event, args)

    sys.addaudithook(hook)


# =============================================================================
# 結果の入れ物と表示
# =============================================================================
class Report:
    def __init__(self):
        self.items = []  # dict(group,name,status,detail)

    def add(self, group, name, status, detail=""):
        self.items.append({"group": group, "name": name, "status": status, "detail": str(detail or "")})

    def count(self, status):
        return sum(1 for i in self.items if i["status"] == status)


def _color(enabled):
    if not enabled:
        return {k: "" for k in ("OK", "INFO", "WARN", "FAIL", "SKIP", "B", "R")}
    return {
        "OK": "\033[32m", "INFO": "\033[36m", "WARN": "\033[33m",
        "FAIL": "\033[1;31m", "SKIP": "\033[90m", "B": "\033[1m", "R": "\033[0m",
    }


def render(rep, header_lines, verbose=False):
    use_color = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
    c = _color(use_color)
    out = []
    out.extend(header_lines)
    for g in GROUPS:
        items = [i for i in rep.items if i["group"] == g]
        if not items:
            continue
        out.append("")
        out.append(f"{c['B']}■ {g}{c['R']}")
        for i in items:
            tag = f"[{i['status']:^4}]"
            out.append(f"  {c[i['status']]}{tag}{c['R']} {i['name']}")
            if i["detail"]:
                for ln in i["detail"].splitlines():
                    out.append(f"           {ln}")
    nf, nw = rep.count(FAIL), rep.count(WARN)
    out.append("")
    out.append("=" * 64)
    if nf:
        verdict = f"{c['FAIL']}判定: NG — 上映前に解消が必要です（FAIL {nf} / WARN {nw}）{c['R']}"
    elif nw:
        verdict = f"{c['WARN']}判定: 要確認 — 内容を確認して問題なければ上映可（WARN {nw}）{c['R']}"
    else:
        verdict = f"{c['OK']}判定: OK — 点検した範囲では異常なし{c['R']}"
    out.append(verdict)
    out.append(
        f"内訳: OK {rep.count(OK)} / INFO {rep.count(INFO)} / WARN {nw} / FAIL {nf} / SKIP {rep.count(SKIP)}"
    )
    out.append(f"書き込みガード: 拒否した書き込み試行 {len(_VIOLATIONS)} 件（0 なら点検は何にも触れていません）")
    out.append("注意: 映像の見え方・実際の音は機械では確認できません。本番機材で目視・試聴してください。")
    return "\n".join(out)


# =============================================================================
# 静的解析（コードは実行せず、ASTだけで起動経路と依存を洗い出す）
# =============================================================================
SKIP_DIRS = {"__MACOSX", "__pycache__", ".git"}


def index_modules(pkg_dir: Path):
    mods = {}
    for p in pkg_dir.rglob("*.py"):
        rel = p.relative_to(pkg_dir)
        if any(part in SKIP_DIRS or part.startswith(".") for part in rel.parts):
            continue
        parts = list(rel.with_suffix("").parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]
        mods[".".join([PKG] + parts)] = p
    return mods


def _catches_import_error(h: ast.ExceptHandler):
    names = {"ImportError", "ModuleNotFoundError", "Exception", "BaseException"}
    t = h.type
    if t is None:
        return True
    if isinstance(t, ast.Name):
        return t.id in names
    if isinstance(t, ast.Tuple):
        return any(isinstance(e, ast.Name) and e.id in names for e in t.elts)
    return False


class _ImportVisitor(ast.NodeVisitor):
    def __init__(self, modname, is_pkg):
        self.modname, self.is_pkg = modname, is_pkg
        self.func = 0
        self.guard = 0
        self.out = []  # dict(module, names, eager, guarded, line)

    def _enter_func(self, n):
        self.func += 1
        self.generic_visit(n)
        self.func -= 1

    visit_FunctionDef = visit_AsyncFunctionDef = visit_Lambda = _enter_func

    def visit_Try(self, n):
        guarded = any(_catches_import_error(h) for h in n.handlers)
        if guarded:
            self.guard += 1
        for st in n.body:
            self.visit(st)
        if guarded:
            self.guard -= 1
        for h in n.handlers:
            self.visit(h)
        for st in list(n.orelse) + list(n.finalbody):
            self.visit(st)

    visit_TryStar = visit_Try

    def _rec(self, module, names, line):
        self.out.append({
            "module": module, "names": names,
            "eager": self.func == 0, "guarded": self.guard > 0, "line": line,
        })

    def visit_Import(self, n):
        for a in n.names:
            self._rec(a.name, [], n.lineno)

    def visit_ImportFrom(self, n):
        if n.level:
            base = self.modname if self.is_pkg else self.modname.rsplit(".", 1)[0]
            for _ in range(n.level - 1):
                base = base.rsplit(".", 1)[0]
            module = f"{base}.{n.module}" if n.module else base
        else:
            module = n.module or ""
        self._rec(module, [a.name for a in n.names], n.lineno)


def analyze(pkg_dir: Path):
    """起動経路(__main__ と sj_player 一式)から辿れるモジュールと、その依存を静的に求める。"""
    mods = index_modules(pkg_dir)
    namespaces = set()
    for m in mods:
        parts = m.split(".")
        for i in range(1, len(parts)):
            namespaces.add(".".join(parts[:i]))
    is_pkg = {m: p.name == "__init__.py" for m, p in mods.items()}

    roots = [f"{PKG}.__main__"] + sorted(
        m for m in mods if ".ui.sj_player." in m and m not in DANGEROUS_MODULES
    )
    chain, queue = [], [r for r in roots if r in mods]
    seen = set()
    syntax_errors, problems = [], []
    third = {}  # top -> {"req": set, "opt": set}
    pyside_mods = set()  # 起動経路が実際に import する PySide6.* サブモジュール
    stdlib = set(getattr(sys, "stdlib_module_names", ()))

    while queue:
        m = queue.pop(0)
        if m in seen:
            continue
        seen.add(m)
        chain.append(m)
        path = mods[m]
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as e:
            syntax_errors.append(f"{path.relative_to(pkg_dir)}:{e.lineno}: {e.msg}")
            continue
        except (UnicodeDecodeError, OSError) as e:
            syntax_errors.append(f"{path.relative_to(pkg_dir)}: 読み込み不可 {e}")
            continue
        v = _ImportVisitor(m, is_pkg[m])
        v.visit(tree)
        for r in v.out:
            mod, names = r["module"], r["names"]
            if mod == PKG or mod.startswith(PKG + "."):
                targets = []
                if mod in mods:
                    targets.append(mod)
                elif mod not in namespaces and mod != PKG:
                    problems.append(f"{m} (line {r['line']}): 存在しないモジュール {mod}")
                    continue
                for nm in names:
                    sub = f"{mod}.{nm}"
                    if sub in mods:
                        targets.append(sub)
                    elif mod not in mods and nm != "*":
                        problems.append(f"{m} (line {r['line']}): {mod} に {nm} が無い")
                for t in targets:
                    if t in DANGEROUS_MODULES:
                        problems.append(f"{m} が危険なモジュール {t} を import している")
                    elif t not in seen:
                        queue.append(t)
            else:
                top = mod.split(".")[0]
                if not top or top in stdlib:
                    continue
                slot = third.setdefault(top, {"req": set(), "opt": set()})
                (slot["req"] if (r["eager"] and not r["guarded"]) else slot["opt"]).add(m)
                if top == "PySide6":
                    if mod == "PySide6":
                        pyside_mods.update(f"PySide6.{nm}" for nm in names if nm.startswith("Qt"))
                    else:
                        pyside_mods.add(mod)
    return {
        "mods": mods, "chain": chain, "third": third, "pyside_mods": sorted(pyside_mods),
        "syntax_errors": syntax_errors, "problems": problems,
    }


def source_digest(pkg_dir: Path, chain, mods):
    """起動経路の .py + web_ui.html + _resources/* のダイジェスト（改変検知用）。"""
    files = {mods[m] for m in chain if m in mods}
    for extra in [pkg_dir / "ui/sj_player/web_ui.html"]:
        if extra.is_file():
            files.add(extra)
    res = pkg_dir / "_resources"
    if res.is_dir():
        files.update(p for p in res.rglob("*") if p.is_file() and not p.name.startswith("."))
    per = {}
    for f in sorted(files):
        h = hashlib.sha256()
        with open(f, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        per[str(f.relative_to(pkg_dir)).replace(os.sep, "/")] = h.hexdigest()
    total = hashlib.sha256("".join(f"{k}:{v}\n" for k, v in sorted(per.items())).encode()).hexdigest()
    return total, per


def extract_alias_keys(pkg_dir: Path):
    """vj_win_actionman.py の defined_alias のキーを、importせずASTで取り出す。"""
    p = pkg_dir / "ui/sj_player/vj_win_actionman.py"
    tree = ast.parse(p.read_text(encoding="utf-8"))
    for n in tree.body:
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "defined_alias" for t in n.targets):
            return set(ast.literal_eval(n.value).keys())
    return None


def extract_port(pkg_dir: Path, default=5000):
    p = pkg_dir / "ui/sj_player/remote_app.py"
    try:
        m = re.search(r"port\s*=\s*(\d+)", p.read_text(encoding="utf-8"))
        return int(m.group(1)) if m else default
    except OSError:
        return default


# =============================================================================
# 小道具
# =============================================================================
def run_cmd(cmd, timeout=15):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
        return r.returncode, r.stdout, r.stderr
    except FileNotFoundError:
        return None, "", "not found"
    except subprocess.TimeoutExpired:
        return None, "", "timeout"


def human_bytes(n):
    for u in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or u == "TB":
            return f"{n:.1f}{u}" if u != "B" else f"{int(n)}B"
        n /= 1024


def ffprobe_json(path, timeout=30):
    rc, out, err = run_cmd(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        timeout=timeout,
    )
    if rc is None:
        return None, err
    if rc != 0:
        return None, (err.strip().splitlines() or ["ffprobe error"])[-1]
    try:
        return json.loads(out), ""
    except json.JSONDecodeError:
        return None, "ffprobe出力を解釈できない"


# =============================================================================
# 親プロセス側の検査（標準ライブラリのみ。環境が壊れていても必ず動く）
# =============================================================================
def check_env(rep, pkg_dir):
    g = "環境"
    now = datetime.datetime.now().astimezone()
    rep.add(g, "現在時刻", INFO, now.strftime("%Y-%m-%d %H:%M:%S %Z (UTC%z)  ※スケジュール運用がある場合は時計のずれに注意"))
    rep.add(g, "OS", INFO, platform.platform())
    v = sys.version_info
    if v >= (3, 12):
        rep.add(g, "Python 3.12 以上", OK, f"{platform.python_version()}  ({sys.executable})")
    else:
        rep.add(g, "Python 3.12 以上", FAIL,
                f"{platform.python_version()} ({sys.executable})\n"
                "vj_win_events.py の f-string が 3.12 構文のため起動不可。上映に使う Python で実行してください。")
    if pkg_dir.name == PKG:
        rep.add(g, f"フォルダ名が '{PKG}'", OK, str(pkg_dir))
    else:
        rep.add(g, f"フォルダ名が '{PKG}'", WARN,
                f"現在の名前: '{pkg_dir.name}'\n`python -m {PKG}` で起動できません（import名が一致しない）。"
                "この点検は別名として読み込んで続行します。")


def check_source(rep, pkg_dir, info, expect_digest):
    g = "ソース整合性"
    missing = [f for f in CORE_FILES if not (pkg_dir / f).is_file()]
    if missing:
        rep.add(g, "必須ファイル", FAIL, "欠落: " + ", ".join(missing))
    else:
        rep.add(g, "必須ファイル", OK, f"{len(CORE_FILES)} 件すべて存在")
    icon = pkg_dir / "_resources/icon.jpg"
    if icon.is_file() and icon.stat().st_size > 0:
        rep.add(g, "ウィンドウアイコン(_resources/icon.jpg)", OK, human_bytes(icon.stat().st_size))
    else:
        rep.add(g, "ウィンドウアイコン(_resources/icon.jpg)", WARN, "無い/空（アイコンが出ないだけで起動は可能）")

    chain = info["chain"]
    if info["syntax_errors"]:
        rep.add(g, "構文チェック(AST)", FAIL, "\n".join(info["syntax_errors"]))
    else:
        rep.add(g, "構文チェック(AST)", OK, f"起動経路 {len(chain)} モジュールすべて構文OK")
    if info["problems"]:
        rep.add(g, "内部import解決", FAIL, "\n".join(info["problems"]))
    else:
        rep.add(g, "内部import解決", OK, "起動経路内の shell_jekyll.* import はすべて解決")

    danger = [m for m in DANGEROUS_MODULES if m in chain]
    if danger:
        rep.add(g, "危険モジュールが起動経路に混入", WARN, ", ".join(danger) + "\nimport時にファイルを書き込む実装。点検では import しません。")
    else:
        rep.add(g, "scheduler_compiler.py", INFO,
                "起動経路には含まれない。import時に固定パスへファイルを書く実装なので、この点検も import しない。")

    try:
        digest, per = source_digest(pkg_dir, chain, info["mods"])
        d16 = digest[:16]
        detail = f"{d16}（先頭16桁 / 対象 {len(per)} ファイル: 起動経路の.py + web_ui.html + _resources）"
        if expect_digest:
            if digest.startswith(expect_digest.lower()):
                rep.add(g, "ソースのダイジェスト一致", OK, detail)
            else:
                rep.add(g, "ソースのダイジェスト一致", FAIL, f"期待 {expect_digest} / 実際 {d16}\n基準にした時点から内容が変わっています。")
        else:
            rep.add(g, "ソースのダイジェスト", INFO, detail + "\nリハーサル時の値を控え、本番前に --expect-digest で照合すると改変を検知できます。")
        info["digest_files"] = per
    except OSError as e:
        rep.add(g, "ソースのダイジェスト", WARN, f"計算できません: {e}")


def check_deps(rep, info):
    g = "依存ライブラリ"
    try:
        import importlib.metadata as md
        dist_map = md.packages_distributions()
    except Exception:
        md, dist_map = None, {}
    req_lines, missing_req = [], []
    for top in sorted(info["third"]):
        slot = info["third"][top]
        spec = None
        try:
            spec = importlib.util.find_spec(top)
        except (ImportError, ValueError):
            spec = None
        ver = ""
        if spec and md:
            for dist in dist_map.get(top, []):
                try:
                    ver = f"{dist} {md.version(dist)}"
                    break
                except Exception:
                    continue
        users = sorted(slot["req"] or slot["opt"])
        eg = ", ".join(u.replace(PKG + ".", "") for u in users[:2]) + (" ほか" if len(users) > 2 else "")
        if slot["req"]:
            if spec:
                req_lines.append((OK, f"{top}  {ver}  ← {eg}"))
            else:
                missing_req.append(top)
                rep.add(g, f"{top}", FAIL, f"未インストール（起動時に必須: {eg}）")
        else:
            st = INFO
            rep.add(g, f"{top}（任意・遅延import）", st,
                    (f"導入済 {ver}" if spec else "未導入") + f"  ← {eg}（使用時にだけ読み込まれる）")
    if req_lines:
        rep.add(g, f"必須ライブラリ {len(req_lines)} 件を検出", OK, "\n".join(f"{t}" for _, t in req_lines))
    rep.add(g, "補足", INFO,
            "launcher/vj_win_events が editor 側(MainUserUi)を import するため、\n"
            "editor 専用ライブラリ(OpenGL, cv2 等)が欠けても Player 単体が起動しません。")


def check_tools(rep):
    g = "外部ツール"
    for tool in ("ffmpeg", "ffprobe"):
        path = shutil.which(tool)
        if not path:
            rep.add(g, tool, WARN, "PATH に無い。Explode/Merge ボタンと本点検のメディア解析に必要（通常の再生だけなら不要）")
            continue
        rc, out, err = run_cmd([tool, "-version"], timeout=10)
        first = (out.splitlines() or [""])[0]
        if rc == 0:
            rep.add(g, tool, OK, f"{first}  ({path})")
        else:
            rep.add(g, tool, WARN, f"実行に失敗: {err.strip()[:120]}")


def _battery():
    """(on_ac:boolean|None, percent:int|None, raw:str)"""
    try:
        if sys.platform == "darwin":
            rc, out, _ = run_cmd(["pmset", "-g", "batt"], timeout=10)
            if rc != 0:
                return None, None, ""
            m = re.search(r"(\d+)%", out)
            pct = int(m.group(1)) if m else None
            if "AC Power" in out:
                return True, pct, out.splitlines()[0]
            if "Battery Power" in out:
                return False, pct, out.splitlines()[0]
            return None, pct, out.splitlines()[0] if out else ""
        if sys.platform.startswith("linux"):
            base = Path("/sys/class/power_supply")
            bats = sorted(base.glob("BAT*")) if base.is_dir() else []
            if not bats:
                return None, None, ""
            pct = int((bats[0] / "capacity").read_text().strip())
            status = (bats[0] / "status").read_text().strip()
            return status != "Discharging", pct, status
        if sys.platform == "win32":
            import ctypes

            class SPS(ctypes.Structure):
                _fields_ = [("AC", ctypes.c_ubyte), ("Flag", ctypes.c_ubyte), ("Pct", ctypes.c_ubyte),
                            ("Saver", ctypes.c_ubyte), ("Life", ctypes.c_ulong), ("Full", ctypes.c_ulong)]

            s = SPS()
            if ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(s)):
                pct = None if s.Pct == 255 else int(s.Pct)
                return (None if s.AC == 255 else s.AC == 1), pct, ""
    except Exception:
        pass
    return None, None, ""


def check_system(rep, pkg_dir):
    g = "システム状態"
    # 一時フォルダ: tempfile.gettempdir() は試し書きをするため使わず、os.access だけで判定
    cands = [os.environ.get(k) for k in ("TMPDIR", "TEMP", "TMP")] + ["/tmp", "/var/tmp"]
    cands = [c for c in cands if c and os.path.isdir(c)]
    usable = next((c for c in cands if os.access(c, os.W_OK | os.X_OK)), None)
    if usable:
        rep.add(g, "一時フォルダに書き込み可能", OK, f"{usable}（Web Remote のQR生成が使用）")
    else:
        rep.add(g, "一時フォルダに書き込み可能", FAIL, "書き込める一時フォルダが無い。Web Remote のQR生成が失敗します。")
    try:
        free = shutil.disk_usage(str(pkg_dir)).free
        st = OK if free >= 2 * 1024 ** 3 else WARN
        rep.add(g, "ディスク空き容量", st, f"{human_bytes(free)}（{pkg_dir} のあるボリューム）" + ("" if st == OK else "  ← 2GB未満"))
    except OSError as e:
        rep.add(g, "ディスク空き容量", WARN, f"取得できません: {e}")

    on_ac, pct, raw = _battery()
    if on_ac is None and pct is None:
        rep.add(g, "電源", INFO, "バッテリー情報なし（デスクトップ機、または取得不可）")
    elif on_ac is False:
        rep.add(g, "電源", WARN, f"バッテリー駆動中 {pct if pct is not None else '?'}%。上映中の電源断を避けるためACアダプタ接続を推奨。")
    else:
        st = WARN if (pct is not None and pct < 20) else OK
        rep.add(g, "電源", st, f"AC接続 / 充電 {pct if pct is not None else '?'}%")

    try:
        la = os.getloadavg()
        cores = os.cpu_count() or 1
        st = WARN if la[0] > cores else OK
        rep.add(g, "CPU負荷", st, f"load average 1/5/15分 = {la[0]:.2f} / {la[1]:.2f} / {la[2]:.2f}  (論理コア {cores})"
                + ("  ← 他の重い処理が動いていないか確認" if st == WARN else ""))
    except (AttributeError, OSError):
        pass
    try:
        import psutil  # 任意

        vm = psutil.virtual_memory()
        st = WARN if vm.available < 1024 ** 3 else OK
        rep.add(g, "メモリ空き", st, f"利用可能 {human_bytes(vm.available)} / 全体 {human_bytes(vm.total)}")
    except Exception:
        pass

    if sys.platform == "darwin":
        rc, out, _ = run_cmd(["pmset", "-g"], timeout=10)
        if rc == 0:
            vals = dict(re.findall(r"^\s*(sleep|displaysleep|disksleep)\s+(\d+)", out, re.M))
            if vals:
                rep.add(g, "スリープ設定（参考）", INFO,
                        "  ".join(f"{k}={v}分" for k, v in vals.items()) +
                        "\n0=無効。動画再生中の抑止はOS/アプリ任せ。気になる場合は事前に別途対策してください（本点検は設定を変更しません）。")


def check_network(rep, port):
    g = "ネットワーク"
    # アプリ(start_web_server)と同じ方法でLAN IPを求める。UDP connect はパケットを送らない。
    ip = None
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except OSError:
        ip = None
    finally:
        s.close()
    if ip is None or ip.startswith("127."):
        rep.add(g, "LAN IP（Web Remote のQR用）", WARN,
                "経路なし → アプリは 127.0.0.1 のQRを表示し、スマホから接続できません。Wi-Fi/LANに接続してください。")
    else:
        rep.add(g, "LAN IP（Web Remote のQR用）", OK, f"{ip}  → QR は http://{ip}:{port}")

    listeners = []
    method = ""
    if shutil.which("lsof"):
        method = "lsof"
        rc, out, _ = run_cmd(["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN"], timeout=10)
        for ln in out.splitlines()[1:]:
            cols = ln.split()
            if len(cols) >= 2:
                listeners.append((cols[0], cols[1]))
    else:
        method = "接続試行"
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                listeners.append(("(不明)", "?"))
        except OSError:
            pass
    if not listeners:
        rep.add(g, f"ポート {port} が空いている（Web Remote）", OK, f"LISTEN 無し（判定: {method}。bind はしていません）")
        return
    selfish, others = [], []
    for cmd, pid in listeners:
        full = ""
        if pid.isdigit():
            rc, out, _ = run_cmd(["ps", "-p", pid, "-o", "command="], timeout=5)
            full = out.strip()
        (selfish if PKG in full else others).append((cmd, pid, full))
    if selfish and not others:
        rep.add(g, f"ポート {port}", INFO, "Shell Jekyll 自身が使用中（既にWeb Remote起動済み）")
        return
    hint = ""
    if any(c.startswith("ControlCe") for c, _, _ in others):
        hint = "\nmacOS の AirPlay レシーバーが 5000 番を使う既知の問題。システム設定 > 一般 > AirDropとHandoff で AirPlayレシーバー をオフに。"
    rep.add(g, f"ポート {port} が空いている（Web Remote）", WARN,
            "他のプロセスが使用中 → Web Remote が起動できません（アプリ側は黙って失敗し、QRだけ表示される）:\n"
            + "\n".join(f"{c} (pid {p}) {f[:80]}" for c, p, f in others) + hint)


# ---------------------------------------------------------------------------
# 上映データ（.sjplay / .sjschedule）— 読み取りと ffprobe だけ
# ---------------------------------------------------------------------------
def _pairs_hook(pairs):
    d, dups = {}, []
    for k, v in pairs:
        if k in d:
            dups.append(k)
        d[k] = v
    if dups:
        d["__dups__"] = dups
    return d


def resolve_notation(k, my_dir):
    """アプリの _resolve_path_notation と同じ解釈（ただしダウンロードはしない）。"""
    if k.startswith("URL==="):
        parts = k.split("===")
        if len(parts) != 3:
            return "", {"bad": True}
        return parts[2].replace("$SELF$", my_dir), {"url": parts[1]}
    return k.replace("$SELF$", my_dir), {}


def check_playlists(rep, files, have_ffprobe, media_for_qt):
    g = "上映データ"
    for f in files:
        fp = Path(f)
        label = f"プレイリスト {fp.name}"
        try:
            with open(fp, "r", encoding="utf-8") as fh:
                data = json.load(fh, object_pairs_hook=_pairs_hook)
        except FileNotFoundError:
            rep.add(g, label, FAIL, f"ファイルが無い: {fp}")
            continue
        except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
            rep.add(g, label, FAIL, f"読めない/JSONではない: {e}")
            continue
        if not isinstance(data, dict):
            rep.add(g, label, FAIL, "トップレベルがオブジェクト(辞書)ではない")
            continue
        dups = data.pop("__dups__", [])
        if not data:
            rep.add(g, label, FAIL, "エントリが0件")
            continue
        my_dir = str(fp.resolve().parent)
        problems, warns, infos = [], [], []
        if dups:
            warns.append("重複キー（後勝ちで1つに潰れる）: " + ", ".join(dups))
        n = 0
        for k, v in data.items():
            n += 1
            if not isinstance(k, str) or not isinstance(v, str):
                problems.append(f"#{n}: キー/値が文字列ではない")
                continue
            vpath, vmeta = resolve_notation(k, my_dir)
            apath, ameta = resolve_notation(v, my_dir)
            for kind, path, meta, raw in (("映像", vpath, vmeta, k), ("音声", apath, ameta, v)):
                if meta.get("bad"):
                    warns.append(f"#{n} {kind}: URL=== 記法が不正（空文字として扱われる）: {raw[:60]}")
                    continue
                if "url" in meta:
                    warns.append(
                        f"#{n} {kind}: URL記法 → 読込のたびにダウンロードし、保存先を先に空にする。\n"
                        f"       通信不能だと既存ファイルが失われる恐れ。ローカルパスへ置換を推奨: {path}")
                if path and not os.path.isabs(path) and not path.startswith("$"):
                    warns.append(f"#{n} {kind}: 相対パスは起動時のカレントディレクトリ基準で解決される: {path}")
            # 映像
            if not vpath:
                problems.append(f"#{n}: 映像パスが空")
            elif not Path(vpath).is_file():
                problems.append(f"#{n} 映像が存在しない（アプリはエラーを出さず黙って無視する）: {vpath}")
            elif not os.access(vpath, os.R_OK) or Path(vpath).stat().st_size == 0:
                problems.append(f"#{n} 映像が読めない/0バイト: {vpath}")
            else:
                media_for_qt.append({"kind": "video", "path": str(Path(vpath)), "label": f"{fp.name}#{n}"})
            # 音声
            if not apath:
                infos.append(f"#{n}: 音声なし（映像の音のみ。Mute Video が既定ONなので無音になる点に注意）")
            elif not Path(apath).is_file():
                problems.append(f"#{n} 音声が存在しない（アプリはエラーを出さず黙って無視する）: {apath}")
            elif not os.access(apath, os.R_OK) or Path(apath).stat().st_size == 0:
                problems.append(f"#{n} 音声が読めない/0バイト: {apath}")
            else:
                media_for_qt.append({"kind": "audio", "path": str(Path(apath)), "label": f"{fp.name}#{n}"})
                if Path(apath).suffix.lower() != ".wav":
                    infos.append(f"#{n}: 音声が .wav ではない（Normalize loudness は .wav のみ対象）")
            # ffprobe
            if have_ffprobe:
                for kind, path, want in (("映像", vpath, "video"), ("音声", apath, "audio")):
                    if path and Path(path).is_file():
                        pj, err = ffprobe_json(path)
                        if pj is None:
                            problems.append(f"#{n} {kind} ffprobe失敗: {err}  ({Path(path).name})")
                            continue
                        kinds = [s.get("codec_type") for s in pj.get("streams", [])]
                        if want not in kinds:
                            problems.append(f"#{n} {kind}に {want} ストリームが無い: {Path(path).name}")
                        dur = pj.get("format", {}).get("duration")
                        try:
                            if dur is not None and float(dur) <= 0:
                                problems.append(f"#{n} {kind}の長さが0: {Path(path).name}")
                        except ValueError:
                            pass
        # 映像・音声の長さの差（INFOのみ）
        status = FAIL if problems else (WARN if warns else OK)
        det = []
        det.append(f"{n} 件")
        det += [f"✗ {p}" for p in problems] + [f"! {w}" for w in warns] + [f"· {i}" for i in infos]
        rep.add(g, label, status, "\n".join(det))


def check_schedules(rep, files, alias_keys):
    g = "上映データ"
    for f in files:
        fp = Path(f)
        label = f"スケジュール {fp.name}"
        try:
            with open(fp, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except FileNotFoundError:
            rep.add(g, label, FAIL, f"ファイルが無い: {fp}")
            continue
        except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
            rep.add(g, label, FAIL, f"読めない/JSONではない: {e}")
            continue
        if not isinstance(data, dict):
            rep.add(g, label, FAIL, "トップレベルがオブジェクトではない")
            continue
        tasks = data.get("tasks", [])
        timings = data.get("timings", [])
        problems, infos = [], []
        if not isinstance(tasks, list) or not all(isinstance(t, str) for t in tasks):
            rep.add(g, label, FAIL, "tasks が文字列のリストではない")
            continue
        if not tasks:
            problems.append("tasks が空（実行しても何も起きない）")
        if alias_keys is None:
            infos.append("defined_alias を読み取れず、コマンドの妥当性は未検証")
        else:
            for i, t in enumerate(tasks, 1):
                if t not in alias_keys:
                    problems.append(f"#{i} 未定義コマンド（そのまま Python として exec() される）: {t!r}")
            if tasks and "<SET>" not in tasks:
                infos.append("<SET> が無い: 事前に手動で Set 済みであることが前提（未Setだと再生系は何も起きない）")
        if timings:
            infos.append(f"timings {len(timings)} 件: 現行コードでは保存/読込のみで、実行時には参照されない（時刻起動はされない）")
        if "<WAIT>" in tasks:
            infos.append("<WAIT> は映像の再生終了(EndOfMedia)まで待つ。映像が読めないと永久に待機する")
        status = FAIL if problems else OK
        det = [f"tasks {len(tasks)} 件 / timings {len(timings) if isinstance(timings, list) else '?'} 件"]
        det += [f"✗ {p}" for p in problems] + [f"· {i}" for i in infos]
        rep.add(g, label, status, "\n".join(det))


# =============================================================================
# Qt検査（子プロセス）
# =============================================================================
def alias_package(pkg_dir: Path):
    """フォルダ名に関係なく 'shell_jekyll' として読み込む（ディスクには何も作らない）。"""
    spec = importlib.machinery.ModuleSpec(PKG, None, is_package=True)
    spec.submodule_search_locations = [str(pkg_dir)]
    mod = importlib.util.module_from_spec(spec)
    mod.__path__ = [str(pkg_dir)]
    sys.modules[PKG] = mod


def child_main(o):
    install_write_guard()
    try:
        import faulthandler

        faulthandler.enable()
    except Exception:
        pass
    G = "Qt実機検査"
    GD = "上映データ"

    def emit(group, name, status, detail=""):
        sys.stdout.write(MARK + json.dumps(
            {"group": group, "name": name, "status": status, "detail": detail}, ensure_ascii=True) + "\n")
        sys.stdout.flush()

    def step(name, fn, group=G):
        try:
            r = fn()
        except Exception as e:  # noqa
            tb = traceback.extract_tb(e.__traceback__)
            where = f"{Path(tb[-1].filename).name}:{tb[-1].lineno}" if tb else ""
            det = f"{type(e).__name__}: {e}" + (f"   @ {where}" if where else "")
            if "preshow_check: write blocked" in str(e):
                det += "\n（点検の書き込みガードが作動。何も書き込まれていません）"
            if o.get("verbose"):
                det += "\n" + traceback.format_exc()
            emit(group, name, FAIL, det)
            return False
        if r is None:
            emit(group, name, OK, "")
        elif isinstance(r, tuple):
            emit(group, name, r[0], r[1])
            return r[0] != FAIL
        else:
            emit(group, name, OK, str(r))
        return True

    pkg_dir = Path(o["pkg_dir"])
    alias_package(pkg_dir)
    ctx = {}
    slot_errors = []

    def s_pyside():
        import PySide6
        from PySide6 import QtCore
        mods = sorted(set(o.get("qt_modules") or []) | {"PySide6.QtCore"})
        for m in mods:
            importlib.import_module(m)
        short = ", ".join(m.split(".")[-1] for m in mods)
        return OK, f"PySide6 {PySide6.__version__} / Qt {QtCore.qVersion()}\nアプリが使う {len(mods)} モジュール: {short}"

    if not step("PySide6 と必要なQtモジュールのimport", s_pyside):
        return _child_finish(emit)

    def s_mods():
        failed = []
        for m in o["modules"]:
            try:
                importlib.import_module(m)
            except Exception as e:  # noqa
                failed.append(f"{m.replace(PKG + '.', '')}: {type(e).__name__}: {e}")
        if failed:
            ctx["mods_failed"] = True
            return FAIL, f"{len(o['modules']) - len(failed)}/{len(o['modules'])} 成功。失敗:\n" + "\n".join(failed[:12])
        detail = f"{len(o['modules'])}/{len(o['modules'])} モジュール（`python -m {PKG}` の起動経路）"
        return OK, detail

    step("起動経路モジュールの実import", s_mods)
    if ctx.get("mods_failed"):
        return _child_finish(emit)

    def s_app():
        from PySide6.QtWidgets import QApplication
        api = importlib.import_module(f"{PKG}.api")
        api.configure_surface_format()  # 本物の main() と同じ
        ctx["app"] = QApplication([sys.argv[0] or "preshow_check"])
        pf = ctx["app"].platformName()
        if pf in ("offscreen", "minimal") and not o.get("offscreen"):
            return WARN, f"QPA platform = {pf}（実画面ではない）"
        return OK, f"QApplication 生成OK / platform={pf}"

    if not step("GUIセッションに接続(QApplication)", s_app):
        return _child_finish(emit)
    app = ctx["app"]

    def s_screens():
        scr = app.screens()
        if not scr:
            return FAIL, "ディスプレイが1つも見えない"
        lines, names = [], []
        for s in scr:
            g = s.geometry()
            names.append(s.name())
            lines.append(f"{s.name()}  {g.width()}x{g.height()} @({g.x()},{g.y()})  {s.refreshRate():.0f}Hz  dpr={s.devicePixelRatio():g}"
                         + ("  [主]" if s == app.primaryScreen() else ""))
        st, notes = OK, []
        if len(set(names)) != len(names):
            st = WARN
            notes.append("同名のディスプレイあり → アプリの選択肢(name→screen辞書)が1つに潰れ、片方を選べない")
        n = o.get("expect_displays")
        if n and len(scr) < n:
            st = FAIL
            notes.append(f"期待 {n} 台に対し {len(scr)} 台しか見えない")
        e = o.get("expect_display")
        if e and not any(e.lower() in s.name().lower() for s in scr):
            st = FAIL
            notes.append(f"'{e}' を含む名前のディスプレイが無い")
        return st, f"{len(scr)} 台\n" + "\n".join(lines + notes)

    step("ディスプレイ", s_screens)

    def s_audio():
        from PySide6.QtMultimedia import QMediaDevices
        devs = QMediaDevices.audioOutputs()
        default = QMediaDevices.defaultAudioOutput()
        if not devs:
            return FAIL, "音声出力デバイスが0台 → Set ボタンで例外（辞書が空）になり再生を準備できない"
        descs = [d.description() for d in devs]
        lines = [f"{d.description()}  ch<={d.maximumChannelCount()}" + ("  [既定]" if d.id() == default.id() else "") for d in devs]
        st, notes = OK, []
        if len(set(descs)) != len(descs):
            st = WARN
            notes.append("同名の出力デバイスあり → アプリの選択肢が1つに潰れる")
        e = o.get("expect_audio")
        if e and not any(e.lower() in d.lower() for d in descs):
            st = FAIL
            notes.append(f"'{e}' を含む名前の出力が無い")
        notes.append("※アプリは Player 画面を開いた時点のデバイス一覧を使用。点検後に機器を抜き差ししたら Player 画面を開き直すこと。")
        return st, f"{len(devs)} 台\n" + "\n".join(lines + notes)

    step("音声出力デバイス", s_audio)

    def s_settings():
        from PySide6.QtCore import QSettings
        st = QSettings("Shell Tech", "Shell Jekyll")
        ctx["has_default_style"] = st.contains("default_style_sheet")
        if ctx["has_default_style"]:
            return OK, f"default_style_sheet = {st.value('default_style_sheet')!r}"
        return INFO, ("default_style_sheet は未保存（このPCで一度も [Default] を押していない）。\n"
                      "この状態でもランチャーが生成できるかは、次の「ランチャー画面の生成」の結果で判断してください。")

    step("QSettings(読み取りのみ)", s_settings)

    def s_icon():
        # QIcon.isNull() は存在しないファイルでも False になるため、実際にデコードして確かめる
        from PySide6.QtGui import QPixmap
        p = pkg_dir / "_resources/icon.jpg"
        if QPixmap(str(p)).isNull():
            return WARN, "アイコンを読み込めない（表示されないだけ）"
        return OK, "アイコン読込OK"

    step("アイコン画像のデコード", s_icon)

    def s_launcher():
        from PySide6.QtWidgets import QMainWindow
        launcher = importlib.import_module(f"{PKG}.ui.launcher")
        # 本物の __main__.main() と同じ手順。ただし show()/exec() はしない。
        ctx["window"] = QMainWindow()
        try:
            ctx["launcher"] = launcher.LauncherUi()
        except Exception as e:  # noqa
            ctx["launcher_err"] = f"{type(e).__name__}: {e}"
            raise
        ctx["window"].setCentralWidget(ctx["launcher"])
        return OK, "LauncherUi 生成OK（表示はしない）"

    if not step("ランチャー画面の生成(本物の起動手順・非表示)", s_launcher):
        err = ctx.get("launcher_err", "")
        if not ctx.get("has_default_style") and ("setCurrentText" in err or "NoneType" in err):
            emit(G, "補足(ランチャー失敗)", INFO,
                 "QSettings の default_style_sheet が未保存で、launcher.py がその値をそのまま setCurrentText() に渡しているため、"
                 "これが原因の可能性があります。上映PCで一度ランチャーの [Default] を押して保存すると解消する見込みです（点検スクリプトは設定を変更しません）。")

    # 例外監視（以後のスロット内例外もここに集まる）
    old_hook = sys.excepthook
    sys.excepthook = lambda t, v, tb: slot_errors.append(f"{t.__name__}: {v}")

    def s_vj():
        if "launcher" not in ctx:
            return SKIP, "ランチャーが生成できないため省略"
        ctx["launcher"].go_vj()  # 本物の画面遷移。VjUserUi が生成される
        vj = ctx["window"].centralWidget()
        if type(vj).__name__ != "VjUserUi":
            return FAIL, f"Player画面に遷移できない（中央ウィジェット={type(vj).__name__}）"
        ctx["vj"] = vj
        pw = vj.main_player_window_widget
        return OK, (f"VjUserUi 生成OK / Display選択肢 {vj.display_selection_combo.count()} / "
                    f"Audio選択肢 {vj.audio_device_selection_combo.count()} / "
                    f"再生ウィンドウ {type(pw).__name__}（表示はしない）")

    step("Player画面の生成(非表示) — QMediaPlayer/QVideoWidget/アクションマネージャ含む", s_vj)

    def s_flask():
        rm = importlib.import_module(f"{PKG}.ui.sj_player.remote_app")
        c = rm.app.test_client()
        r = c.get("/")
        if r.status_code != 200 or b"Remote Controller" not in r.data:
            return FAIL, f"GET / が不正 (status={r.status_code})"
        rules = {rule.rule: set(rule.methods) for rule in rm.app.url_map.iter_rules()}
        if "POST" not in rules.get("/<action>", set()):
            return FAIL, "POST /<action> ルートが無い"
        return OK, f"GET / → 200 ({len(r.data)} bytes) / POST /<action> ルート有り / 想定ポート {o['port']}（サーバは起動していない・操作POSTもしていない）"

    step("Web Remote アプリ(Flask test_client・サーバ非起動)", s_flask)

    def s_qr():
        import io
        import qrcode
        from PySide6.QtGui import QPixmap
        img = qrcode.make(f"http://192.168.0.10:{o['port']}")
        buf = io.BytesIO()
        img.save(buf)  # メモリ上のみ。ディスクには書かない
        pm = QPixmap()
        if not pm.loadFromData(buf.getvalue()) or pm.isNull():
            return FAIL, "QRのPNGをQtが読み込めない"
        return OK, f"QR生成→Qtで表示可能 ({pm.width()}x{pm.height()}px)"

    step("QRコード生成と表示(メモリ上のみ)", s_qr)

    def s_soak():
        secs = float(o.get("soak") or 0)
        if secs <= 0:
            return SKIP, "--soak 0 のため省略"
        from PySide6.QtCore import QCoreApplication, QEventLoop
        before = len(slot_errors)
        t0 = time.monotonic()
        spins = 0
        while time.monotonic() - t0 < secs:
            QCoreApplication.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 20)
            time.sleep(0.005)
            spins += 1
        new = slot_errors[before:]
        if new:
            return FAIL, f"{secs:g}秒のイベントループ中に例外 {len(new)} 件:\n" + "\n".join(new[:5])
        return OK, f"{secs:g}秒間イベントループを回して例外なし（Player画面生成済みの状態）"

    step("短時間の安定稼働(イベントループ)", s_soak)

    def s_media():
        items = o.get("media") or []
        if not items:
            return
        from PySide6.QtCore import QCoreApplication, QEventLoop, QUrl
        from PySide6.QtMultimedia import QMediaPlayer
        per = float(o.get("media_timeout", 12))
        for it in items:
            name = f"Qtで読込 {Path(it['path']).name} ({it['label']})"
            player = QMediaPlayer()
            errs = []

            def on_err(code, text, _errs=errs):
                _errs.append(text)

            player.errorOccurred.connect(on_err)
            player.setSource(QUrl.fromLocalFile(it["path"]))
            t0 = time.monotonic()
            final = None
            while time.monotonic() - t0 < per:
                QCoreApplication.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 30)
                stt = player.mediaStatus()
                if stt in (QMediaPlayer.MediaStatus.LoadedMedia, QMediaPlayer.MediaStatus.BufferedMedia,
                           QMediaPlayer.MediaStatus.InvalidMedia):
                    final = stt
                    break
                time.sleep(0.01)
            ok_loaded = final in (QMediaPlayer.MediaStatus.LoadedMedia, QMediaPlayer.MediaStatus.BufferedMedia)
            dur, hv, ha = player.duration(), player.hasVideo(), player.hasAudio()
            player.setSource(QUrl())
            player.deleteLater()
            if not ok_loaded:
                why = errs[0] if errs else ("タイムアウト" if final is None else "InvalidMedia")
                emit(GD, name, FAIL, f"Qtが開けない: {why}")
                continue
            st, notes = OK, []
            if it["kind"] == "video" and not hv:
                st = WARN
                notes.append("映像ストリームを認識していない")
            if it["kind"] == "audio" and not ha:
                st = FAIL
                notes.append("音声ストリームを認識していない")
            if dur <= 0:
                st = FAIL if st == OK else st
                notes.append("長さが取得できない")
            emit(GD, name, st, f"{it['kind']} / {dur / 1000:.1f}s / video={hv} audio={ha}（再生はしていない）" +
                 ("".join("\n" + n for n in notes)))
        return None

    # media は個別に emit するので step の「OK」自動出力を避けるため直接呼ぶ
    try:
        s_media()
    except Exception as e:  # noqa
        emit(GD, "メディア読込テスト", FAIL, f"{type(e).__name__}: {e}")

    sys.excepthook = old_hook
    return _child_finish(emit)


def _child_finish(emit):
    if _VIOLATIONS:
        emit("点検自身の安全性", "Qt検査中の書き込み試行(拒否済み)", WARN,
             f"{len(_VIOLATIONS)} 件。点検対象コードが書き込もうとしたが、ガードが拒否した（何も変更されていない）:\n" +
             "\n".join(f"{e}: {a}" for e, a in _VIOLATIONS[:6]))
    sys.stdout.write(MARK + json.dumps({"done": True}) + "\n")
    sys.stdout.flush()
    os._exit(0)  # Qt の終了処理で稀に落ちるのを避ける


def run_qt_child(rep, pkg_dir, info, args, media):
    g = "Qt実機検査"
    opts = {
        "pkg_dir": str(pkg_dir),
        "modules": [m for m in info["chain"] if m not in DANGEROUS_MODULES],
        "qt_modules": info["pyside_mods"],
        "soak": args.soak, "port": info["port"], "media": media,
        "expect_displays": args.expect_displays, "expect_display": args.expect_display,
        "expect_audio": args.expect_audio, "offscreen": args.offscreen,
        "verbose": args.verbose, "media_timeout": 12,
    }
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    if args.offscreen:
        env["QT_QPA_PLATFORM"] = "offscreen"
    cmd = [sys.executable, "-B", str(Path(__file__).resolve()), "--_child", json.dumps(opts)]
    timeout = args.timeout + 15 * len(media)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL, env=env)
    timed_out = False
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate()
        timed_out = True
    out = (out or b"").decode("utf-8", "replace")
    err = (err or b"").decode("utf-8", "replace")
    done = False
    for ln in out.splitlines():
        if not ln.startswith(MARK):
            continue
        try:
            d = json.loads(ln[len(MARK):])
        except json.JSONDecodeError:
            continue
        if d.get("done"):
            done = True
            continue
        rep.add(d["group"], d["name"], d["status"], d.get("detail", ""))
    if timed_out:
        rep.add(g, "Qt検査の完走", FAIL, f"{timeout}秒でタイムアウト（ハング）。直前の項目で止まっています。")
    elif not done:
        tail = "\n".join([l for l in err.strip().splitlines() if l.strip()][-12:])
        hint = ""
        if proc.returncode is not None and proc.returncode < 0:
            hint = f"（シグナル {-proc.returncode} で異常終了）"
        rep.add(g, "Qt検査の完走", FAIL, f"子プロセスが途中で終了 rc={proc.returncode}{hint}\n" +
                ("GUIセッションが無い(SSH接続等)場合もここで落ちます。\n" if not args.offscreen else "") + tail)
    elif args.verbose and err.strip():
        rep.add(g, "Qtからの警告出力(stderr)", INFO, "\n".join(err.strip().splitlines()[-15:]))


# =============================================================================
# main
# =============================================================================
def locate_package(arg):
    cands = []
    if arg:
        cands.append(Path(arg))
    else:
        here = Path(__file__).resolve().parent
        cands += [here, Path.cwd(), here / PKG, Path.cwd() / PKG]
    for c in cands:
        c = c.expanduser().resolve()
        if (c / "__main__.py").is_file() and (c / "api.py").is_file():
            return c
    return None


def build_parser():
    ap = argparse.ArgumentParser(description="Shell Jekyll Player 上映前点検（読み取り専用）")
    ap.add_argument("package", nargs="?", help="shell_jekyll フォルダ（省略時は自動検出）")
    ap.add_argument("--playlist", action="append", default=[], metavar="FILE.sjplay",
                    help="点検するプレイリスト（複数なら繰り返し指定）")
    ap.add_argument("--schedule", action="append", default=[], metavar="FILE.sjschedule",
                    help="点検するスケジュール（複数なら繰り返し指定）")
    ap.add_argument("--expect-displays", type=int)
    ap.add_argument("--expect-display")
    ap.add_argument("--expect-audio")
    ap.add_argument("--expect-digest")
    ap.add_argument("--soak", type=float, default=3.0)
    ap.add_argument("--timeout", type=int, default=90, help="Qt検査のタイムアウト秒（既定90）")
    ap.add_argument("--no-qt", action="store_true")
    ap.add_argument("--offscreen", action="store_true", help="（開発用）QT_QPA_PLATFORM=offscreen で実画面なしに検査")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    ap.add_argument("--_child", help=argparse.SUPPRESS)
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args._child:
        child_main(json.loads(args._child))
        return 0

    install_write_guard()
    rep = Report()
    pkg = locate_package(args.package)
    if pkg is None:
        print("shell_jekyll フォルダを見つけられません。パスを引数で指定してください。\n"
              "  例: python3 preshow_check.py /path/to/shell_jekyll", file=sys.stderr)
        return 2

    info = analyze(pkg)
    info["port"] = extract_port(pkg)

    check_env(rep, pkg)
    check_source(rep, pkg, info, args.expect_digest)
    check_deps(rep, info)
    check_tools(rep)
    check_system(rep, pkg)
    check_network(rep, info["port"])

    media = []
    have_ffprobe = bool(shutil.which("ffprobe"))
    if args.playlist:
        if not have_ffprobe:
            rep.add("上映データ", "ffprobe 不在", WARN, "映像/音声の中身(ストリーム・長さ)の事前解析を省略。Qtでの読込テストのみ行います。")
        check_playlists(rep, args.playlist, have_ffprobe, media)
    if args.schedule:
        check_schedules(rep, args.schedule, extract_alias_keys(pkg))

    fatal_static = bool(info["syntax_errors"] or info["problems"]) or any(
        not (pkg / f).is_file() for f in CORE_FILES)
    if args.no_qt:
        rep.add("Qt実機検査", "Qtを使う検査", SKIP, "--no-qt 指定。実機のディスプレイ/音声デバイス/画面生成は未検査です。")
    elif fatal_static:
        rep.add("Qt実機検査", "Qtを使う検査", SKIP, "ソース整合性にFAILがあるため省略（先にそちらを解消してください）。")
    elif sys.version_info < (3, 12):
        rep.add("Qt実機検査", "Qtを使う検査", SKIP, "Pythonが古いため省略。")
    else:
        run_qt_child(rep, pkg, info, args, media)

    # 親プロセス側のガード結果
    if _VIOLATIONS:
        rep.add("点検自身の安全性", "親プロセスでの書き込み試行(拒否済み)", WARN,
                "\n".join(f"{e}: {a}" for e, a in _VIOLATIONS[:6]))
    else:
        rep.add("点検自身の安全性", "書き込みガード", OK,
                "監査フックでファイル作成/削除/改名/権限変更/ポートbindを拒否。.pyc も作成しない。")

    if args.json:
        print(json.dumps({
            "verdict": "NG" if rep.count(FAIL) else ("CHECK" if rep.count(WARN) else "OK"),
            "counts": {s: rep.count(s) for s in (OK, INFO, WARN, FAIL, SKIP)},
            "blocked_write_attempts": len(_VIOLATIONS),
            "results": rep.items,
        }, ensure_ascii=False, indent=2))
    else:
        header = [
            "=" * 64,
            " Shell Jekyll Player 上映前点検（読み取り専用・何も変更しません）",
            f" 対象: {pkg}",
            f" 実行: {datetime.datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S')}  /  Python {platform.python_version()}",
            "=" * 64,
        ]
        print(render(rep, header, args.verbose))
    return 2 if rep.count(FAIL) else (1 if rep.count(WARN) else 0)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
