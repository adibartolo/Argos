import subprocess
import threading
import uuid
import json
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)


# ── Health / heartbeat ────────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status":    "ok",
        "timestamp": datetime.utcnow().isoformat()
    }), 200


# ── Background task runner ────────────────────────────────────────────────────
def run_discovery(job_id: str, target: str, callback_url: str = None):
    """
    Runs argos-discovery container with nmap -F -sT -sV.
    Non-blocking: called from a background thread.
    """
    try:
        cmd = [
            "docker", "run", "--rm",
            "--name", f"discovery-{job_id}",
            "argos-discovery",
            target
        ]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180
        )
        payload = {
            "job_id":      job_id,
            "target":      target,
            "status":      "success" if proc.returncode == 0 else "error",
            "output":      proc.stdout,
            "error":       proc.stderr,
            "finished_at": datetime.utcnow().isoformat()
        }
    except subprocess.TimeoutExpired:
        payload = {
            "job_id":      job_id,
            "target":      target,
            "status":      "timeout",
            "output":      "",
            "error":       "Task exceeded 180s timeout",
            "finished_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        payload = {
            "job_id":      job_id,
            "target":      target,
            "status":      "error",
            "output":      "",
            "error":       str(e),
            "finished_at": datetime.utcnow().isoformat()
        }

    print(f"[JOB {job_id}] {payload['status'].upper()} — {target}")
    print(payload["output"][:500] if payload["output"] else payload["error"])

    # POST results back to control plane if callback provided
    if callback_url:
        try:
            data = json.dumps(payload).encode()
            import urllib.request
            req = urllib.request.Request(
                callback_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            urllib.request.urlopen(req, timeout=10)
            print(f"[JOB {job_id}] Callback sent to {callback_url}")
        except Exception as e:
            print(f"[JOB {job_id}] Callback error: {e}")


# ── Discovery endpoint ────────────────────────────────────────────────────────
@app.route("/scan/discovery", methods=["POST"])
def scan_discovery():
    """
    Trigger an async network discovery task.

    Request body (JSON):
    {
        "target":       "192.168.1.0/24",
        "callback_url": "https://your-n8n/webhook/results"  // optional
    }

    Response (immediate, 202 Accepted):
    {
        "job_id":      "A3F2C1B0",
        "status":      "accepted",
        "target":      "192.168.1.0/24",
        "accepted_at": "2026-07-22T10:00:00"
    }
    """
    body   = request.get_json(silent=True) or {}
    target = body.get("target", "").strip()

    if not target:
        return jsonify({"error": "Missing 'target' field"}), 400

    forbidden = [";", "&", "|", "`", "$", ">", "<"]
    if any(c in target for c in forbidden):
        return jsonify({"error": "Invalid target"}), 400

    callback_url = body.get("callback_url")
    job_id = uuid.uuid4().hex[:8].upper()

    t = threading.Thread(
        target=run_discovery,
        args=(job_id, target, callback_url),
        daemon=True
    )
    t.start()

    return jsonify({
        "job_id":      job_id,
        "status":      "accepted",
        "target":      target,
        "accepted_at": datetime.utcnow().isoformat()
    }), 202


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
