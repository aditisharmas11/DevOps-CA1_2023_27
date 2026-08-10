import os 
from flask import Flask, jsonify, request
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

webhook_counter = Counter(
    "webhooks_received_total",
    "Total number of webhooks received"
)


@app.route("/")
def home():
    return jsonify({
        "application": "SRE DevOps Challenge",
        "status": "running"
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy"
    })


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}

    webhook_counter.inc()

    commit_sha = (
        data.get("after")
        or data.get("commit_sha")
        or data.get("checkout_sha")
        or "unknown"
    )

    return jsonify({
        "message": "Webhook received",
        "commit_sha": commit_sha
    }), 200


@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {
        "Content-Type": CONTENT_TYPE_LATEST
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))