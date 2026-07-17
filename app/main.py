"""
Task/Order Tracking API
UAS Mini Project Individu - Communication Protocol - Universitas Cakrawala
Nama: Ghina Athaya Tyano | NIM: 25120500011

Use Case 4: Task/Order Tracking (REST + n8n optional)

Endpoints:
1. POST   /api/tasks               -> buat task baru
2. GET    /api/tasks               -> list semua task (bisa filter ?status=)
3. GET    /api/tasks/<id>          -> detail satu task
4. PUT    /api/tasks/<id>/status   -> update status task (dengan validasi transition)
5. DELETE /api/tasks/<id>          -> hapus/cancel task

Observability:
- Setiap request diberi X-Request-ID (correlation ID)
- Response time (ms) dicatat di header X-Response-Time dan di log
- Semua request/response dicatat ke app.log (dan console)
"""

from flask import Flask, request, jsonify, g
from datetime import datetime, timezone
import logging
import time
import uuid

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

# ---------------------------------------------------------------------------
# Logging setup (Observability evidence)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("task-tracking-api")

# ---------------------------------------------------------------------------
# In-memory "database"
# ---------------------------------------------------------------------------
TASKS = {}
NEXT_ID = 1

# Status transition rules (Reliability: error contract for invalid transitions)
VALID_STATUSES = ["pending", "in_progress", "done", "cancelled"]
ALLOWED_TRANSITIONS = {
    "pending": ["in_progress", "cancelled"],
    "in_progress": ["done", "cancelled"],
    "done": [],          # final state, tidak bisa pindah lagi
    "cancelled": []       # final state, tidak bisa pindah lagi
}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def error_response(status_code, error_code, message, request_id):
    """Error contract yang konsisten untuk semua failure scenario."""
    return jsonify({
        "error": {
            "code": error_code,
            "message": message
        },
        "requestId": request_id,
        "timestamp": now_iso()
    }), status_code


# ---------------------------------------------------------------------------
# Middleware: correlation ID + response time (Observability)
# ---------------------------------------------------------------------------
@app.before_request
def before_request():
    g.start_time = time.time()
    g.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    logger.info(
        f"REQUEST  id={g.request_id} method={request.method} path={request.path} "
        f"body={request.get_data(as_text=True)[:300]}"
    )


@app.after_request
def after_request(response):
    duration_ms = round((time.time() - g.start_time) * 1000, 2)
    response.headers["X-Request-ID"] = g.request_id
    response.headers["X-Response-Time"] = f"{duration_ms}ms"
    response.headers["Server"] = "TaskTrackingDemo/1.0 Python/Flask"
    logger.info(
        f"RESPONSE id={g.request_id} status={response.status_code} "
        f"duration={duration_ms}ms"
    )
    return response


# ---------------------------------------------------------------------------
# Endpoint 1: POST /api/tasks -> buat task baru
# ---------------------------------------------------------------------------
@app.route("/api/tasks", methods=["POST"])
def create_task():
    global NEXT_ID
    data = request.get_json(silent=True)

    if not data or "title" not in data or not str(data.get("title", "")).strip():
        return error_response(
            400, "VALIDATION_ERROR",
            "Field 'title' wajib diisi dan tidak boleh kosong.",
            g.request_id
        )

    if "assignee" not in data or not str(data.get("assignee", "")).strip():
        return error_response(
            400, "VALIDATION_ERROR",
            "Field 'assignee' wajib diisi.",
            g.request_id
        )

    task = {
        "id": NEXT_ID,
        "title": data["title"],
        "assignee": data["assignee"],
        "priority": data.get("priority", "medium"),
        "status": "pending",
        "createdAt": now_iso(),
        "updatedAt": now_iso()
    }
    TASKS[NEXT_ID] = task
    NEXT_ID += 1

    return jsonify(task), 201


# ---------------------------------------------------------------------------
# Endpoint 2: GET /api/tasks -> list semua task (filter opsional ?status=)
# ---------------------------------------------------------------------------
@app.route("/api/tasks", methods=["GET"])
def list_tasks():
    status_filter = request.args.get("status")
    items = list(TASKS.values())

    if status_filter:
        if status_filter not in VALID_STATUSES:
            return error_response(
                400, "INVALID_QUERY_PARAM",
                f"Status filter '{status_filter}' tidak valid. Pilihan: {VALID_STATUSES}",
                g.request_id
            )
        items = [t for t in items if t["status"] == status_filter]

    return jsonify({
        "resource": "tasks",
        "count": len(items),
        "data": items
    }), 200


# ---------------------------------------------------------------------------
# Endpoint 3: GET /api/tasks/<id> -> detail satu task
# ---------------------------------------------------------------------------
@app.route("/api/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    task = TASKS.get(task_id)
    if not task:
        return error_response(
            404, "TASK_NOT_FOUND",
            f"Task dengan id {task_id} tidak ditemukan.",
            g.request_id
        )
    return jsonify(task), 200


# ---------------------------------------------------------------------------
# Endpoint 4: PUT /api/tasks/<id>/status -> update status (dengan validasi transition)
# ---------------------------------------------------------------------------
@app.route("/api/tasks/<int:task_id>/status", methods=["PUT"])
def update_status(task_id):
    task = TASKS.get(task_id)
    if not task:
        return error_response(
            404, "TASK_NOT_FOUND",
            f"Task dengan id {task_id} tidak ditemukan.",
            g.request_id
        )

    data = request.get_json(silent=True)
    new_status = data.get("status") if data else None

    if not new_status or new_status not in VALID_STATUSES:
        return error_response(
            400, "VALIDATION_ERROR",
            f"Field 'status' wajib diisi dengan salah satu dari {VALID_STATUSES}",
            g.request_id
        )

    current_status = task["status"]
    allowed_next = ALLOWED_TRANSITIONS[current_status]

    if new_status not in allowed_next:
        return error_response(
            409, "INVALID_STATE_TRANSITION",
            f"Tidak bisa mengubah status dari '{current_status}' ke '{new_status}'. "
            f"Transisi yang diizinkan dari '{current_status}': {allowed_next}",
            g.request_id
        )

    task["status"] = new_status
    task["updatedAt"] = now_iso()

    return jsonify(task), 200


# ---------------------------------------------------------------------------
# Endpoint 5: DELETE /api/tasks/<id> -> hapus/cancel task
# ---------------------------------------------------------------------------
@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    task = TASKS.get(task_id)
    if not task:
        return error_response(
            404, "TASK_NOT_FOUND",
            f"Task dengan id {task_id} tidak ditemukan, tidak bisa dihapus.",
            g.request_id
        )
    del TASKS[task_id]
    return jsonify({
        "message": f"Task {task_id} berhasil dihapus.",
        "requestId": g.request_id
    }), 200


# ---------------------------------------------------------------------------
# Root endpoint -> info API (memudahkan demo & Wireshark evidence)
# ---------------------------------------------------------------------------
@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "service": "Task/Order Tracking API",
        "case": "Use Case 4 - Task/Order Tracking",
        "endpoints": [
            "POST   /api/tasks",
            "GET    /api/tasks",
            "GET    /api/tasks/<id>",
            "PUT    /api/tasks/<id>/status",
            "DELETE /api/tasks/<id>"
        ]
    }), 200


if __name__ == "__main__":
    # Jalankan di 127.0.0.1:8088 supaya konsisten dengan project UTS sebelumnya
    app.run(host="127.0.0.1", port=8088, debug=False)
