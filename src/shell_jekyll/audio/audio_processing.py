import os
import subprocess

import numpy as np
from pathlib import Path

import soundfile as sf

class AudioProcessing:
    @classmethod
    def norm_loudness(cls, 
                      paths: list[str]
                      ) -> list:
        rms_list = {}
            
        for path in paths:
            if Path(path).suffix != ".wav":
                continue
            data, rate = sf.read(path)
            if data.ndim > 1:
                data = np.mean(data, axis=1)
            rms = np.sqrt(np.mean(data**2))
            rms_list[path] = rms
            
        min_rms = min(rms_list.values())
        
        coe_dict = {}
        for path, rms in rms_list.items():
            if rms == 0:
                coe_dict[path] = 1.0
                continue
            coe = min_rms / rms
            coe_dict[path] = float(coe)
            
        return coe_dict

    @classmethod
    def explode_mov(cls,
                    original_mov_path: str
                    ) -> tuple[str, str]:
        if Path(original_mov_path).suffix != ".mov":
            print("Only .mov supported")
            return
        base_dir = Path(original_mov_path).resolve().parent
        base_name = Path(original_mov_path).stem
        renamed_original_mov_path = base_dir / f"{base_name}_unsplitted.mov"
        os.rename(original_mov_path, renamed_original_mov_path)
        splitted_video_out = base_dir / f"{base_name}.mov"
        splitted_audio_out = base_dir / f"{base_name}.wav"

        try:
            cmd_audio = [
                "ffmpeg", "-y", "-i", str(renamed_original_mov_path),
                "-vn", "-acodec", "pcm_s16le", str(splitted_audio_out)
            ]
            subprocess.run(cmd_audio, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            print(f"  └ 音声保存完了: {splitted_audio_out.name}")

            # 2. 映像のみをMOV（H.264 / 無音）に変換・抽出
            cmd_video = [
                "ffmpeg", "-y", "-i", str(renamed_original_mov_path),
                "-an", "-vcodec", "libx264", "-preset", "ultrafast", str(splitted_video_out)
            ]
            subprocess.run(cmd_video, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            print(f"  └ 映像保存完了: {splitted_video_out.name}")

        except subprocess.CalledProcessError as e:
            print(f"エラーが発生しました ({renamed_original_mov_path.name}): 変換処理に失敗しました。")
        except FileNotFoundError:
            print("エラー: ffmpeg コマンドが見つかりません。`brew install ffmpeg` を実行してください。")

        return (str(splitted_video_out), str(splitted_audio_out))


   