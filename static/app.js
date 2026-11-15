/**
 * static/app.js - Frontend Client Logic for TaskFlow To-Do Application.
 * Handles task creation, toggling, filtering, deletion, and reactive statistics.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Application State
  let currentStatus = "all";
  let currentPriority = "all";

  // DOM Elements
  const addTaskForm = document.getElementById("add-task-form");
  const taskTitleInput = document.getElementById("task-title");
  const taskDescInput = document.getElementById("task-desc");
  const taskPrioritySelect = document.getElementById("task-priority");
  const tasksListContainer = document.getElementById("tasks-list");
  const emptyState = document.getElementById("empty-state");
  const filterStatusBtns = document.querySelectorAll("[data-filter-status]");
  const filterPrioritySelect = document.getElementById("filter-priority-select");
  const toastEl = document.getElementById("toast");

  // Summary Stat Elements
  const statTotal = document.getElementById("stat-total");
  const statPending = document.getElementById("stat-pending");
  const statCompleted = document.getElementById("stat-completed");
  const statHigh = document.getElementById("stat-high");

  /**
   * Display temporary toast notification.
   */
  function showToast(message, type = "info") {
    toastEl.textContent = message;
    toastEl.className = "toast show";
    if (type === "error") {
      toastEl.style.borderColor = "#ef4444";
      toastEl.style.color = "#f87171";
    } else if (type === "success") {
      toastEl.style.borderColor = "#10b981";
      toastEl.style.color = "#34d399";
    } else {
      toastEl.style.borderColor = "#3b82f6";
      toastEl.style.color = "#93c5fd";
    }

    setTimeout(() => {
      toastEl.className = "toast";
    }, 3200);
  }

  /**
   * Fetch and update top summary counter pills.
   */
  async function fetchStats() {
    try {
      const res = await fetch("/api/stats");
      if (!res.ok) return;
      const stats = await res.json();
      statTotal.textContent = stats.total || 0;
      statPending.textContent = stats.pending || 0;
      statCompleted.textContent = stats.completed || 0;
      statHigh.textContent = stats.high_priority || 0;
    } catch (err) {
      console.error("Failed to load task statistics:", err);
    }
  }

  /**
   * Fetch tasks with current status and priority filters and render.
   */
  async function fetchTasks() {
    try {
      const url = `/api/tasks?status=${encodeURIComponent(currentStatus)}&priority=${encodeURIComponent(currentPriority)}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error("Could not fetch tasks");
      const tasks = await res.json();

      renderTasks(tasks);
      fetchStats();
    } catch (err) {
      console.error("Fetch tasks error:", err);
      showToast("Error loading tasks", "error");
    }
  }

  /**
   * Render tasks into DOM list.
   */
  function renderTasks(tasks) {
    tasksListContainer.innerHTML = "";

    if (!tasks || tasks.length === 0) {
      emptyState.style.display = "block";
      return;
    }

    emptyState.style.display = "none";

    tasks.forEach(task => {
      const item = document.createElement("div");
      item.className = `task-item ${task.completed ? "completed" : ""}`;
      item.dataset.id = task.id;

      const priorityBadgeClass = `badge-${task.priority || "normal"}`;

      item.innerHTML = `
        <div class="task-left">
          <div class="task-checkbox-custom" title="Toggle status" role="button" tabindex="0">
            ${task.completed ? "✓" : ""}
          </div>
          <div class="task-info">
            <span class="task-title">${escapeHtml(task.title)}</span>
            ${task.description ? `<span class="task-desc">${escapeHtml(task.description)}</span>` : ""}
          </div>
        </div>
        <div class="task-right">
          <span class="badge ${priorityBadgeClass}">${escapeHtml(task.priority || "normal")}</span>
          <button class="btn-delete" title="Delete Task" aria-label="Delete Task">✕</button>
        </div>
      `;

      // Toggle status on checkbox click
      const checkbox = item.querySelector(".task-checkbox-custom");
      checkbox.addEventListener("click", () => toggleTask(task.id));
      checkbox.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          toggleTask(task.id);
        }
      });

      // Delete task
      const deleteBtn = item.querySelector(".btn-delete");
      deleteBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        deleteTask(task.id);
      });

      tasksListContainer.appendChild(item);
    });
  }

  /**
   * Escape HTML utility to prevent XSS.
   */
  function escapeHtml(text) {
    if (!text) return "";
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * Add Task form submission.
   */
  addTaskForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = taskTitleInput.value.trim();
    const description = taskDescInput.value.trim();
    const priority = taskPrioritySelect.value;

    if (!title) {
      showToast("Please enter a task title.", "error");
      return;
    }

    try {
      const res = await fetch("/api/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, description, priority })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || "Failed to create task");
      }

      taskTitleInput.value = "";
      taskDescInput.value = "";
      taskPrioritySelect.value = "normal";

      showToast(`Task "${data.title}" created successfully!`, "success");
      fetchTasks();
    } catch (err) {
      showToast(err.message, "error");
    }
  });

  /**
   * Toggle task completion.
   */
  async function toggleTask(taskId) {
    try {
      const res = await fetch(`/api/tasks/${taskId}`, { method: "PUT" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Could not toggle task");

      const statusText = data.completed ? "marked completed" : "reopened";
      showToast(`Task #${data.id} ${statusText}.`, "info");
      fetchTasks();
    } catch (err) {
      showToast(err.message, "error");
    }
  }

  /**
   * Delete task by ID.
   */
  async function deleteTask(taskId) {
    try {
      const res = await fetch(`/api/tasks/${taskId}`, { method: "DELETE" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Could not delete task");

      showToast("Task deleted successfully.", "info");
      fetchTasks();
    } catch (err) {
      showToast(err.message, "error");
    }
  }

  /**
   * Status filter buttons click handlers.
   */
  filterStatusBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      filterStatusBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentStatus = btn.dataset.filterStatus;
      fetchTasks();
    });
  });

  /**
   * Priority filter dropdown handler.
   */
  filterPrioritySelect.addEventListener("change", (e) => {
    currentPriority = e.target.value;
    fetchTasks();
  });

  // Initial load
  fetchTasks();
});
