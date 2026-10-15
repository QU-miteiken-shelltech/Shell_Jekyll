import os
import subprocess
import json

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
    def get_duration(cls, file_path):
        get_duration_cmd = [
            "ffprobe", "-v", "quiet", 
            "-print_format", "json", 
            "-show_format", 
            file_path
        ]
        result = subprocess.run(get_duration_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])

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
            print(f"  └ Splitted audio saved : {splitted_audio_out.name}")

            cmd_video = [
                "ffmpeg", "-y", "-i", str(renamed_original_mov_path),
                "-an", "-vcodec", "libx264", "-preset", "ultrafast", str(splitted_video_out)
            ]
            subprocess.run(cmd_video, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            print(f"  └ Splitted movie saved : {splitted_video_out.name}")

        except subprocess.CalledProcessError as e:
            print(f"Error ! - {renamed_original_mov_path.name}\nconversion failed : {e}")
        except FileNotFoundError:
            print("Error !\nffmpeg unfound. Run `brew install ffmpeg` to install")

        return (str(splitted_video_out), str(splitted_audio_out))

    @classmethod
    def merge_wav(cls,
                  wav_audio_path: str,
                  mov_movie_path: str
                  ) -> tuple[str, str]:
        is_audio_longer = cls.get_duration(wav_audio_path) > cls.get_duration(mov_movie_path)
        original_mov_path = mov_movie_path
        renamed_original_mov_path = str(Path(mov_movie_path).resolve().parent / f"unmerged_{Path(mov_movie_path).name}")
        os.rename(original_mov_path, renamed_original_mov_path)
        ffmpeg_cmd = [
            "ffmpeg", "-i", renamed_original_mov_path, 
            "-i", wav_audio_path, 
            "-filter_complex", 
            "[0:v]tpad=stop_mode=add:color=black:stop_duration=3600[v]", 
            "-map", "[v]", 
            "-map", "1:a:0", 
            "-c:v", "libx264", 
            "-c:a", "aac", 
            "-shortest", 
            mov_movie_path
        ] if is_audio_longer else [
            "ffmpeg", "-i", renamed_original_mov_path, 
            "-i", wav_audio_path, 
            "-map", "0:v:0", 
            "-map", "1:a:0", 
            "-c:v", "copy", 
            "-c:a", "aac", 
            "-af", "apad", 
            "-shortest", 
            mov_movie_path
        ]
        subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print(f"  └ Audio merged to movie as {mov_movie_path}")
        return (str(mov_movie_path), str(wav_audio_path))
        