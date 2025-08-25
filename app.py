import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # se front e back sono su domini diversi

# ===== DB CONFIG =====
uri = os.getenv("DATABASE_URL")  # es: postgres://user:pass@host:5432/db
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = uri or "sqlite:///data.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Player(db.Model):
    user_id = db.Column(db.String(64), primary_key=True)
    username = db.Column(db.String(120))
    coins = db.Column(db.Integer, default=100)
    stamina = db.Column(db.Integer, default=100)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_public(self):
        return {"username": self.username or "anonimo", "coins": self.coins, "stamina": self.stamina}

with app.app_context():
    db.create_all()

# ===== ROUTES =====
@app.get("/")
def home():
    return "Casino API is running 🎰"

@app.get("/me")
def me():
    user_id = str(request.args.get("userId"))
    if not user_id:
        return jsonify({"error": "missing userId"}), 400
    p = db.session.get(Player, user_id)
    if not p:
        # crea record default
        p = Player(user_id=user_id, username="anonimo", coins=100, stamina=100)
        db.session.add(p)
        db.session.commit()
    return jsonify({"userId": p.user_id, "username": p.username, "coins": p.coins, "stamina": p.stamina})

@app.post("/save")
def save():
    data = request.get_json(force=True)
    user_id = str(data.get("userId"))
    if not user_id:
        return jsonify({"error": "missing userId"}), 400

    p = db.session.get(Player, user_id)
    if not p:
        p = Player(user_id=user_id)

    p.username = data.get("username") or p.username or "anonimo"
    p.coins = int(data.get("coins", p.coins or 100))
    p.stamina = int(data.get("stamina", p.stamina or 100))
    p.updated_at = datetime.utcnow()

    db.session.add(p)
    db.session.commit()
    return jsonify({"ok": True})

@app.get("/leaderboard")
def leaderboard():
    cutoff = datetime.utcnow() - timedelta(hours=24)
    q = (Player.query
         .filter(Player.updated_at > cutoff)
         .order_by(Player.coins.desc())
         .limit(20))
    return jsonify([x.to_public() for x in q])
