"""Flask entrypoint for the Bug Reporter app."""
from __future__ import annotations

import itertools
import logging
import os
from datetime import datetime
from typing import Dict, List

import requests
from flask import Flask, jsonify, render_template, request

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

app = Flask(__name__, template_folder=TEMPLATE_DIR)
logging.basicConfig(level=logging.INFO)

PRIORITY_CHOICES = {"low", "medium", "high"}
_request_counter = itertools.count(1)


def generate_tracking_id() -> str:
    """Return a BUG-YYYYMMDD-N style identifier."""
    today = datetime.utcnow().strftime("%Y%m%d")
    return f"BUG-{today}-{next(_request_counter)}"


def extract_payload() -> Dict[str, str]:
    """Support both JSON bodies and x-www-form-urlencoded submissions."""
    if request.is_json:
        payload = request.get_json(silent=True) or {}
    else:
        payload = request.form.to_dict()
    sanitized = {k: v.strip() if isinstance(v, str) else v for k, v in payload.items()}
    return sanitized


def validate_payload(payload: Dict[str, str]) -> List[str]:
    errors: List[str] = []
    for field in ("title", "description", "priority"):
        if not payload.get(field):
            errors.append(f"Missing required field: {field}")
    if payload.get("priority") and payload["priority"].lower() not in PRIORITY_CHOICES:
        errors.append("Priority must be one of: low, medium, high")
    return errors


def forward_to_n8n(payload: Dict[str, str], tracking_id: str) -> None:
    """POST the raw payload to the configured n8n webhook, if any."""
    webhook_url = os.getenv("N8N_WEBHOOK_URL")
    if not webhook_url:
        logging.info("N8N_WEBHOOK_URL not set; skipping webhook forward")
        return

    headers = {"X-Bug-Tracking-Id": tracking_id}
    response = requests.post(webhook_url, json=payload, headers=headers, timeout=5)
    response.raise_for_status()


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat() + "Z"})


@app.route("/api/report", methods=["POST"])
def report_bug():
    payload = extract_payload()
    errors = validate_payload(payload)
    if errors:
        return jsonify({"status": "error", "errors": errors}), 400

    tracking_id = generate_tracking_id()

    try:
        forward_to_n8n(payload, tracking_id)
    except requests.RequestException as exc:  # pragma: no cover - simple error path
        logging.error("Forwarding to n8n failed: %s", exc)
        return jsonify({"status": "error", "message": "Failed to reach automation webhook."}), 502

    return jsonify({"status": "ok", "tracking_id": tracking_id})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
