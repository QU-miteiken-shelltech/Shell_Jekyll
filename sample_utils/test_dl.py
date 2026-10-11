import yt_dlp, os

def download(url):
    def hook(d):
        if d['status'] == 'downloading':
            print(f"\r{d.get('_percent_str','0%')} {d.get('_speed_str','0B/s')}", end='')

    opts = {
        'format': 'bv*+ba/b',
        # merge_output_format は指定しない。
        # → yt-dlp が vcodec/acodec に応じて可能なコンテナを選ぶ（混在なら mkv）
        'progress_hooks': [hook],
    }

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        print("\n完了")
        dl = (info.get('requested_downloads') or [{}])[0]
        path = dl.get('filepath')
        print(f"{os.path.basename(path)} / {os.path.getsize(path)/1048576:.2f} MB")
        print(f"{info.get('width')}x{info.get('height')} "
              f"{info.get('vcodec')} + {info.get('acodec')} [{info.get('format_id')}]")

download(input("URL: "))
