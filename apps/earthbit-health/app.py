"""HTTP endpoints for the earthbit-health service."""
from flask import Flask, jsonify

app = Flask(__name__)


@app.get("/")
def index():
    return jsonify({"message": "Pulse of Earth - staging test"})


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "earthbit-health"})


@app.get("/version")
def version():
    return jsonify({"version": "0.1.0", "service": "earthbit-health"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
