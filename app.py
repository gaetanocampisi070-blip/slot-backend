from flask import Flask, request, jsonify
import json, os, threading

app = Flask(__name__)

DATA_FILE = "scores.json"
_lock = threading.Lock()

# inizializza il file dati se non esiste
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

def read_scores():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def write_scores(scores):
    with open(DATA_FILE, "w") as f:
        json.dump(scores, f)

@app.route("/")
def home():
    return "✅ Server attivo! Endpoints: /save, /load/<user_id>, /leaderboard"

@app.route("/save", methods=["POST"])
def save():
    payload = request.get_json(force=True, silent=True) or {}
    user_id = str(payload.get("user_id"))
    name = payload.get("name", "Anonimo")
    money = int(payload.get("money", 0))
    stamina = int(payload.get("stamina", 100))

    with _lock:
        scores = read_scores()
        scores[user_id] = {
            "name": name,
            "money": money,
            "stamina": stamina
        }
        write_scores(scores)

    return jsonify({"status": "ok", "saved": scores[user_id]})

@app.route("/load/<user_id>")
def load(user_id):
    with _lock:
        scores = read_scores()
        data = scores.get(str(user_id))
    if data:
        return jsonify(data)
    return jsonify({"name": "Anonimo", "money": 100, "stamina": 100})

@app.route("/leaderboard")
def leaderboard():
    with _lock:
        scores = read_scores()
        players = list(scores.values())
    players.sort(key=lambda p: p.get("money", 0), reverse=True)
    return jsonify(players[:10])  # primi 10 giocatori

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
