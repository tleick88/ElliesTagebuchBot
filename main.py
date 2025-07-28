# main.py - Angepasste Version für eine flache Struktur

import os
import threading
from dotenv import load_dotenv
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

# Lade Umgebungsvariablen aus der .env-Datei (für lokale Entwicklung)
# Auf Render werden diese direkt aus den Environment-Settings geladen.
load_dotenv()

# --- WICHTIGE IMPORTE (angepasst für flache Struktur) ---
# Wir gehen davon aus, dass die folgenden Dateien im selben Ordner wie main.py liegen:
# - models.py (enthält die User-Klasse und db-Instanz)
# - routes.py (enthält die user_bp-Blaupause)
# - telegram_bot.py (enthält die TochterErinnerungenBot-Klasse)

from models import db
from routes import user_bp
from telegram_bot import TochterErinnerungenBot

# --- Flask App Konfiguration ---
# Der 'static' Ordner für Ihre Weboberfläche (z.B. React/Vue Build)
STATIC_FOLDER = os.path.join(os.path.dirname(__file__), 'static')

app = Flask(__name__, static_folder=STATIC_FOLDER)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'ein-zufaelliger-geheimer-schluessel') # Besser aus Umgebungsvariablen laden

# CORS für die API aktivieren
CORS(app, resources={r"/api/*": {"origins": "*"}})

# API-Routen registrieren
app.register_blueprint(user_bp, url_prefix='/api')

# --- Datenbank Konfiguration ---
# Render stellt einen persistenten Speicher unter /var/data/ zur Verfügung.
# Wir erstellen dort einen Ordner für unsere Datenbank.
DB_FOLDER = '/var/data/database'
if not os.path.exists(DB_FOLDER):
    os.makedirs(DB_FOLDER)

DB_PATH = os.path.join(DB_FOLDER, 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Erstelle die Datenbanktabellen, falls sie nicht existieren
with app.app_context():
    db.create_all()

# --- Statische Dateien für die Weboberfläche ausliefern ---
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

# --- Telegram Bot Start ---
def start_bot_in_thread():
    """Startet den Bot in einem separaten Thread, damit er den Webserver nicht blockiert."""
    print("🤖 Starte Telegram Bot automatisch...")
    try:
        bot_instance = TochterErinnerungenBot()
        bot_instance.run() # Die run-Methode sollte blockierend sein (z.B. updater.idle())
        print("✅ Telegram Bot erfolgreich gestartet und läuft.")
    except Exception as e:
        print(f"❌ Fehler beim automatischen Bot-Start: {e}")

# --- Hauptausführung ---
if __name__ == '__main__':
    # Starte den Bot in einem Hintergrund-Thread
    bot_thread = threading.Thread(target=start_bot_in_thread, daemon=True)
    bot_thread.start()
    
    # Starte die Flask Web App
    # Render stellt die PORT-Variable automatisch zur Verfügung.
    port = int(os.getenv('PORT', 5000))
    print(f"🌐 Starte Flask Web-Interface auf Port {port}...")
    app.run(host='0.0.0.0', port=port)

