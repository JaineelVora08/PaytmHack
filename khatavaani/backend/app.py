from flask import Flask
from flask_cors import CORS
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent.parent / ".env")
load_dotenv(BASE_DIR / ".env")

from database import init_db
from local_intelligence.routes import local

app = Flask(__name__)
CORS(app, expose_headers=["X-Transcript", "X-Answer-Text", "X-Agent", "X-Lang-Detected"])
init_db()
app.register_blueprint(local)

try:
    from network_intelligence.routes import network

    app.register_blueprint(network)
except ImportError:
    pass

@app.route("/")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
