# Shell Jekyll 改修記録

元のコードの構造(`gb_var` / `TimeMap` → `EditingUtils` → OpenGL ウィジェット、という流れ)と
Mixin 構成は維持し、機能の増減はせずに、バグ・冗長・未稼働コードの修正と、ご依頼の5項目を実装しました。
変更した関数・クラスには docstring を付け、`[Changed]` / `[Added]` で変更箇所と理由を書いてあります。

## 0. 使い方

- この zip の中身は **パッケージ `shell_jekyll` の中身そのもの**(元の zip と同じ構成)です。
  `shell_jekyll` という名前のフォルダに展開し、そのフォルダの親で `python -m shell_jekyll [スタイル名]` を実行します。
- 依存: PySide6, PyOpenGL, numpy, opencv-python, psutil(従来どおり)。TCL 式には tkinter、CEL 式には `cel_expr_python`(従来どおり)。
  ただし両者は **使うときに初めて import** します(無くてもアプリは起動します)。
- UI なしで使う: `from shell_jekyll.api import ShellJekyll`(第6章)。
- 簡易テスト: `python tests/test_api_headless.py`(Qt / OpenGL 不要)。

## 1. 検証状況(正直に)

作業環境では PySide6 / PyOpenGL をインストールできませんでした(pypi.org / apt への接続が組織ポリシーで拒否)。
そのため **実物の Qt での動作確認はしていません**。代わりに次の方法で検証しました。

| 検証 | 方法 | 結果 |
|---|---|---|
| 状態管理・IO・フレーム解決・レンダー・式ループ・API | 実コードをそのまま実行(PNG連番を生成、OpenCV で動画を書き出して再読込) | 合格 |
| **GLSL・VBO(画素バッファ)描画** | **Mesa のソフトウェア GL(EGL)上で、実際の `gl_frame_store.py` / `opengl.py` / `.glsl` を実行**。PyOpenGL の代わりに ctypes の薄い代用品を使用 | 合格 |
| UI ロジック(QShortcut、Mixin、イベント連携、再生) | Qt を模した代用品でメインウィンドウを組み立て、ショートカット発火→コントローラ→**本物の GL 描画→ピクセル確認**まで通した | 合格 |

GL の合格項目: 2層合成(レイヤー0が最前面)/ 何度再描画しても順序が変わらない / 表示切替 / アスペクト比 /
双線形補間(参照実装と差0)/ **プリロード後のフレーム切替でGPUアップロード0回** / 複数バッファページ /
複数ページへの分割保持 / 欠損画像のフォールバック / カスタムGLSL(適用・コンパイルエラー時は直前のシェーダーを維持・uniform・全面差し替え)。

**未確認(お手元で最初に試してください)**
1. 実機の PySide6 での `QShortcut` の挙動(特に FPS 欄など入力欄に文字を打てること、Return で `editingFinished` が効くこと)
2. `QOpenGLWidget` の実環境での表示(HiDPI 含む)。PyOpenGL の呼び出しは元コードと同じ API ですが、実物では未実行です
3. `QMediaPlayer` と実際の動画でのリアルタイム再生(フレーム→時間→連番の計算と描画経路は確認済み。動画デコード自体は未確認)
4. TCL 式(tkinter が無く未実行)と CEL 式(ライブラリが無く未実行)。式ループ本体は偽の評価関数で確認
5. 画面が真っ黒になった場合: `window.centralWidget().gl_widget.shader_error` にシェーダーのコンパイルログが入ります

## 2. ご依頼との対応

### 追加依頼

| # | 依頼 | 実装 |
|---|---|---|
| 1 | テクスチャ切替 → VBO | 全フレームの画素を GPU のバッファオブジェクトに格納し、GLSL が `texelFetch` で読む方式(ご選択どおり)。`ui/gl_frame_store.py` 新規。フレーム切替はオフセットの uniform を変えるだけ。1バッファの上限(`GL_MAX_TEXTURE_BUFFER_SIZE`)を超える場合は複数ページに自動分割 |
| 2 | リアルタイムプレビューの修復 | 原因は第4章。`ref_video_proceed` → `ShellJekyll.ref_video_proceed` → VBOストアから表示、で動作(30フレーム再生でアップロード0回を確認) |
| 3 | UI操作の関数集約 | `api.py` の `ShellJekyll`(第6章)。メインウィンドウはダイアログとキー入力を受けて呼ぶだけの薄い層に |
| 4 | QShortcut に集約 | `ui/main_win/main_win_shortcuts.py`(第7章)。`keyPressEvent` 約140行と `LayerListWidget.keyPressEvent` の重複を表1つに |
| 5 | 任意GLSL | `set_effect_shader` / `set_shader_sources` / `set_custom_uniform`(第8章) |

