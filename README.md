# TaskFlow & Automated QA Quality Suite

A complete, lightweight **Software Quality Engineering & Defect Prediction** system built for college-level software testing projects, demonstrations, and viva presentations.

---

## 🎯 Project Overview & Architecture

The project pairs a functional **To-Do Application** (core subject) with an automated **QA Audit Runner** and a **Quality & Defect Prediction Dashboard**.

```text
c:/to-do list testing/
├── app.py                 # Main Flask application (Web UI, REST APIs, and Audit endpoint)
├── todo_logic.py          # Core business logic & validations (isolated for clean tool metrics)
├── audit_runner.py        # Subprocess orchestrator running all 5 QA tools & aggregating JSON
├── requirements.txt       # Dependencies (Flask, PyTest, Coverage, Flake8, Bandit, Radon)
├── tests/
│   └── test_todo.py       # Comprehensive unit tests & Flask integration test suite (10 tests)
├── templates/
│   ├── index.html         # To-Do List interface (Add, Filter, Toggle, Delete, Stats)
│   └── dashboard.html     # QA Quality & Defect Prediction Dashboard UI
└── static/
    ├── style.css          # Modern dark design system
    ├── app.js             # To-Do frontend interaction logic
    └── dashboard.js       # Live dashboard rendering & asynchronous re-audit runner
```

---

## 🔬 The 5 QA & Software Testing Tools

| # | Tool | Purpose | Command Triggered | Viva Key Metric |
|---|---|---|---|---|
| **1** | **PyTest** | Automated Unit & Integration Testing | `pytest tests/` | Test Execution Count, Pass/Fail status, Duration |
| **2** | **Coverage.py** | Dynamic Statement Coverage | `coverage run` + `coverage json` | Total & Per-file Line Coverage Percentage (Target > 90%) |
| **3** | **Flake8** | Static Code Analysis & PEP 8 Style | `flake8 todo_logic.py app.py` | Code smell detection, line length, formatting alerts |
| **4** | **Bandit** | Abstract Syntax Tree (AST) Security Scan | `bandit -r todo_logic.py app.py -f json` | CWE vulnerability IDs, Severity (`HIGH`/`MEDIUM`), Confidence |
| **5** | **Radon (McCabe)** | Cyclomatic Complexity & Defect Prediction | `radon cc todo_logic.py app.py -j` | Cyclomatic Complexity ($M$), Radon Grade, Defect Risk Classification |

---

## 📊 McCabe Cyclomatic Defect Prediction Rule

Thomas J. McCabe formulated Cyclomatic Complexity as:
$$M = E - N + 2P$$
Where:
- $E$ = Number of edges in the control-flow graph
- $N$ = Number of nodes (basic blocks)
- $P$ = Number of connected components (usually 1 per function)

### Defect Likelihood Thresholds (Applied in Dashboard)
- **$M = 1\text{–}5$ (Low Defect Risk - Green)**: Simple, well-structured logic. Highly maintainable and low bug probability.
- **$M = 6\text{–}10$ (Moderate Defect Risk - Yellow)**: Moderate branching. Requires targeted test cases and path coverage.
- **$M > 10$ (High Defect Risk - Red)**: Complex decision logic with high risk of latent defects. Prime candidate for refactoring.

---

## 🚀 How to Run the Project

### 1. Activate the Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```

### 2. Run the Automated QA Audit Suite via CLI
```powershell
python audit_runner.py
```
This executes all 5 tools in parallel through Python's `subprocess` engine and outputs unified JSON metrics.

### 3. Run the Unit Test Suite
```powershell
pytest -v
```

### 4. Check Test Coverage
```powershell
coverage run -m pytest tests/
coverage report -m
```

### 5. Launch the Web Application
```powershell
python app.py
```
Open your web browser:
- **To-Do Application:** `http://127.0.0.1:5000/`
- **QA & Defect Prediction Dashboard:** `http://127.0.0.1:5000/dashboard`

---

## 💡 Viva & Presentation Talking Points

1. **Why separate `todo_logic.py` from `app.py`?**
   - Keeps business logic pure and testable without requiring HTTP request mocks.
   - Allows Radon and Flake8 to measure core algorithmic complexity separately from framework routing code.

2. **Why does Bandit flag warnings in `app.py`?**
   - In `app.py`, `app.run(debug=True, host="0.0.0.0")` was deliberately configured.
   - Bandit catches **B201** (`flask_debug_true`: enables Werkzeug interactive debugger) and **B104** (`hardcoded_bind_all_interfaces`: exposes service externally).
   - This proves the automated security scanner actively detects vulnerabilities.

3. **Live Re-Run Demonstration:**
   - On the `/dashboard` page, click the **"Re-Run Analysis"** button.
   - It invokes `GET /api/run-audit`, runs the live CLI suite in the background, and refreshes the KPI cards, progress bars, and defect prediction table in real time.
