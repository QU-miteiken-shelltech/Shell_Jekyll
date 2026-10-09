import os
from pathlib import Path
from enum import StrEnum

from flask import Flask, render_template, jsonify

from PySide6.QtCore import Signal, QObject

class RequestType(StrEnum):
    PLAY = "play"
    PAUSE = "pause"
    PROCEED = "proceed"
    RETURN = "return"

class FlaskBridge(QObject):
    flask_sig = Signal(RequestType)

bridge = FlaskBridge()
app = Flask(__name__)

@app.route('/')
def index():
    html_path = Path(__file__).resolve().parent / "web_ui.html"
    with open(html_path, "r", encoding="utf-8") as f:
        html_str = f.read()
    return html_str

@app.route('/<action>', methods=['POST'])
def handle_action(action):
    valid_actions = ['play', 'pause', 'proceed', 'return']
    try:
        if action in valid_actions:
            bridge.flask_sig.emit(action)
            
            return jsonify({
                "status": "success", 
                "request": action
            })
        else:
            raise Exception
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500

def run_web_remote():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
