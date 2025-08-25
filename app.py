from flask import Flask, jsonify

# Inizializza Flask
app = Flask(__name__)

# Rotta di test (homepage)
@app.route("/")
def home():
    return "✅ Server Flask attivo su Render!"

# Rotta classifica (esempio)
@app.route("/leaderboard")
def leaderboard():
    # Dati finti per test, poi li sostituiamo col salvataggio reale
    fake_data = [
         {"player": "Mario", "coin": 100}

