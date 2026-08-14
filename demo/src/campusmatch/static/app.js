const byId = (id) => document.getElementById(id);
const form = byId("analysis-form");
const demoButton = byId("run-demo");
const analyzeButton = byId("analyze");
const resultSection = byId("result");
const formMessage = byId("form-message");
const materialInput = byId("material-markdown");
const jobInput = byId("job-markdown");
const modeInput = byId("career-mode");

let taskId = makeTaskId();

function makeTaskId() {
  const suffix = globalThis.crypto?.randomUUID?.().slice(0, 8) ?? Date.now().toString(36);
  return `web-${suffix}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function clamp(value) {
  return Math.min(100, Math.max(0, Number(value) || 0));
}

function showMessage(message = "") {
  formMessage.hidden = !message;
  formMessage.textContent = message;
}

function setBusy(busy, label = "正在分析…") {
  analyzeButton.disabled = busy;
  demoButton.disabled = busy;
  analyzeButton.textContent = busy ? label : "开始证据化分析 →";
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  let payload;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }
  if (!response.ok) {
    const message = payload?.detail?.message || "服务暂时不可用，请稍后重试。";
    throw new Error(message);
  }
  return payload;
}

async function convertFile(file, target, status) {
  if (!file) return;
  status.className = "file-status";
  status.textContent = `正在读取 ${file.name}…`;
  const body = new FormData();
  body.append("file", file);
  try {
    const data = await api("/api/v1/documents/convert", { method: "POST", body });
    target.value = data.markdown;
    status.className = "file-status ok";
    status.textContent = `已转换 ${data.filename} · ${data.char_count} 个字符；可在上方继续修改。`;
  } catch (error) {
    status.className = "file-status error";
    status.textContent = error.message;
  }
}

byId("material-file").addEventListener("change", (event) => {
  convertFile(event.target.files[0], materialInput, byId("material-status"));
});

byId("job-file").addEventListener("change", (event) => {
  convertFile(event.target.files[0], jobInput, byId("job-status"));
});

function analysisPayload(humanApproved) {
  return {
    task_id: taskId,
    markdown: materialInput.value,
    job_markdown: jobInput.value,
    mode: modeInput.value,
    consent_granted: byId("consent").checked,
    human_approved: humanApproved,
  };
}

async function runAnalysis(humanApproved = false) {
  showMessage();
  if (!materialInput.value.trim() || !jobInput.value.trim()) {
    showMessage("请先提供经历材料和岗位 JD；也可以点击“使用演示案例”。");
    return;
  }
  if (!byId("consent").checked) {
    showMessage("请先确认材料使用授权。没有授权，系统不会开始分析。");
    return;
  }

  setBusy(true, humanApproved ? "正在重新审计…" : "5 个 Agent 正在协作…");
  try {
    const data = await api("/api/v1/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(analysisPayload(humanApproved)),
    });
    renderResult(data);
  } catch (error) {
    showMessage(error.message);
  } finally {
    setBusy(false);
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  taskId = makeTaskId();
  byId("human-approval").checked = false;
  runAnalysis(false);
});

demoButton.addEventListener("click", async () => {
  setBusy(true, "正在载入案例…");
  showMessage();
  try {
    const demo = await api("/api/v1/demo/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task_id: "preview", human_approved: false }),
    });
    materialInput.value = demo.markdown;
    jobInput.value = demo.job_markdown;
    modeInput.value = "job_search";
    byId("consent").checked = true;
    taskId = makeTaskId();
    await runAnalysis(false);
  } catch (error) {
    showMessage(error.message);
  } finally {
    setBusy(false);
  }
});

byId("approve").addEventListener("click", () => {
  if (!byId("human-approval").checked) {
    showMessage("请先勾选“我已核对并确认最终内容”，再提交审计。");
    resultSection.scrollIntoView({ behavior: "smooth", block: "end" });
    return;
  }
  runAnalysis(true);
});

function stateMeta(state) {
  const map = {
    MATCH: ["符合", "match"],
    PARTIAL: ["部分符合", "partial"],
    NO_EVIDENCE: ["缺少证据", "missing"],
    GAP: ["待提升", "missing"],
    CONFLICT: ["信息冲突", "missing"],
    POLICY_EXCLUDED: ["合规排除", "excluded"],
  };
  return map[state] || [state, "excluded"];
}

function renderRadar(items) {
  const dimensions = items.filter((item) => item.counted).slice(0, 5);
  while (dimensions.length < 5) {
    dimensions.push({ label: "待补充", coefficient: 0 });
  }
  const point = (index, radius) => {
    const angle = -Math.PI / 2 + (index * Math.PI * 2) / 5;
    return `${(60 + Math.cos(angle) * radius).toFixed(1)},${(60 + Math.sin(angle) * radius).toFixed(1)}`;
  };
  const outer = dimensions.map((_, index) => point(index, 48)).join(" ");
  const middle = dimensions.map((_, index) => point(index, 30)).join(" ");
  const value = dimensions.map((item, index) => point(index, 48 * clamp(item.coefficient))).join(" ");
  const axes = dimensions.map((_, index) => {
    const [x, y] = point(index, 48).split(",");
    return `<line x1="60" y1="60" x2="${x}" y2="${y}" />`;
  }).join("");
  byId("radar-chart").innerHTML = `
    <svg viewBox="0 0 120 120" role="img" aria-label="五项岗位能力匹配结构">
      <polygon points="${outer}" fill="none" stroke="#ccd7e8" stroke-width="1" />
      <polygon points="${middle}" fill="none" stroke="#e0e6ef" stroke-width="1" />
      <g stroke="#e0e6ef" stroke-width="1">${axes}</g>
      <polygon points="${value}" fill="rgba(49,91,232,.22)" stroke="#315be8" stroke-width="2" />
    </svg>
    <div class="radar-legend">${dimensions.map((item) => `<span>${escapeHtml(item.label)}</span>`).join("")}</div>`;
}

function renderProfile(data) {
  const evidence = Object.fromEntries(data.profile.evidence.map((item) => [item.evidence_id, item]));
  const groups = data.profile.competencies.map((competency) => {
    const quotes = competency.evidence_refs.map((reference) => {
      const item = evidence[reference];
      return `<blockquote class="evidence-quote"><small>${escapeHtml(reference)} · 原文第 ${item.line_start} 行</small>${escapeHtml(item.quote)}</blockquote>`;
    }).join("");
    return `<section class="evidence-group"><h4>${escapeHtml(competency.label)}</h4>${quotes}</section>`;
  }).join("");
  byId("profile-results").innerHTML = groups || '<p class="field-help">当前没有识别到可核对的能力证据，请补充具体任务、本人动作和结果。</p>';
}

function renderMatches(data) {
  byId("match-results").innerHTML = data.match.items.map((item) => {
    const [label, className] = stateMeta(item.state);
    const width = item.counted ? clamp(item.coefficient * 100) : 0;
    return `<section class="match-item">
      <div class="match-head"><h4>${escapeHtml(item.label)}</h4><span class="status-pill ${className}">${label}</span></div>
      <p>${escapeHtml(item.reason)}${item.counted ? ` · 权重 ${item.weight}%` : " · 不参与评分"}</p>
      <div class="weight-bar" aria-hidden="true"><i style="width:${width}%"></i></div>
    </section>`;
  }).join("");
}

function renderCoach(data) {
  const suggestions = data.coaching.resume_suggestions.length
    ? data.coaching.resume_suggestions.map((item) => `<div class="suggestion"><p>${escapeHtml(item.suggestion)}</p><small>依据：${item.evidence_refs.map(escapeHtml).join("、")}${item.needs_confirmation ? " · 需本人再次确认" : ""}</small></div>`).join("")
    : '<p class="field-help">证据不足，暂不生成简历表述，避免虚构经历。</p>';
  const learning = data.coaching.learning_plan.map((item) => `<li><strong>${escapeHtml(item.target)}</strong><br />${escapeHtml(item.action)}</li>`).join("");
  const interviews = data.coaching.interview_questions.map((item) => `<li>${escapeHtml(item.question)}</li>`).join("");
  byId("coach-results").innerHTML = `
    <section class="coach-section"><h4>简历表述建议</h4>${suggestions}</section>
    <section class="coach-section"><h4>补证 / 学习计划</h4><ul>${learning}</ul></section>
    <section class="coach-section"><h4>模拟面试查漏</h4><ul>${interviews}</ul></section>`;
}

function renderAudit(data) {
  const passed = data.audit.status === "PASS";
  const issues = data.audit.issues.length
    ? data.audit.issues.map((item) => `<div class="audit-issue"><strong>${escapeHtml(item.code)}</strong><br />${escapeHtml(item.message)}<br /><small>处理：${escapeHtml(item.action)}</small></div>`).join("")
    : '<div class="audit-issue" style="color:#14674f;background:#effbf6">证据、隐私、公平、Trace 与人工审批均已通过。</div>';
  byId("audit-results").innerHTML = `<div class="audit-state ${passed ? "pass" : ""}"><i></i>${passed ? "PASS · 允许导出" : "BLOCK · 暂停导出"}</div>${issues}`;
  byId("trace-results").innerHTML = data.trace.map((event) => `<li><strong>${escapeHtml(event.agent)}</strong>${escapeHtml(event.detail)}</li>`).join("");
}

function renderResult(data) {
  resultSection.hidden = false;
  const passed = data.audit.export_allowed;
  const status = byId("result-status");
  status.className = `result-status ${passed ? "pass" : ""}`;
  status.innerHTML = passed
    ? '<strong>审计已通过，可以导出</strong><span>最终内容已由人工确认；请妥善保存报告。</span>'
    : '<strong>分析完成，导出仍处于保护状态</strong><span>先核对证据与建议，再由你亲自批准。</span>';

  const matchScore = clamp(data.match.match_score);
  const coverage = clamp(data.match.evidence_coverage);
  byId("match-ring").style.setProperty("--score", matchScore);
  byId("coverage-ring").style.setProperty("--score", coverage);
  byId("match-score").textContent = data.match.match_score;
  byId("coverage-score").textContent = data.match.evidence_coverage;
  renderRadar(data.match.items);
  renderProfile(data);
  renderMatches(data);
  renderCoach(data);
  renderAudit(data);
  byId("material-preview").textContent = data.markdown;
  byId("job-preview").textContent = data.job_markdown;

  const exportLink = byId("export-report");
  if (passed) {
    exportLink.href = `/api/v1/reports/${encodeURIComponent(data.task_id)}.md`;
    exportLink.classList.remove("disabled");
    exportLink.setAttribute("aria-disabled", "false");
  } else {
    exportLink.href = "#";
    exportLink.classList.add("disabled");
    exportLink.setAttribute("aria-disabled", "true");
  }
  resultSection.scrollIntoView({ behavior: "smooth", block: "start" });
}
