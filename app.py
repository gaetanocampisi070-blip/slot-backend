from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
import datetime

app = Flask(__name__)
CORS(app)

DB_FILE = "db.sqlite3"

# --- Utility DB ---
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    # utenti
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            money INTEGER,
            stamina INTEGER,
            updated TIMESTAMP
        )
    """)
    # classifica
    c.execute("""
        CREATE TABLE IF NOT EXISTS leaderboard (
            user_id TEXT PRIMARY KEY,
            money INTEGER,
            last_update TIMESTAMP
        )
    """)
    # metadati (per reset ogni 24h)
    c.execute("""
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- API ---

@app.route("/")
def home():
    return {"status": "ok", "message": "MiniCasino backend attivo"}

# Legge progressi utente
@app.route("/user/<uid>", methods=["GET"])
def get_user(uid):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()
    if not row:
        # se nuovo utente, crea con default
        money, stamina = 100, 100
        c.execute("INSERT INTO users VALUES (?,?,?,?)", (uid, money, stamina, datetime.datetime.utcnow()))
        conn.commit()
    else:
        money, stamina = row["money"], row["stamina"]
    conn.close()
    return jsonify({"money": money, "stamina": stamina})

# Aggiorna progressi
@app.route("/user/<uid>", methods=["POST"])
def update_user(uid):
    data = request.json
    money = int(data.get("money", 100))
    stamina = int(data.get("stamina", 100))
    now = datetime.datetime.utcnow()

    conn = get_db()
    c = conn.cursor()
    # update users
    c.execute("INSERT OR REPLACE INTO users (user_id,money,stamina,updated) VALUES (?,?,?,?)",
              (uid, money, stamina, now))
    # update leaderboard
    c.execute("INSERT OR REPLACE INTO leaderboard (user_id,money,last_update) VALUES (?,?,?)",
              (uid, money, now))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

# Restituisce la classifica
@app.route("/leaderboard", methods=["GET"])
def leaderboard():
    # reset se serve
    reset_if_needed()

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT user_id, money FROM leaderboard ORDER BY money DESC LIMIT 20")
    rows = c.fetchall()
    conn.close()
    return jsonify([{"user": r["user_id"], "money": r["money"]} for r in rows])

# --- Reset classifica ogni 24h ---
def reset_if_needed():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT value FROM meta WHERE key='last_reset'")
    row = c.fetchone()
    now = datetime.datetime.utcnow()

    do_reset = False
    if not row:
        do_reset = True
    else:
        last_reset = datetime.datetime.fromisoformat(row["value"])
        if (now - last_reset).total_seconds() > 24*3600:
            do_reset = True

    if do_reset:
        c.execute("DELETE FROM leaderboard")
        c.execute("INSERT OR REPLACE INTO meta (key,value) VALUES ('last_reset',?)", (now.isoformat(),))
        conn.commit()
    conn.close()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