### 基本方針

- 論理・データの流れの維持: `seq_idx →(time_map)→ 実画像番号 →(ファイル名テンプレート)→ レイヤーごとのパス → GL` は同じです。関数名も可能な限り維持しました。
- 機能は増減していません(ただし、元々動いていなかった機能は動くようにしてあります。第3・4章)。
- コード量: 非スタイル `.py` が 2,088行 → 3,045行に増えました。主に docstring と新規モジュール(`api.py` / `gl_frame_store.py`)で、`keyPressEvent`・`opengl_single.py`(157→20行)・`main_win_io.py`(194→53行)などは短くなっています。
- スタイル 4 ファイル(`style/*.py`)は一切変更していません。

## 3. 修正したバグ

**★ = 元のコードで実際に再現を確認したもの**(元コードを動かして確認)。それ以外はコード読解で確定したものです。

| 場所 | 内容 |
|---|---|
| `render/render.py` ★ | `get_actual_filepath` に必須引数 `layer` を渡しておらず `TypeError` で**レンダーが一度も動かない**。時間マップ判定が「dict のリスト」に対する `in` で常に偽。サイズ違いの画像は黙って捨てられる |
| `gb_var.restack_layers` ★ | レイヤーを2回以上入れ替えると `layer_order`(ラベル)とデータの対応が崩れる(3回入れ替えの再現:データ `[a,c,b]` に対しラベルが `[b,a,c]`)。保存すると壊れた状態で保存される |
| `open_sequence` ★ | 1層目の `base_frame_list` が空 `[[]]` に上書きされる(`switch_layer` が古い作業コピーを書き戻すため)。結果 `seq_count` が0になり、保存→再読込するまで式の結果がすべて無視される |
| `opengl.paintGL` | 描画のたびに `self.texture = self.texture[::-1]` でレイヤー順が反転。可視/サイズ基準も反転した行を指していた |
| `opengl.change_image_onram` | `list` を dict のキーにして `TypeError`、それを `except: pass` で握りつぶす。フォールバック値は `str` なのにタプルとして添字アクセス |
| `opengl.send_img_to_buffer` | パス文字列の**1文字ずつ**を画像として読もうとしていた(`[i][j]` の添字誤り)→ 何もバッファされない |
| `opengl_single.py` | `paintGL` でレイヤー uniform を設定しておらず、**参照ビューアが常に真っ黒** |
| `expression_widgets` (TCL) | ループ変数 `frame` をループ前に参照 → `UnboundLocalError`。TCL 式が一度も動かない。毎フレームエンジン再生成+プロジェクト再読込 |
| `__main__.py` | 未知のスタイル名で `style_script` に**文字列** `"dark_default"` が入り `AttributeError`。アイコンのパスが存在しない(`icon` → `icon.jpg`) |
| `io_sjproj` | 拡張子処理が `"".join(split("."))` でパス中の他のドットも消す。`load_sjproj` が `TimeMap` を追記するだけで、2回開くとレイヤーが倍になる。`ref_path` 未設定を文字列 `"None"` で保存 |
| 参照動画パス / 開始位置 | `GBVar_CTX` にしか入らず `GBVar` に書き戻されないため、**保存されない**。さらに最初のシーケンス読込前に選ぶと消える |
| `save_proj` | 新規保存なのに `getOpenFileName`(既存ファイルしか選べない)。未読込で `KeyError` |
| `render_sequence` | `int("29.97")` で `ValueError`(FPS欄は小数を許す) |
| `move_sequence` | 未使用変数のために `time_map[...][actual_img_idx]` を引き、`actual_img_idx = -1` などで `KeyError` |
| `switch_active_layer` | 同様の二重参照(`time_map[layer][actual_img_idx]`)で誤った番号を表示/`KeyError`。リスト `clear()` 時の行 -1 が「最後のレイヤー」を選択してしまう |
| `ref_video_proceed` | 全レイヤーに「アクティブレイヤーのフォルダ」を使っていた。表示ラベルが最後のレイヤーの番号になる |
| `LayerListWidget.keyPressEvent` | 他のキーを全て握りつぶし、リストにフォーカスがあると左右キーが効かない。`T` キーは `print("Hello")` のスタブ |
| `GBVar` ほか | 未読込状態でキー/ボタンを押すと `KeyError`(`has_sequence()` で防止)。`get_base_frames` が `None` を返し後続で落ちる。層の上限(8)超過で配列がずれる |
| `TCLEngine` | プロジェクト未保存時に `self.expression` が未定義で `AttributeError`。起動時に `tkinter` を import(無いとアプリが起動しない) |
| 動作しない記述 | `lo.addStretch` / `dialog_lo.addStretch` / `video_lo.addSpacing`(括弧が無く何もしない行)、`on_finished`(接続されていない)、各所のデバッグ `print`(`asdict` で全データを毎回出力) |

