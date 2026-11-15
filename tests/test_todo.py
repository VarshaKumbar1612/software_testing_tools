"""
tests/test_todo.py - Comprehensive Unit & Integration Tests for To-Do Application.
Covers core logic edge cases, validation, and Flask REST API endpoints.
"""

import json
import os
import pytest
from app import app
import todo_logic


@pytest.fixture
def temp_task_file(tmp_path):
    """Provides a fresh isolated JSON file for each test run."""
    file_path = str(tmp_path / "test_tasks.json")
    return file_path


@pytest.fixture
def client(temp_task_file):
    """Configures the Flask test client with an isolated data store."""
    app.config["TESTING"] = True
    old_env = os.environ.get("TODO_DATA_FILE")
    os.environ["TODO_DATA_FILE"] = temp_task_file

    with app.test_client() as test_client:
        yield test_client

    if old_env is not None:
        os.environ["TODO_DATA_FILE"] = old_env
    else:
        os.environ.pop("TODO_DATA_FILE", None)


# ==========================================
# Core Logic Unit Tests (todo_logic.py)
# ==========================================

def test_add_task_success(temp_task_file):
    """Verify standard task creation with all fields."""
    task = todo_logic.add_task(
        title="Study Software Testing",
        description="Review McCabe complexity and Coverage",
        priority="high",
        filepath=temp_task_file
    )
    assert task["id"] == 1
    assert task["title"] == "Study Software Testing"
    assert task["description"] == "Review McCabe complexity and Coverage"
    assert task["priority"] == "high"
    assert task["completed"] is False
    assert "created_at" in task

    # Verify persistent storage
    loaded = todo_logic.load_tasks(temp_task_file)
    assert len(loaded) == 1
    assert loaded[0]["id"] == 1


def test_add_task_validation_failures(temp_task_file):
    """Verify edge case validations: empty title, length limit, invalid priority."""
    with pytest.raises(ValueError, match="cannot be empty"):
        todo_logic.add_task("", filepath=temp_task_file)

    with pytest.raises(ValueError, match="cannot be empty"):
        todo_logic.add_task("   ", filepath=temp_task_file)

    long_title = "A" * 121
    with pytest.raises(ValueError, match="exceeds 120 characters"):
        todo_logic.add_task(long_title, filepath=temp_task_file)

    with pytest.raises(ValueError, match="Priority must be one of"):
        todo_logic.add_task("Valid Title", priority="urgent", filepath=temp_task_file)


def test_get_tasks_filtering(temp_task_file):
    """Verify filtering tasks by active/completed status and priority."""
    t1 = todo_logic.add_task("Task 1", priority="low", filepath=temp_task_file)
    t2 = todo_logic.add_task("Task 2", priority="high", filepath=temp_task_file)
    t3 = todo_logic.add_task("Task 3", priority="normal", filepath=temp_task_file)

    todo_logic.toggle_task(t2["id"], filepath=temp_task_file)

    # Status filter
    all_tasks = todo_logic.get_tasks("all", "all", filepath=temp_task_file)
    assert len(all_tasks) == 3

    active_tasks = todo_logic.get_tasks("active", "all", filepath=temp_task_file)
    assert len(active_tasks) == 2
    assert t2["id"] not in [t["id"] for t in active_tasks]

    completed_tasks = todo_logic.get_tasks("completed", "all", filepath=temp_task_file)
    assert len(completed_tasks) == 1
    assert completed_tasks[0]["id"] == t2["id"]

    # Priority filter
    high_tasks = todo_logic.get_tasks("all", "high", filepath=temp_task_file)
    assert len(high_tasks) == 1
    assert high_tasks[0]["id"] == t2["id"]

    # Invalid filters
    with pytest.raises(ValueError, match="Invalid status filter"):
        todo_logic.get_tasks("unknown_status", "all", filepath=temp_task_file)

    with pytest.raises(ValueError, match="Invalid priority filter"):
        todo_logic.get_tasks("all", "unknown_priority", filepath=temp_task_file)


def test_toggle_task(temp_task_file):
    """Verify toggling task between active and completed."""
    task = todo_logic.add_task("Toggle Me", filepath=temp_task_file)
    assert task["completed"] is False

    toggled = todo_logic.toggle_task(task["id"], filepath=temp_task_file)
    assert toggled["completed"] is True
    assert "updated_at" in toggled

    toggled_again = todo_logic.toggle_task(task["id"], filepath=temp_task_file)
    assert toggled_again["completed"] is False

    # Invalid IDs
    with pytest.raises(ValueError, match="valid integer"):
        todo_logic.toggle_task("not-an-id", filepath=temp_task_file)

    with pytest.raises(ValueError, match="not found"):
        todo_logic.toggle_task(999, filepath=temp_task_file)


