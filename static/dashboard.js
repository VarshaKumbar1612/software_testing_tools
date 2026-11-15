/**
 * static/dashboard.js - Interactive QA & Defect Prediction Dashboard.
 * Fetches real-time JSON audit metrics from /api/run-audit and renders
 * KPI cards, McCabe complexity table, Flake8 logs, Bandit alerts, and PyTest results.
 */

document.addEventListener("DOMContentLoaded", () => {
  // State
  let auditData = null;
  let currentRiskFilter = "all";

  // Elements
  const rerunBtn = document.getElementById("btn-rerun-audit");
  const rerunIcon = document.getElementById("rerun-icon");
  const rerunText = document.getElementById("rerun-text");
  const auditTimestamp = document.getElementById("audit-timestamp");

  // KPI elements
  const kpiTestsVal = document.getElementById("kpi-tests-val");
  const kpiTestsSub = document.getElementById("kpi-tests-sub");
  const kpiTestsDuration = document.getElementById("kpi-tests-duration");
  const kpiCoverageVal = document.getElementById("kpi-coverage-val");
  const kpiCoverageLines = document.getElementById("kpi-coverage-lines");
  const kpiCoverageBar = document.getElementById("kpi-coverage-bar");
  const kpiFlake8Val = document.getElementById("kpi-flake8-val");
  const kpiFlake8Status = document.getElementById("kpi-flake8-status");
  const kpiBanditVal = document.getElementById("kpi-bandit-val");
  const kpiBanditSeverity = document.getElementById("kpi-bandit-severity");

  // Table & Lists
  const mccabeTbody = document.getElementById("mccabe-tbody");
  const flake8Logs = document.getElementById("flake8-logs");
  const banditLogs = document.getElementById("bandit-logs");
  const pytestTestsList = document.getElementById("pytest-tests-list");
  const fileCoverageList = document.getElementById("file-coverage-list");

  // Badges & Counters
  const flake8PillCount = document.getElementById("flake8-pill-count");
  const banditPillCount = document.getElementById("bandit-pill-count");
  const pytestPillCount = document.getElementById("pytest-pill-count");
  const coveragePillPercent = document.getElementById("coverage-pill-percent");

  // Filter Buttons
  const riskFilterBtns = document.querySelectorAll("[data-filter-risk]");

  /**
   * Fetch QA Audit JSON from backend API.
   */
  async function fetchAuditData() {
    setLoadingState(true);
    try {
      const res = await fetch("/api/run-audit");
      if (!res.ok) throw new Error("Failed to run QA analysis suite.");
      auditData = await res.json();

      auditTimestamp.textContent = new Date().toLocaleTimeString();
      renderDashboard(auditData);
    } catch (err) {
      console.error("Audit Runner Error:", err);
      auditTimestamp.textContent = "Audit execution failed";
      mccabeTbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted" style="color: #ef4444;">Error running audit: ${escapeHtml(err.message)}</td></tr>`;
    } finally {
      setLoadingState(false);
    }
  }

  /**
   * Set loading animation on Re-Run button.
   */
  function setLoadingState(isLoading) {
    if (isLoading) {
      rerunIcon.classList.add("rotating");
      rerunText.textContent = "Running 5 QA Tools...";
      rerunBtn.disabled = true;
    } else {
      rerunIcon.classList.remove("rotating");
      rerunText.textContent = "Re-Run Analysis";
      rerunBtn.disabled = false;
    }
  }

  /**
   * Render all visual dashboard components.
   */
  function renderDashboard(data) {
    renderKPIs(data);
    renderMcCabeTable(data.mccabe || []);
    renderFlake8Issues(data.flake8 || []);
    renderBanditFindings(data.bandit || []);
    renderPytestBreakdown(data.pytest || {});
    renderCoverageBreakdown(data.coverage || {});
  }

  /**
   * Render the 4 Top KPI Cards.
   */
  function renderKPIs(data) {
    const pt = data.pytest || {};
    const cov = data.coverage || {};
    const flk = data.flake8 || [];
    const bnd = data.bandit || [];

    // KPI 1: PyTest
    const passed = pt.passed || 0;
    const total = pt.total || 0;
    kpiTestsVal.textContent = `${passed} / ${total}`;
    kpiTestsSub.textContent = pt.failed === 0 ? "100% Tests Passing" : `${pt.failed} test(s) failed`;
    kpiTestsDuration.textContent = `Duration: ${pt.duration || 0}s (${total} total cases)`;

    // KPI 2: Coverage
    const covPct = cov.percent !== undefined ? cov.percent : 0;
    kpiCoverageVal.textContent = `${covPct}%`;
    kpiCoverageLines.textContent = `${cov.covered_lines || 0} / ${cov.total_lines || 0} statements covered`;
    kpiCoverageBar.style.width = `${Math.min(100, covPct)}%`;
    if (covPct < 80) {
      kpiCoverageBar.style.background = "linear-gradient(90deg, #f59e0b, #fbbf24)";
    } else {
      kpiCoverageBar.style.background = "linear-gradient(90deg, #10b981, #34d399)";
    }
    coveragePillPercent.textContent = `${covPct}%`;

    // KPI 3: Flake8
    kpiFlake8Val.textContent = flk.length;
    kpiFlake8Status.textContent = flk.length === 0 ? "Zero PEP 8 violations" : `${flk.length} styling warning(s)`;
    flake8PillCount.textContent = `${flk.length} Issue${flk.length === 1 ? "" : "s"}`;

    // KPI 4: Bandit
    kpiBanditVal.textContent = bnd.length;
    const highSevCount = bnd.filter(i => (i.severity || "").toUpperCase() === "HIGH").length;
    const medSevCount = bnd.filter(i => (i.severity || "").toUpperCase() === "MEDIUM").length;
    kpiBanditSeverity.textContent = `${highSevCount} High, ${medSevCount} Medium`;
    banditPillCount.textContent = `${bnd.length} Alert${bnd.length === 1 ? "" : "s"}`;
    pytestPillCount.textContent = pt.failed === 0 ? `${passed} Passed` : `${pt.failed} Failed`;
  }

  /**
   * Render McCabe Cyclomatic Defect Prediction Table.
   */
  function renderMcCabeTable(mccabeItems) {
    mccabeTbody.innerHTML = "";

    const filtered = currentRiskFilter === "all"
      ? mccabeItems
      : mccabeItems.filter(item => item.risk === currentRiskFilter);

    if (filtered.length === 0) {
      mccabeTbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted py-4">No functions match the selected risk filter.</td></tr>`;
      return;
    }

    filtered.forEach(item => {
      const tr = document.createElement("tr");

      const badgeClass = item.risk_badge ? `badge-${item.risk_badge}` : "badge-info";

      tr.innerHTML = `
        <td><span class="code-badge">${escapeHtml(item.function)}()</span></td>
        <td><span class="file-badge">${escapeHtml(item.file)}</span></td>
        <td><span class="file-badge">L${item.line}</span></td>
        <td><strong>${item.complexity}</strong></td>
        <td><span class="badge ${item.rank === 'A' ? 'badge-success' : 'badge-warning'}">${escapeHtml(item.rank)}</span></td>
        <td><span class="badge ${badgeClass}">${escapeHtml(item.risk)}</span></td>
      `;
      mccabeTbody.appendChild(tr);
    });
  }

  /**
   * Render Flake8 static analysis findings.
   */
  function renderFlake8Issues(issues) {
    flake8Logs.innerHTML = "";

    if (issues.length === 0) {
      flake8Logs.innerHTML = `
        <div class="text-center py-4" style="color: #10b981;">
          ✓ Flake8 clean! No PEP 8 violations or syntax warnings detected.
        </div>
      `;
      return;
    }

    issues.forEach(issue => {
      const item = document.createElement("div");
      item.className = "log-item";
      item.innerHTML = `
        <div class="log-item-header">
          <span class="log-code">${escapeHtml(issue.code)}</span>
          <span class="log-location">${escapeHtml(issue.file)}:${issue.line}:${issue.col}</span>
        </div>
        <div class="log-desc">${escapeHtml(issue.msg)}</div>
      `;
      flake8Logs.appendChild(item);
    });
  }

  /**
   * Render Bandit AST security alerts.
   */
  function renderBanditFindings(findings) {
    banditLogs.innerHTML = "";

    if (findings.length === 0) {
      banditLogs.innerHTML = `
        <div class="text-center py-4" style="color: #10b981;">
          ✓ Bandit clean! Zero security vulnerabilities identified.
        </div>
      `;
      return;
    }

    findings.forEach(finding => {
      const item = document.createElement("div");
      item.className = "log-item log-bandit";

      const sevBadge = finding.severity === "HIGH" ? "badge-danger" : "badge-warning";

      item.innerHTML = `
        <div class="log-item-header">
          <div>
            <span class="badge ${sevBadge}">${escapeHtml(finding.severity)}</span>
            <span class="log-code" style="margin-left: 0.35rem;">${escapeHtml(finding.code)}</span>
          </div>
          <span class="log-location">${escapeHtml(finding.file)}:L${finding.line}</span>
        </div>
        <div class="log-desc" style="margin-top: 0.35rem;">${escapeHtml(finding.issue)}</div>
        ${finding.cwe ? `<div class="log-location" style="margin-top: 0.25rem;">CWE: #${finding.cwe}</div>` : ""}
      `;
      banditLogs.appendChild(item);
    });
  }

  /**
   * Render PyTest tests list.
   */
  function renderPytestBreakdown(pytestData) {
    pytestTestsList.innerHTML = "";
    const tests = pytestData.tests || [];

    if (tests.length === 0) {
      pytestTestsList.innerHTML = `<div class="text-center text-muted py-4">No tests logged.</div>`;
      return;
    }

    tests.forEach(test => {
      const row = document.createElement("div");
      row.className = "test-row";
      const badgeClass = test.status === "passed" ? "badge-success" : "badge-danger";
      row.innerHTML = `
        <span class="test-name">${escapeHtml(test.name)}</span>
        <div>
          <span class="file-badge" style="margin-right: 0.5rem;">${test.duration}s</span>
          <span class="badge ${badgeClass}">${escapeHtml(test.status)}</span>
        </div>
      `;
      pytestTestsList.appendChild(row);
    });
  }

  /**
   * Render per-file statement coverage.
   */
  function renderCoverageBreakdown(coverageData) {
    fileCoverageList.innerHTML = "";
    const files = coverageData.files || {};
    const fileKeys = Object.keys(files);

    if (fileKeys.length === 0) {
      fileCoverageList.innerHTML = `<div class="text-center text-muted py-4">No module coverage data.</div>`;
      return;
    }

    fileKeys.forEach(fname => {
      const finfo = files[fname];
      const row = document.createElement("div");
      row.className = "file-cov-row";
      row.innerHTML = `
        <div class="file-cov-meta">
          <span class="file-badge" style="font-weight: 600; color: #f8fafc;">${escapeHtml(fname)}</span>
          <span><strong>${finfo.percent}%</strong> (${finfo.covered}/${finfo.total} lines)</span>
        </div>
        <div class="progress-container">
          <div class="progress-bar" style="width: ${Math.min(100, finfo.percent)}%;"></div>
        </div>
      `;
      fileCoverageList.appendChild(row);
    });
  }

  /**
   * Helper utility to escape strings for HTML.
   */
  function escapeHtml(text) {
    if (text === null || text === undefined) return "";
    const div = document.createElement("div");
    div.textContent = String(text);
    return div.innerHTML;
  }

  // Event Listeners
  rerunBtn.addEventListener("click", fetchAuditData);

  riskFilterBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      riskFilterBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentRiskFilter = btn.dataset.filterRisk;
      if (auditData) {
        renderMcCabeTable(auditData.mccabe || []);
      }
    });
  });

  // Initial load
  fetchAuditData();
});