## 4. リアルタイムプレビューが動かなかった原因

1. `send_img_to_buffer` が何もバッファしない(上表)
2. `change_image_onram` が毎回例外 → `except: pass` で隠される(上表)
3. 再生中のパス構築が他のレイヤーのフォルダを使う(上表)

これらを、`FrameStore`(GPUバッファ)への一括プリロード+`ref_video_proceed` からの切替に置き換えて修復しました。
`on_finished`(動画終了で Play を再び有効にする)は存在するのに接続されていなかったので接続しました。

## 5. 私が下した判断(確認してください)

指示にない部分で私が選んだことを、すべて書きます。違う場合は教えてください。

1. **レイヤー順**: リスト行0 = 最前面。元の `paintGL` の反転は「行0を最前面にする」意図と読み、反転をシェーダー内の固定順序に置き換えました。これに伴い、可視切替(H)とサイズ基準(S)は選択した**行**に正しく作用します(元はミラー側のレイヤーに作用)。
2. **参照ビューア**: 元は動かない別実装だったため、`OpenGLImageWidget` を1レイヤーで使う形(サブクラス)にしました。
3. **レンダー**: 対象は**アクティブレイヤーのみ**(元の `gb_var.sequence_root_dir` の意味)。画像サイズが指定サイズと違う場合は**引き伸ばし**(`cv2.resize`、レターボックスではない)。時間マップの解決はプレビューと同じ規則(マップに無い位置は直前のフレームを保持)。書き込み失敗時はエラーダイアログを出してダイアログを閉じません(追加したUI)。
4. **新しいレイヤーを開いたらリストの選択をそのレイヤーに**(元はアクティブレイヤーと選択行がずれていた)。
5. **参照ビューのホバー検知**: `mouseMoveEvent` だけでは子ウィジェットの上で発火しないため、`eventFilter`(Enter/Leave)を追加しました。実マウスでは未確認です。
6. **ショートカットの範囲**: `WidgetWithChildrenShortcut`(メインウィンドウと子ウィジェットにフォーカスがあるとき)。入力欄は文字キーを優先します。`Return` は「数字入力中」だけ有効にしています(常時有効だと FPS 欄などの Enter を奪うため)。テンキーの Enter は元どおり対象外です。
7. **層の上限**: 9層目は追加を拒否(ログのみ。元は配列がずれていた)。
8. **`on_finished`** は「Back」ボタンも再有効化します(Play が無効の間 Back も無効にしているため)。
9. **互換の保持**: `ref_path` が `"None"`(旧形式)のファイルも読めます。時間マップが無い層は恒等マップで補います。保存は一時ファイル経由で原子的に書きます。
10. **`graphics/`**: 空ディレクトリ(`player.cpython-313.pyc` の残骸のみ)・`__pycache__`・`__MACOSX`・`.DS_Store`・古い `.pyc` は zip から除きました。
11. **GLSL 配列長** `MAX_LAYERS 16` → `8`(if 連鎖が8までのため。`gb_var.MAX_LAYER` と一致)。`MAX_LAYER` の定義は5か所 → `gb_var` の1か所に。
12. **`resizeGL` / `glViewport` の削除**: `QOpenGLWidget` が `paintGL` 前にデバイスピクセルで設定するため、論理ピクセルで設定する元の処理は HiDPI で不適切でした。

