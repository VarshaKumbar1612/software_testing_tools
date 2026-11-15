"""
audit_runner.py - Automated QA Audit Suite.
Executes PyTest, Coverage.py, Flake8, Bandit, and Radon (McCabe Complexity)
via subprocess and aggregates the output into unified structured JSON.
"""

import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _run_cmd(cmd_args):
    """Execute a CLI command safely and return (returncode, stdout, stderr)."""
    try:
        proc = subprocess.run(
            cmd_args,
            cwd=BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
            check=False
        )
        return proc.returncode, proc.stdout, proc.stderr
    except Exception as err:
        return -1, "", str(err)


def run_pytest_and_coverage():
    """
    Run PyTest with Coverage.py.
    Collects unit test counts (passed, failed, total, duration)
    and coverage percentage metrics.
    """
    coverage_file = os.path.join(BASE_DIR, ".coverage_audit.json")
    junit_file = os.path.join(BASE_DIR, ".junit_report.xml")

    # Clean existing temp report files if present
    for temp_f in (coverage_file, junit_file):
        if os.path.exists(temp_f):
            try:
                os.remove(temp_f)
            except OSError:
                pass

    # 1. Run Coverage with PyTest and JUnit XML output
    cmd = [
        sys.executable,
        "-m",
        "coverage",
        "run",
        "--source=todo_logic,app",
        "-m",
        "pytest",
        "tests",
        f"--junitxml={junit_file}"
    ]
    _run_cmd(cmd)

    # 2. Export Coverage JSON
    cmd_cov_json = [
        sys.executable,
        "-m",
        "coverage",
        "json",
        "-o",
        coverage_file
    ]
    _run_cmd(cmd_cov_json)

    # 3. Parse PyTest results from JUnit XML
    pytest_stats = {
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "skipped": 0,
        "total": 0,
        "duration": 0.0,
        "tests": []
    }

    if os.path.exists(junit_file):
        try:
            tree = ET.parse(junit_file)
            root = tree.getroot()
            # Handle either testsuite or testsuites root
            suite = root if root.tag == "testsuite" else root.find("testsuite")
            if suite is not None:
                total = int(suite.attrib.get("tests", 0))
                failures = int(suite.attrib.get("failures", 0))
                errors = int(suite.attrib.get("errors", 0))
                skipped = int(suite.attrib.get("skipped", 0))
                duration = float(suite.attrib.get("time", 0.0))
                passed = max(0, total - (failures + errors + skipped))

                pytest_stats["total"] = total
                pytest_stats["passed"] = passed
                pytest_stats["failed"] = failures
                pytest_stats["errors"] = errors
                pytest_stats["skipped"] = skipped
                pytest_stats["duration"] = round(duration, 3)

                for case in suite.findall("testcase"):
                    case_name = case.attrib.get("name", "unknown")
                    case_time = float(case.attrib.get("time", 0.0))
                    status = "passed"
                    fail_elem = case.find("failure") or case.find("error")
                    if fail_elem is not None:
                        status = "failed"
                    elif case.find("skipped") is not None:
                        status = "skipped"

                    pytest_stats["tests"].append({
                        "name": case_name,
                        "duration": round(case_time, 4),
                        "status": status
                    })
        except Exception as err:
            pytest_stats["error"] = f"Failed to parse JUnit XML: {err}"

    # 4. Parse Coverage JSON
    coverage_stats = {
        "percent": 0.0,
        "covered_lines": 0,
        "total_lines": 0,
        "missing_lines": 0,
        "files": {}
    }

    if os.path.exists(coverage_file):
        try:
            with open(coverage_file, "r", encoding="utf-8") as f:
                cov_data = json.load(f)
            totals = cov_data.get("totals", {})
            coverage_stats["percent"] = round(float(totals.get("percent_covered", 0.0)), 1)
            coverage_stats["covered_lines"] = int(totals.get("covered_lines", 0))
            coverage_stats["total_lines"] = int(totals.get("num_statements", 0))
            coverage_stats["missing_lines"] = int(totals.get("missing_lines", 0))

            # Per-file summary
            for fname, finfo in cov_data.get("files", {}).items():
                short_name = os.path.basename(fname)
                f_summary = finfo.get("summary", {})
                coverage_stats["files"][short_name] = {
                    "percent": round(float(f_summary.get("percent_covered", 0.0)), 1),
                    "covered": f_summary.get("covered_lines", 0),
                    "total": f_summary.get("num_statements", 0),
                    "missing": f_summary.get("missing_lines", 0)
                }
        except Exception as err:
            coverage_stats["error"] = f"Failed to parse Coverage JSON: {err}"

    # Cleanup temp files
    for temp_f in (coverage_file, junit_file):
        if os.path.exists(temp_f):
            try:
                os.remove(temp_f)
            except OSError:
                pass

    return pytest_stats, coverage_stats


