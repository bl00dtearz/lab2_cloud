import json
import os
import uuid
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUEUE_DIR = os.path.join(BASE_DIR, "queue")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
MAX_MESSAGE_LEN = 1000

os.makedirs(QUEUE_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

app = Flask(__name__)


def error(text, code):
    return jsonify({"error": text}), code


def get_message():
    """Return (message, None) or (None, error_response) for a JSON body with 'message'."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or "message" not in data:
        return None, error("field 'message' is required", 400)
    msg = data["message"]
    if not isinstance(msg, str) or not msg.strip():
        return None, error("'message' must be a non-empty string", 400)
    if len(msg) > MAX_MESSAGE_LEN:
        return None, error(f"'message' is too long (max {MAX_MESSAGE_LEN})", 400)
    return msg, None


def valid_job_id(job_id):
    """Strict UUID check: only the canonical form like 123e4567-e89b-12d3-a456-426614174000."""
    try:
        return str(uuid.UUID(job_id)) == job_id.lower()
    except ValueError:
        return False


# R1
@app.route("/echo", methods=["POST"])
def echo():
    msg, err = get_message()
    if err:
        return err
    return jsonify({"reply": msg}), 200


# R2
@app.route("/time", methods=["GET"])
def current_time():
    return jsonify({"time": datetime.now(timezone.utc).isoformat()}), 200


# R3
@app.route("/jobs", methods=["POST"])
def submit_job():
    msg, err = get_message()
    if err:
        return err
    job_id = str(uuid.uuid4())
    tmp_path = os.path.join(QUEUE_DIR, f"{job_id}.tmp")
    final_path = os.path.join(QUEUE_DIR, f"{job_id}.json")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump({"job_id": job_id, "message": msg}, f)
        os.replace(tmp_path, final_path)  # atomic: worker never sees a half-written file
    except OSError:
        return error("could not save the job", 500)
    return jsonify({"job_id": job_id, "status": "queued"}), 202


# R4
@app.route("/jobs/<job_id>", methods=["GET"])
def job_status(job_id):
    if not valid_job_id(job_id):
        return error("job not found", 404)
    job_id = job_id.lower()

    result_path = os.path.join(RESULTS_DIR, f"{job_id}.json")
    queue_path = os.path.join(QUEUE_DIR, f"{job_id}.json")

    if os.path.exists(result_path):
        try:
            with open(result_path, encoding="utf-8") as f:
                result = json.load(f).get("result")
        except (OSError, ValueError):
            return error("could not read the result", 500)
        return jsonify({"job_id": job_id, "status": "done", "result": result}), 200
    if os.path.exists(queue_path):
        return jsonify({"job_id": job_id, "status": "queued", "result": None}), 200
    return error("job not found", 404)


# R5 + 405 + others: always JSON, never an HTML page
@app.errorhandler(HTTPException)
def handle_http_error(e):
    messages = {404: "not found", 405: "method not allowed"}
    return error(messages.get(e.code, e.name.lower()), e.code)


@app.errorhandler(Exception)
def handle_unexpected(e):
    return error("internal server error", 500)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