## 6. 変更しなかったが気になる点(判断を保留)

- **再生時の連番の起点**: 動画の最初のフレームは `seq_idx = 0`(開始位置を引いた値)になります。連番が1始まりだと最初の1フレームだけフォールバック画像になります。元の仕様か意図的かが読み取れないため変更していません。
- **TCL の呼び出し規約**: 引数を「`key value ...` を平坦化した**1つのリスト**」として渡す元の書き方のままです(`*` 展開の意図の可能性もあります)。スクリプト側の `proc` の受け方に依存するので、TCL 側と合っているか確認してください。毎回スクリプトを再評価する点も元のままです。
- **`GBVar.layer_visibility`** はどこからも使われていません。可視設定は「リスト行」に結び付いており、レイヤーを入れ替えても行に残ります。
- **「Release Buff. (%)」** の数字はシステムメモリ使用率のままです(GPUメモリではありません)。プリロードはUIスレッドで同期実行です(元と同じ)。
- **`GLSL` / `Python` のコンボ項目** は元から予約枠(TCLウィジェットに割り当てられる)のままです。
- `EditingUtils.get_actual_img_idx` の「前方を1つずつ遡る」探索は元のままです(長い連番で非常に大きい `seq_idx` を指定すると遅くなります)。
- `style/*.py` の4ファイルはほぼ同一の重複ですが、手を付けていません。
- 状態(`gb_var` / `TimeMap`)はプロセス全体で1つ(元と同じ)。`ShellJekyll` を複数作っても同じプロジェクトを共有します。

## 7. Python API(UIなし)

```python
from shell_jekyll.api import ShellJekyll
sj = ShellJekyll()

sj.open_sequence("/shots/bg/bg_0001.png")        # レイヤー追加。戻り値 = レイヤー番号
sj.open_reference("/shots/ref.mp4")              # 参照動画(FPS を返す)
sj.mark_ref_start(1500)                          # "Mark as Start"(ms)
sj.read_proj("/shots/a.sjproj") / sj.save_proj("/shots/a.sjproj")

sj.show_frame(5) / sj.move_sequence(is_foward=True, increment_step=10) / sj.assign_frame(seq_idx=10, img_idx=3)
sj.show_ref_frame(2)
sj.switch_active_layer(1) / sj.move_layer(row=1, direction=-1)
sj.toggle_layer_visibility(0, mode=1)            # 1:切替 2:ソロ 3:全表示
sj.switch_size_standard(layer=0)

sj.run_cel_expression("(frame - 1) % seq_count + 1", 1, 48)
sj.run_tcl_expression("myproc", 1, 48); sj.get_tcl_procs(); sj.get_expression(); sj.save_expression(text)
sj.render_video("/out", "clip", codec="MPEG-4 Video", container="MPEG-4 Part 14", size=(1920, 1080), export_range=(1, 48))

# プレビュー(Qt/OpenGL が必要。ウィンドウ不要)
view = sj.create_preview(); sj.preload_frames(); sj.ref_video_proceed(time_us=500_000)
sj.grab_preview().save("/tmp/frame.png")
```

イベント購読: `sj.on("frame_changed", callback)`。種類: `frame_changed` / `ref_frame_changed` / `sequence_opened` / `project_loaded` / `project_saved` / `ref_fps_changed` / `active_layer_changed` / `layer_moved`(詳細は `api.py` 冒頭)。

## 8. 任意 GLSL の差し込み口

