import subprocess
from pathlib import Path

def separate_videos(folder_path):
    folder = Path(folder_path)

    if not folder.exists() or not folder.is_dir():
        print("指定されたフォルダが見つかりません。")
        return

    target_extensions = [".webm", ".mp4", ".mkv"]

    for file_path in folder.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in target_extensions:
            print(f"処理中: {file_path.name}")

            base_name = file_path.stem
            audio_output = folder / f"{base_name}.wav"
            video_output = folder / f"{base_name}.mov"

            try:
                # 1. 音声をWAVに抽出 (ffmpeg)
                cmd_audio = [
                    "ffmpeg", "-y", "-i", str(file_path),
                    "-vn", "-acodec", "pcm_s16le", str(audio_output)
                ]
                subprocess.run(cmd_audio, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                print(f"  └ 音声保存完了: {audio_output.name}")

                # 2. 映像のみをMOV（H.264 / 無音）に変換・抽出
                cmd_video = [
                    "ffmpeg", "-y", "-i", str(file_path),
                    "-an", "-vcodec", "libx264", "-preset", "ultrafast", str(video_output)
                ]
                subprocess.run(cmd_video, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                print(f"  └ 映像保存完了: {video_output.name}")

            except subprocess.CalledProcessError as e:
                print(f"エラーが発生しました ({file_path.name}): 変換処理に失敗しました。")
            except FileNotFoundError:
                print("エラー: ffmpeg コマンドが見つかりません。`brew install ffmpeg` を実行してください。")
                break

if __name__ == "__main__":
    target_folder = input("folder : ")
    separate_videos(target_folder)