def test_delete_task(temp_task_file):
    """Verify task deletion and error handling for missing tasks."""
    task = todo_logic.add_task("Delete Me", filepath=temp_task_file)
    deleted = todo_logic.delete_task(task["id"], filepath=temp_task_file)
    assert deleted["id"] == task["id"]

    remaining = todo_logic.load_tasks(temp_task_file)
    assert len(remaining) == 0

    with pytest.raises(ValueError, match="valid integer"):
        todo_logic.delete_task("invalid", filepath=temp_task_file)

    with pytest.raises(ValueError, match="not found"):
        todo_logic.delete_task(999, filepath=temp_task_file)


def test_load_corrupted_file(tmp_path):
    """Verify graceful handling when data file contains corrupt JSON."""
    corrupted_file = str(tmp_path / "corrupt.json")
    with open(corrupted_file, "w", encoding="utf-8") as f:
        f.write("{ invalid_json: true ")

    tasks = todo_logic.load_tasks(corrupted_file)
    assert tasks == []

    # Non-existent file
    missing = todo_logic.load_tasks(str(tmp_path / "missing.json"))
    assert missing == []


def test_task_summary(temp_task_file):
    """Verify summary statistics calculation."""
    todo_logic.add_task("Task A", priority="high", filepath=temp_task_file)
    t2 = todo_logic.add_task("Task B", priority="normal", filepath=temp_task_file)
    todo_logic.add_task("Task C", priority="high", filepath=temp_task_file)

    todo_logic.toggle_task(t2["id"], filepath=temp_task_file)

    stats = todo_logic.get_task_summary(filepath=temp_task_file)
    assert stats["total"] == 3
    assert stats["completed"] == 1
    assert stats["pending"] == 2
    assert stats["high_priority"] == 2


def test_batch_process_tasks(temp_task_file):
    """Verify batch processing, validation rules, and error tolerance."""
    raw_records = [
        {"title": "Valid 1", "priority": "high", "tags": ["work"]},
        {"title": "Valid 2", "completed": True, "priority": "low", "tags": ["work"]},
        {"title": "", "priority": "normal"},  # Empty title -> error in permissive mode
        "invalid_record_string",  # Invalid type -> error in permissive mode
        {"title": "Valid 3", "priority": "invalid_priority", "tags": ["home"]}
    ]

    # Permissive mode
    result = todo_logic.batch_process_tasks(
        raw_records,
        options={"auto_complete": False, "strict_mode": False, "tag_filter": None},
        filepath=temp_task_file
    )
    assert result["processed_count"] == 3
    assert result["error_count"] == 2
    assert len(result["tasks"]) == 3

    # Type error on non-list
    with pytest.raises(TypeError, match="must be a list"):
        todo_logic.batch_process_tasks("not a list", filepath=temp_task_file)

    # Strict mode on invalid record
    with pytest.raises(ValueError, match="is not a valid dictionary"):
        todo_logic.batch_process_tasks(["not_dict"], options={"strict_mode": True}, filepath=temp_task_file)

    # Strict mode on empty title
    with pytest.raises(ValueError, match="Title cannot be empty"):
        todo_logic.batch_process_tasks([{"title": ""}], options={"strict_mode": True}, filepath=temp_task_file)

    # Strict mode on invalid priority
    with pytest.raises(ValueError, match="Invalid priority"):
        todo_logic.batch_process_tasks([{"title": "T", "priority": "urgent"}], options={"strict_mode": True}, filepath=temp_task_file)


# ==========================================
# Flask API Integration Tests (app.py)
# ==========================================

def test_index_and_dashboard_pages(client):
    """Verify HTML pages load with HTTP 200."""
    resp_index = client.get("/")
    assert resp_index.status_code == 200
    assert b"To-Do" in resp_index.data

    resp_dash = client.get("/dashboard")
    assert resp_dash.status_code == 200
    assert b"Quality" in resp_dash.data or b"Dashboard" in resp_dash.data


def test_api_tasks_crud_flow(client):
    """Test full CRUD lifecycle via REST API."""
    # 1. Get empty tasks
    res = client.get("/api/tasks")
    assert res.status_code == 200
    assert res.get_json() == []

    # 2. Create task
    payload = {
        "title": "API Test Task",
        "description": "Testing from pytest client",
        "priority": "high"
    }
    res_post = client.post("/api/tasks", json=payload)
    assert res_post.status_code == 201
    created = res_post.get_json()
    task_id = created["id"]
    assert created["title"] == "API Test Task"

    # 3. Bad request on empty title
    bad_res = client.post("/api/tasks", json={"title": ""})
    assert bad_res.status_code == 400
    assert "error" in bad_res.get_json()

    # 4. Toggle task
    res_toggle = client.put(f"/api/tasks/{task_id}")
    assert res_toggle.status_code == 200
    assert res_toggle.get_json()["completed"] is True

    # 5. Toggle non-existent task
    res_toggle_missing = client.put("/api/tasks/9999")
    assert res_toggle_missing.status_code == 404

    # 6. Delete task
    res_delete = client.delete(f"/api/tasks/{task_id}")
    assert res_delete.status_code == 200

    # 7. Delete non-existent task
    res_delete_missing = client.delete(f"/api/tasks/{task_id}")
    assert res_delete_missing.status_code == 404
