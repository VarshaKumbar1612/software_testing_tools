"""
todo_logic.py - Core business logic for To-Do task management.
Designed with distinct validation rules and branching to showcase
unit test coverage and McCabe Cyclomatic Complexity metrics.
"""

import json
import os
from datetime import datetime

DEFAULT_DATA_FILE = "tasks.json"
ALLOWED_PRIORITIES = {"low", "normal", "high"}


def get_data_filepath():
    """Retrieve active data storage file path, allowing environment override."""
    return os.environ.get("TODO_DATA_FILE", DEFAULT_DATA_FILE)


def load_tasks(filepath=None):
    """Load tasks safely from a local JSON file."""
    path = filepath if filepath is not None else get_data_filepath()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, OSError):
        return []


def save_tasks(tasks, filepath=None):
    """Save tasks to local JSON file."""
    path = filepath if filepath is not None else get_data_filepath()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2)


def get_tasks(status="all", priority="all", filepath=None):
    """
    Retrieve tasks with optional status and priority filtering.
    Status options: 'all', 'active', 'completed'.
    Priority options: 'all', 'low', 'normal', 'high'.
    """
    path = filepath if filepath is not None else get_data_filepath()
    tasks = load_tasks(path)
    filtered = []

    for task in tasks:
        # Check status filter
        if status == "active" and task.get("completed", False):
            continue
        elif status == "completed" and not task.get("completed", False):
            continue
        elif status not in ("all", "active", "completed"):
            raise ValueError(f"Invalid status filter: {status}")

        # Check priority filter
        if priority != "all":
            if priority not in ALLOWED_PRIORITIES:
                raise ValueError(f"Invalid priority filter: {priority}")
            if task.get("priority", "normal") != priority:
                continue

        filtered.append(task)

    return filtered


def add_task(title, description="", priority="normal", filepath=None):
    """
    Validate and add a new task to the task list.
    Returns the newly created task dict.
    """
    path = filepath if filepath is not None else get_data_filepath()
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Task title cannot be empty.")

    cleaned_title = title.strip()
    if len(cleaned_title) > 120:
        raise ValueError("Task title exceeds 120 characters limit.")

    cleaned_priority = str(priority).lower().strip()
    if cleaned_priority not in ALLOWED_PRIORITIES:
        raise ValueError(f"Priority must be one of: {', '.join(sorted(ALLOWED_PRIORITIES))}")

    tasks = load_tasks(path)
    next_id = max([t.get("id", 0) for t in tasks], default=0) + 1

    new_task = {
        "id": next_id,
        "title": cleaned_title,
        "description": description.strip() if isinstance(description, str) else "",
        "priority": cleaned_priority,
        "completed": False,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }

    tasks.append(new_task)
    save_tasks(tasks, path)
    return new_task


def toggle_task(task_id, filepath=None):
    """
    Toggle task completion status between completed and active.
    Returns updated task dict, or raises ValueError if not found.
    """
    path = filepath if filepath is not None else get_data_filepath()
    try:
        numeric_id = int(task_id)
    except (ValueError, TypeError):
        raise ValueError("Task ID must be a valid integer.")

    tasks = load_tasks(path)
    target_task = None

    for task in tasks:
        if task.get("id") == numeric_id:
            target_task = task
            break

    if target_task is None:
        raise ValueError(f"Task with ID {numeric_id} not found.")

    target_task["completed"] = not target_task.get("completed", False)
    target_task["updated_at"] = datetime.utcnow().isoformat() + "Z"

    save_tasks(tasks, path)
    return target_task


def delete_task(task_id, filepath=None):
    """
    Delete a task by ID.
    Returns the deleted task dict, or raises ValueError if not found.
    """
    path = filepath if filepath is not None else get_data_filepath()
    try:
        numeric_id = int(task_id)
    except (ValueError, TypeError):
        raise ValueError("Task ID must be a valid integer.")

    tasks = load_tasks(path)
    remaining_tasks = []
    deleted_task = None

    for task in tasks:
        if task.get("id") == numeric_id:
            deleted_task = task
        else:
            remaining_tasks.append(task)

    if deleted_task is None:
        raise ValueError(f"Task with ID {numeric_id} not found.")

    save_tasks(remaining_tasks, path)
    return deleted_task


def get_task_summary(filepath=None):
    """Calculate summary statistics for dashboard or overview."""
    path = filepath if filepath is not None else get_data_filepath()
    tasks = load_tasks(path)
    total = len(tasks)
    completed = sum(1 for t in tasks if t.get("completed", False))
    pending = total - completed
    high_priority = sum(1 for t in tasks if t.get("priority") == "high" and not t.get("completed", False))

    return {
        "total": total,
        "completed": completed,
        "pending": pending,
        "high_priority": high_priority
    }


def batch_process_tasks(task_records, options=None, filepath=None):
    """
    Process and import multiple task records in batch.
    Demonstrates high Cyclomatic Complexity (M > 10) through extensive branching,
    strict vs. permissive input sanitization, and multi-rule validation.
    """
    path = filepath if filepath is not None else get_data_filepath()
    if options is None:
        options = {}

    auto_complete = options.get("auto_complete", False)
    default_priority = options.get("default_priority", "normal")
    strict_mode = options.get("strict_mode", False)
    tag_filter = options.get("tag_filter", None)

    if not isinstance(task_records, list):
        raise TypeError("task_records must be a list of task dictionaries.")

    processed = []
    errors = []

    for index, record in enumerate(task_records):
        if not isinstance(record, dict):
            if strict_mode:
                raise ValueError(f"Record at index {index} is not a valid dictionary.")
            errors.append(f"Index {index}: Invalid record structure.")
            continue

        title = record.get("title", "")
        if not title or not isinstance(title, str) or not title.strip():
            if strict_mode:
                raise ValueError(f"Record {index}: Title cannot be empty.")
            errors.append(f"Index {index}: Empty title omitted.")
            continue

        raw_priority = record.get("priority", default_priority)
        if raw_priority not in ALLOWED_PRIORITIES:
            if strict_mode:
                raise ValueError(f"Record {index}: Invalid priority '{raw_priority}'.")
            priority = default_priority
        else:
            priority = raw_priority

        if tag_filter:
            tags = record.get("tags", [])
            if tag_filter not in tags:
                continue

        task_entry = add_task(
            title=title.strip(),
            description=record.get("description", ""),
            priority=priority,
            filepath=path
        )

        if auto_complete or record.get("completed", False):
            task_entry = toggle_task(task_entry["id"], filepath=path)

        processed.append(task_entry)

    return {
        "processed_count": len(processed),
        "error_count": len(errors),
        "tasks": processed,
        "errors": errors
    }
