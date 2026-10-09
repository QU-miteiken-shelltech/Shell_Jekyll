import os
from pathlib import Path
from flask import Flask, render_template, jsonify

app = Flask(__name__)

def get_download_dir():
    """OSごとのダウンロードフォルダのパスを取得"""
    return Path.home() / "Downloads"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create-file', methods=['POST'])
def create_file():
    try:
        download_dir = get_download_dir()
        
        # 保存先フォルダが存在しない場合は作成
        download_dir.mkdir(parents=True, exist_ok=True)
        
        # 作成するファイル名を設定
        file_path = download_dir / "created_by_flask.txt"
        
        # 空のテキストファイルを作成（すでに存在する場合は上書き/空にする）
        file_path.touch()
        
        return jsonify({
            "status": "success", 
            "message": f"ファイルを生成しました: {file_path}"
        })
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
