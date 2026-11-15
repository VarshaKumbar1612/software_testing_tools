"""
app.py - Flask Web Application and REST API.
Serves To-Do frontend, REST API endpoints, and QA Audit Dashboard.
"""

from flask import Flask, jsonify, render_template, request
import todo_logic
import audit_runner

app = Flask(__name__)


# -------------------------------------------------------------
# Frontend Page Routes
# -------------------------------------------------------------

@app.route("/")
def index():
    """Render the primary To-Do list client interface."""
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    """Render the Software Quality & Defect Prediction Dashboard."""
    return render_template("dashboard.html")


# -------------------------------------------------------------
# To-Do REST API Endpoints
# -------------------------------------------------------------

@app.route("/api/tasks", methods=["GET"])
def api_get_tasks():
    """Return all tasks, with optional status and priority query parameters."""
    status = request.args.get("status", "all")
    priority = request.args.get("priority", "all")
    try:
        tasks = todo_logic.get_tasks(status=status, priority=priority)
        return jsonify(tasks), 200
    except ValueError as err:
        return jsonify({"error": str(err)}), 400


@app.route("/api/tasks", methods=["POST"])
def api_add_task():
    """Create a new task."""
    data = request.get_json(silent=True) or {}
    title = data.get("title", "")
    description = data.get("description", "")
    priority = data.get("priority", "normal")

    try:
        new_task = todo_logic.add_task(
            title=title,
            description=description,
            priority=priority
        )
        return jsonify(new_task), 201
    except ValueError as err:
        return jsonify({"error": str(err)}), 400


@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
def api_toggle_task(task_id):
    """Toggle completed status of a specific task."""
    try:
        updated_task = todo_logic.toggle_task(task_id)
        return jsonify(updated_task), 200
    except ValueError as err:
        return jsonify({"error": str(err)}), 404


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def api_delete_task(task_id):
    """Delete a task by ID."""
    try:
        deleted = todo_logic.delete_task(task_id)
        return jsonify({"message": "Task deleted", "task": deleted}), 200
    except ValueError as err:
        return jsonify({"error": str(err)}), 404


@app.route("/api/stats", methods=["GET"])
def api_get_stats():
    """Return summary statistics of current tasks."""
    stats = todo_logic.get_task_summary()
    return jsonify(stats), 200


# -------------------------------------------------------------
# QA & Defect Prediction Audit API
# -------------------------------------------------------------

@app.route("/api/run-audit", methods=["GET"])
def api_run_audit():
    """Trigger the automated QA tools suite and return unified JSON metrics."""
    results = audit_runner.run_all()
    return jsonify(results), 200


if __name__ == "__main__":
    # Note: debug=True is deliberately maintained for QA demonstration
    # allowing Bandit to detect Flask debug vulnerability during scans.
    app.run(debug=True, host="0.0.0.0", port=5000)