def run_flake8():
    """
    Run Flake8 linting and static analysis on application files.
    Returns list of PEP 8 style & formatting issues.
    """
    cmd = [
        sys.executable,
        "-m",
        "flake8",
        "todo_logic.py",
        "app.py"
    ]
    _, stdout, _ = _run_cmd(cmd)

    issues = []
    # Pattern: path:line:col: code message
    pattern = re.compile(r"^([^:]+):(\d+):(\d+):\s*([A-Z]\d+)\s*(.*)$")

    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        match = pattern.match(line)
        if match:
            fpath, lno, col, code, msg = match.groups()
            issues.append({
                "file": os.path.basename(fpath),
                "line": int(lno),
                "col": int(col),
                "code": code,
                "msg": msg
            })
        else:
            # Fallback if unformatted line
            issues.append({
                "file": "app",
                "line": 0,
                "col": 0,
                "code": "INFO",
                "msg": line
            })

    return issues


def run_bandit():
    """
    Run Bandit security scanner on application files.
    Returns list of security findings with severity, confidence, and CWE info.
    """
    cmd = [
        sys.executable,
        "-m",
        "bandit",
        "-r",
        "todo_logic.py",
        "app.py",
        "-f",
        "json"
    ]
    _, stdout, _ = _run_cmd(cmd)

    findings = []
    # Bandit prints log lines before JSON output. Find JSON start '{'
    json_start = stdout.find("{")
    if json_start != -1:
        json_str = stdout[json_start:]
        try:
            data = json.loads(json_str)
            for item in data.get("results", []):
                findings.append({
                    "file": os.path.basename(item.get("filename", "")),
                    "line": item.get("line_number", 0),
                    "code": item.get("test_id", ""),
                    "severity": item.get("issue_severity", "LOW"),
                    "confidence": item.get("issue_confidence", "LOW"),
                    "issue": item.get("issue_text", ""),
                    "cwe": item.get("issue_cwe", {}).get("id", "")
                })
        except json.JSONDecodeError:
            pass

    return findings


def run_radon_mccabe():
    """
    Run Radon Cyclomatic Complexity analyzer on application files.
    Applies Defect Prediction Rule:
      - Complexity 1 to 5  : Low Defect Risk (Green)
      - Complexity 6 to 10 : Moderate Defect Risk (Yellow)
      - Complexity > 10    : High Defect Risk (Red)
    """
    cmd = [
        sys.executable,
        "-m",
        "radon",
        "cc",
        "todo_logic.py",
        "app.py",
        "-j"
    ]
    _, stdout, _ = _run_cmd(cmd)

    items = []
    try:
        data = json.loads(stdout)
        for filepath, funcs in data.items():
            base_file = os.path.basename(filepath)
            for item in funcs:
                comp = item.get("complexity", 1)
                rank = item.get("rank", "A")

                # Defect Prediction categorization
                if comp <= 5:
                    risk = "Low Defect Risk"
                    risk_badge = "success"
                elif comp <= 10:
                    risk = "Moderate Defect Risk"
                    risk_badge = "warning"
                else:
                    risk = "High Defect Risk"
                    risk_badge = "danger"

                items.append({
                    "file": base_file,
                    "function": item.get("name", "unknown"),
                    "complexity": comp,
                    "rank": rank,
                    "line": item.get("lineno", 0),
                    "risk": risk,
                    "risk_badge": risk_badge
                })
    except json.JSONDecodeError:
        pass

    # Sort descending by complexity for best analysis display
    items.sort(key=lambda x: x["complexity"], reverse=True)
    return items


def run_all():
    """Execute all 5 tools and return the consolidated JSON dictionary."""
    pytest_stats, coverage_stats = run_pytest_and_coverage()
    flake8_issues = run_flake8()
    bandit_findings = run_bandit()
    mccabe_metrics = run_radon_mccabe()

    return {
        "pytest": pytest_stats,
        "coverage": coverage_stats,
        "flake8": flake8_issues,
        "bandit": bandit_findings,
        "mccabe": mccabe_metrics,
        "summary": {
            "tests_passed": pytest_stats.get("passed", 0),
            "tests_total": pytest_stats.get("total", 0),
            "coverage_percent": coverage_stats.get("percent", 0.0),
            "flake8_count": len(flake8_issues),
            "bandit_count": len(bandit_findings),
            "mccabe_count": len(mccabe_metrics)
        }
    }


if __name__ == "__main__":
    print("Executing QA Audit Suite...")
    report = run_all()
    print(json.dumps(report, indent=2))