```python
view = window.gl_widget            # または sj.create_preview() の戻り値

# (A) ポストエフェクト: 合成後の色に対する関数だけを書く(#version は省略可)
view.set_effect_shader("""
uniform float uGain;
vec4 userEffect(vec4 color, vec2 uv) { return vec4(color.rgb * uGain, 1.0); }   // uv: 左上(0,0)〜右下(1,1)
""")
view.set_custom_uniform("uGain", 0.5)     # 毎回の描画で再設定される。float/int/2〜4要素のタプル
view.set_effect_shader()                  # 元(恒等)に戻す

# (B) 頂点/フラグメントシェーダーを丸ごと差し替え(契約は shaders/utils/alpha_blending.glsl の冒頭参照)
view.set_shader_sources(fragment=my_fragment_source)

view.shader_error                         # コンパイル失敗時のログ(失敗時は直前の動くシェーダーが維持される)
```

## 9. ショートカット(キーは元のまま)

| キー | 動作 |
|---|---|
| ← / → | 前/次のフレーム(参照ビューにポインタがあるときは参照フレーム) |
| Shift+← / → | ∓10フレーム |
| 0〜9, Return | 実画像番号を入力して確定(Return は入力中のみ有効) |
| U / D | 上/下のレイヤーを選択 |
| Shift+U / Shift+D | 選択レイヤーを上/下へ移動 |
| H / Shift+H / Alt+H | 表示切替 / ソロ(逆ソロ) / 全表示 |
| S | 選択レイヤーを表示サイズの基準にする |

## 10. ファイル別の変更

| ファイル | 変更 |
|---|---|
| `api.py` | **新規**。UI非依存の `ShellJekyll`(全操作の実体) |
| `ui/gl_frame_store.py` | **新規**。画素をバッファオブジェクトに格納するフレームストア(ページ分割。ページは拡張せず、満杯なら新ページ) |
| `ui/opengl.py` | 全面書き換え。VBOストア/カスタムシェーダー口/バグ修正。公開メソッド名は維持 |
| `ui/opengl_single.py` | 1レイヤー用サブクラスに(157→20行) |
| `shaders/utils/alpha_blending.glsl` | `texelFetch`+自前の双線形補間。`userEffect` 呼び出し |
| `shaders/utils/user_effect_default.glsl` | **新規**。恒等エフェクト |
| `ui/main_win/main_win_shortcuts.py` | **新規**。QShortcut 表 |
| `ui/main_win/main_win.py` | `keyPressEvent` 削除、コントローラ接続、ホバー検知 |
| `ui/main_win/main_win_{io,events,playback,ui}.py` | ダイアログ/ウィジェット更新のみに(ロジックは `api.py`) |
| `ui/ui_utils.py` | **新規**。3か所に重複していたボタン点滅処理 |
| `ui/layer_ui.py` | キー処理を削除(QShortcutへ) |
| `ui/expression_widgets.py`, `ui/expression_editor.py`, `ui/render_dialog.py` | コントローラ経由に。TCL 実行のバグ修正 |
| `utils/editing_utils.py` | `has_sequence` / `resolve_image_paths` / `get_layer_image_path` / `used_image_paths`(6か所の重複を集約) |
| `utils/layer_view.py` | **新規**。可視/サイズ基準の状態(Qt/GL非依存) |
| `gb_var.py`, `io/io_sjproj.py`, `render/render.py`, `expression/*.py`, `__main__.py` | 第3章のとおり |
| `tests/test_api_headless.py` | **新規**。Qt/GL不要の動作確認 |


## 11. macOS(Apple Silicon)で判明した問題と修正(追記)

実機のログ `gldCopyBufferSubData: NEEDS IMPLEMENTATION` と `unit 1 ... unloadable` を受けた修正。
- `glCopyBufferSubData` はMacのOpenGL(Metal変換層)で未実装 → バッファの拡張コピーを廃止し、満杯になったら新ページ(前ページの2倍の容量)を追加する方式に変更(`gl_frame_store.py`)。
- 未使用のテクスチャユニット(ユニット1〜7)に有効なバッファテクスチャが無かった → 1テクセルのダミーを全ユニットにバインド(`FrameStore.dummy_texture`、`paintGL`)。
- `qt.qpa.fonts ... "Segoe UI"` はスタイルシートのフォント指定による警告で、機能には影響しません(元のコードのまま)。
