from flask import Flask, request, jsonify
from flask_cors import CORS
import json, os, threading, datetime

app = Flask(__name__)
CORS(app)  # Permette richieste dal tuo GitHub Pages / Telegram WebApp

DATA_FILE = "scores.json"
_lock = threading.Lock()

# Inizializza il file dati se non esiste
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

def _read_scores():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def _write_scores(scores):
    with open(DATA_FILE, "w") as f:
        json.dump(scores, f)

@app.route("/")
def home():
    return jsonify({
        "ok": True,
        "message": "Slot backend attivo",
        "endpoints": ["/save", "/load/<user_id>", "/leaderboard", "/leaderboard/daily"]
    })

@app.route("/save", methods=["POST"])
def save_score():
    payload = request.get_json(force=True, silent=True) or {}
    user_id = str(payload.get("user_id"))
    name = payload.get("name", "Anon")
    money = int(payload.get("money", 100))
    stamina = int(payload.get("stamina", 100))
    today = str(datetime.date.today())

    with _lock:
        scores = _read_scores()
        scores[user_id] = {
            "name": name,
            "money": money,
            "stamina": stamina,
            "last_update": today
        }
        _write_scores(scores)

    return jsonify({"status": "ok"})

@app.route("/load/<user_id>")
def load_score(user_id):
    with _lock:
        scores = _read_scores()
        data = scores.get(str(user_id))
    if data:
        return jsonify(data)
    return jsonify({"money": 100, "stamina": 100})

@app.route("/leaderboard")
def leaderboard():
    with _lock:
        scores = _read_scores()
        players = list(scor
