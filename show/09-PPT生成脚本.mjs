import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const OUT_DIR = path.dirname(fileURLToPath(import.meta.url));
const TMP_DIR = path.join(OUT_DIR, ".ppt_tmp", "artifact-preview");
const HERO = path.join(OUT_DIR, "assets", "campusmatch-hero.png");

const W = 1280;
const H = 720;
const C = {
  bg: "#FFFFFF",
  ink: "#101828",
  muted: "#667085",
  faint: "#98A2B3",
  line: "#D0D5DD",
  panel: "#F2F4F7",
  pale: "#EAF2FF",
  blue: "#1666D3",
  blue2: "#4A90E2",
  navy: "#0B3B75",
  green: "#16865B",
  greenPale: "#E8F7F0",
  amber: "#C77800",
  amberPale: "#FFF5D6",
  red: "#C83838",
  redPale: "#FDECEC",
  violet: "#7047B8",
  violetPale: "#F2ECFF",
};
const FONT = "Microsoft YaHei";

function addShape(slide, name, geometry, x, y, w, h, fill = "none", lineFill = "none", lineWidth = 0, radius = undefined) {
  const spec = {
    name,
    geometry,
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: { style: "solid", fill: lineFill, width: lineWidth },
  };
  if (radius) spec.borderRadius = radius;
  return slide.shapes.add(spec);
}

function addText(slide, name, text, x, y, w, h, opts = {}) {
  const box = addShape(
    slide,
    name,
    opts.geometry || "textbox",
    x,
    y,
    w,
    h,
    opts.fill || "none",
    opts.lineFill || "none",
    opts.lineWidth || 0,
    opts.radius,
  );
  box.text = text;
  box.text.style = {
    fontSize: opts.size || 22,
    typeface: opts.font || FONT,
    color: opts.color || C.ink,
    bold: opts.bold || false,
    alignment: opts.align || "left",
    verticalAlignment: opts.valign || "top",
    autoFit: opts.autoFit || "shrinkText",
    wrap: "square",
    insets: opts.insets || { top: 6, right: 8, bottom: 6, left: 8 },
  };
  return box;
}

function addHeader(slide, num, title, kicker = "CAMPUSMATCH") {
  addText(slide, `kicker-${num}`, kicker, 52, 31, 340, 22, { size: 12, bold: true, color: C.blue, insets: { top: 0, right: 0, bottom: 0, left: 0 } });
  addText(slide, `title-${num}`, title, 52, 58, 1176, 54, { size: 34, bold: true, color: C.ink, autoFit: "none", insets: { top: 0, right: 0, bottom: 0, left: 0 } });
  addShape(slide, `header-line-${num}`, "straightConnector1", 52, 128, 1176, 0, "none", C.line, 1);
}

function addFooter(slide, num, label = "复杂任务多 Agent 自主协同｜初赛方案") {
  addText(slide, `footer-${num}`, label, 52, 680, 900, 18, { size: 10, color: C.faint, insets: { top: 0, right: 0, bottom: 0, left: 0 } });
  addText(slide, `page-${num}`, String(num).padStart(2, "0"), 1170, 677, 58, 18, { size: 11, color: C.faint, bold: true, align: "right", insets: { top: 0, right: 0, bottom: 0, left: 0 } });
}

function addPill(slide, name, text, x, y, w, fill, color, size = 15) {
  return addText(slide, name, text, x, y, w, 34, {
    geometry: "roundRect", fill, lineFill: fill, lineWidth: 1, radius: "rounded-xl",
    size, bold: true, color, align: "center", valign: "middle",
    insets: { top: 4, right: 7, bottom: 4, left: 7 },
  });
}

function addPanel(slide, name, x, y, w, h, fill = C.panel, lineFill = C.line) {
  return addShape(slide, name, "roundRect", x, y, w, h, fill, lineFill, 1, "rounded-xl");
}

function addStep(slide, name, n, title, sub, x, y, w, h, accent = C.blue, fill = C.pale) {
  addPanel(slide, `${name}-panel`, x, y, w, h, fill, fill);
  addText(slide, `${name}-num`, String(n), x + 14, y + 13, 34, 34, {
    geometry: "ellipse", fill: accent, lineFill: accent, lineWidth: 0, size: 15,
    bold: true, color: "#FFFFFF", align: "center", valign: "middle",
    insets: { top: 5, right: 4, bottom: 4, left: 4 },
  });
  addText(slide, `${name}-title`, title, x + 58, y + 12, w - 72, 30, { size: 18, bold: true, color: C.ink, valign: "middle" });
  addText(slide, `${name}-sub`, sub, x + 16, y + 55, w - 32, h - 68, { size: 14, color: C.muted, insets: { top: 0, right: 0, bottom: 0, left: 0 } });
}

function setNotes(slide, text, sources = []) {
  const block = sources.length ? `\n\n[Sources]\n${sources.map((s) => `- ${s}`).join("\n")}\n[/Sources]` : "";
  slide.speakerNotes.textFrame.setText(text + block);
  slide.speakerNotes.setVisible(true);
}

async function readImageBlob(imagePath) {
  const bytes = await fs.readFile(imagePath);
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
}

async function build() {
  await fs.mkdir(TMP_DIR, { recursive: true });
  const deck = Presentation.create({ slideSize: { width: W, height: H } });

  // 01 cover
  {
    const s = deck.slides.add();
    s.background.fill = C.bg;
    const heroBytes = await readImageBlob(HERO);
    s.images.add({
      blob: heroBytes,
      contentType: "image/png",
      alt: "University student and career counselor reviewing evidence-linked career materials",
      fit: "cover",
      position: { left: 500, top: 155, width: 780, height: 438 },
    });
    addShape(s, "cover-overlay", "rect", 510, 0, 150, 720, { color: "#FFFFFF", transparency: 30 }, "none", 0);
    addText(s, "cover-kicker", "AGENT INFRA · 初赛方案", 60, 66, 420, 26, { size: 14, bold: true, color: C.blue, insets: { top: 0, right: 0, bottom: 0, left: 0 } });
    addText(s, "cover-title", "CampusMatch", 60, 158, 500, 90, { size: 54, bold: true, color: C.ink, insets: { top: 0, right: 0, bottom: 0, left: 0 } });
    addText(s, "cover-cn", "高校可信求职协同基座", 60, 257, 470, 58, { size: 28, bold: true, color: C.navy, insets: { top: 0, right: 0, bottom: 0, left: 0 } });
    addText(s, "cover-thesis", "让每项匹配和建议，都能回到证据。", 60, 346, 450, 74, { size: 24, color: C.muted, insets: { top: 0, right: 0, bottom: 0, left: 0 } });
    addPill(s, "cover-pill1", "多 Agent 协同", 60, 455, 144, C.pale, C.blue, 14);
    addPill(s, "cover-pill2", "全链路审计", 216, 455, 132, C.greenPale, C.green, 14);
    addPill(s, "cover-pill3", "人工可接管", 360, 455, 132, C.violetPale, C.violet, 14);
    addText(s, "cover-foot", "面向高校就业中心与在校大学生", 60, 642, 430, 24, { size: 13, color: C.faint, insets: { top: 0, right: 0, bottom: 0, left: 0 } });
    setNotes(s, "CampusMatch 不是替学生包装经历的聊天机器人，而是一套面向高校就业服务的多 Agent 基础设施。它连接学生材料、岗位要求、匹配理由、辅导建议和审计记录，让每项结论都能回到证据。", ["Cover visual generated with OpenAI image generation for this deck; no external asset URL."]);
  }

  // 02 context
  {
    const s = deck.slides.add(); s.background.fill = C.bg; addHeader(s, 2, "高校需要“精准服务”，但个性化辅导难以规模化");
    addPanel(s, "scale-panel", 52, 166, 350, 440, C.navy, C.navy);
    addText(s, "scale-label", "2026 届普通高校毕业生", 82, 205, 290, 32, { size: 17, color: "#D9E9FF", bold: true, align: "center" });
    addText(s, "scale-number", "1,270", 72, 250, 310, 120, { size: 76, color: "#FFFFFF", bold: true, align: "center", valign: "middle" });
    addText(s, "scale-unit", "万人 · 预计规模", 92, 363, 270, 45, { size: 22, color: "#FFFFFF", bold: true, align: "center" });
    addShape(s, "scale-rule", "straightConnector1", 98, 438, 258, 0, "none", "#5F83AD", 1);
    addText(s, "scale-note", "规模扩大之外，政策要求持续强调\n专业化、精准化就业服务", 82, 463, 290, 86, { size: 18, color: "#D9E9FF", align: "center", valign: "middle" });
    const items = [
      ["材料非结构化", "简历、课程、项目、证书格式各异"],
      ["岗位快速变化", "JD 模糊、要求冲突、风险条件混杂"],
      ["辅导高并发", "老师难以逐项核对证据并持续跟进"],
    ];
    items.forEach((it, i) => {
      const y = 170 + i * 143;
      addText(s, `ctx-num-${i}`, `0${i + 1}`, 455, y + 7, 42, 30, { size: 16, bold: true, color: C.blue, insets: { top: 0, right: 0, bottom: 0, left: 0 } });
      addText(s, `ctx-title-${i}`, it[0], 512, y, 560, 42, { size: 24, bold: true, color: C.ink, insets: { top: 0, right: 0, bottom: 0, left: 0 } });
      addText(s, `ctx-sub-${i}`, it[1], 512, y + 50, 630, 48, { size: 17, color: C.muted, insets: { top: 0, right: 0, bottom: 0, left: 0 } });
      if (i < 2) addShape(s, `ctx-line-${i}`, "straightConnector1", 455, y + 117, 720, 0, "none", C.line, 1);
    });
    addPill(s, "source-pill", "真实场景：高校就业服务中心", 455, 585, 280, C.pale, C.blue, 14);
    addText(s, "source-hint", "资料来源见演讲者备注", 950, 591, 226, 22, { size: 11, color: C.faint, align: "right", insets: { top: 0, right: 0, bottom: 0, left: 0 } });
    addFooter(s, 2);
    setNotes(s, "场景不是虚构的。高校就业中心需要在短时间内处理大量学生材料和岗位，同时还要提供个性化服务。问题不是缺一个聊天框，而是缺一套可复核、可协作、可规模化的任务系统。", ["https://www.moe.gov.cn/jyb_xwfb/s5147/202606/t20260615_1440719.html", "https://hudong.moe.gov.cn/jyb_xxgk/moe_1777/moe_1779/202604/t20260403_1432954.html"]);
  }

  // 03 problem framing
  {
    const s = deck.slides.add(); s.background.fill = C.bg; addHeader(s, 3, "现有工具把三种不同问题混成一个黑盒分数");
    const probs = [
      ["A", "简历没写出来", "材料缺证", C.pale, C.blue],
      ["B", "学生确实不会", "能力差距", C.amberPale, C.amber],
      ["C", "岗位要求不合理", "政策风险", C.redPale, C.red],
    ];
    probs.forEach((p, i) => {
      const x = 52 + i * 303;
      addPanel(s, `prob-${i}`, x, 176, 270, 170, p[3], p[3]);
      addText(s, `prob-letter-${i}`, p[0], x + 18, 196, 45, 45, { geometry: "ellipse", fill: p[4], lineFill: p[4], size: 18, bold: true, color: "#FFFFFF", align: "center", valign: "middle" });
      addText(s, `prob-title-${i}`, p[1], x + 72, 194, 175, 48, { size: 21, bold: true });
      addText(s, `prob-sub-${i}`, p[2], x + 20, 273, 225, 38, { size: 17, color: p[4], bold: true, align: "center", valign: "middle" });
      if (i < 2) addText(s, `prob-plus-${i}`, "+", x + 272, 230, 31, 40, { size: 28, color: C.faint, bold: true, align: "center" });
    });
    addText(s, "prob-arrow", "→", 955, 225, 64, 55, { size: 36, bold: true, color: C.faint, align: "center" });
    addText(s, "blackbox", "72", 1033, 176, 160, 170, { geometry: "roundRect", fill: C.ink, lineFill: C.ink, radius: "rounded-xl", size: 58, bold: true, color: "#FFFFFF", align: "center", valign: "middle" });
    addText(s, "blackbox-label", "不可解释的总分", 1038, 306, 150, 28, { size: 13, color: "#D0D5DD", bold: true, align: "center" });
    addPanel(s, "principle", 52, 395, 1140, 204, "#FAFAFB", C.line);
    addText(s, "principle-big", "“没有证据” ≠ “没有能力”", 83, 432, 520, 60, { size: 31, bold: true, color: C.navy, valign: "middle" });
    addShape(s, "principle-divider", "straightConnector1", 640, 425, 0, 118, "none", C.line, 1);
    addText(s, "principle-small", "风险条件不能进入评分\n匹配结论必须逐项说明\n系统不能替企业作录用决定", 685, 423, 450, 132, { size: 21, color: C.ink, bold: true, valign: "middle" });
    addFooter(s, 3);
    setNotes(s, "一个黑盒分数无法区分缺证、能力差距和岗位风险，也无法告诉就业老师该如何介入。这正是我们选择证据链作为基础设施核心的原因。");
  }

  // 04 evidence chain thesis
  {
    const s = deck.slides.add(); s.background.fill = C.bg; addHeader(s, 4, "CampusMatch 把求职建议变成可回放的证据链");
    const chain = [
      ["01", "原始材料", "只读 + 哈希"], ["02", "Markdown", "人机共览"], ["03", "能力证据", "原文锚点"], ["04", "岗位要求", "分类 + 风险"],
      ["05", "匹配矩阵", "逐项状态"], ["06", "求职辅导", "只用已证实经历"], ["07", "Audit", "阻断 / 升级"], ["08", "人工批准", "导出与留痕"],
    ];
    chain.forEach((it, i) => {
      const x = 52 + i * 146;
      const blue = i < 6 ? C.blue : (i === 6 ? C.red : C.green);
      const fill = i < 6 ? C.pale : (i === 6 ? C.redPale : C.greenPale);
      addText(s, `chain-num-${i}`, it[0], x, 198, 116, 28, { size: 12, bold: true, color: blue, align: "center", insets: { top: 0, right: 0, bottom: 0, left: 0 } });
      addText(s, `chain-card-${i}`, `${it[1]}\n${it[2]}`, x, 233, 116, 126, { geometry: "roundRect", fill, lineFill: fill, radius: "rounded-xl", size: 17, bold: true, color: C.ink, align: "center", valign: "middle" });
      if (i < chain.length - 1) addText(s, `chain-arrow-${i}`, "→", x + 117, 271, 29, 35, { size: 20, color: C.faint, align: "center", valign: "middle" });
    });
    addShape(s, "chain-rule", "straightConnector1", 52, 402, 1140, 0, "none", C.line, 1);
    const keys = [
      ["可追溯", "每条结论都有 evidence_id"],
      ["可解释", "分数与置信度分开展示"],
      ["可审批", "风险动作必须人确认"],
      ["可复用", "流程封装为 Skills 与 Schema"],
    ];
    keys.forEach((k, i) => {
      const x = 52 + i * 290;
      addText(s, `key-title-${i}`, k[0], x, 445, 250, 40, { size: 25, bold: true, color: C.navy, align: "center" });
      addText(s, `key-sub-${i}`, k[1], x, 492, 250, 55, { size: 15, color: C.muted, align: "center" });
    });
    addPill(s, "chain-thesis", "关键基础设施：可验证的证据状态，而不是更长的提示词", 347, 580, 585, C.navy, "#FFFFFF", 16);
    addFooter(s, 4);
    setNotes(s, "系统从原始材料开始，保留哈希和引用；所有结构化结论、匹配与辅导建议都带着证据走到审计与人工批准。这样每一步都可回放、可质疑、可重做。");
  }

  // 05 end-to-end state machine
  {
    const s = deck.slides.add(); s.background.fill = C.bg; addHeader(s, 5, "一条完整任务链覆盖输入、执行、验证和沉淀");
    const stages = ["授权\n目标", "文档\n规范化", "学生\n画像", "岗位\n规范化", "证据\n匹配", "求职\n辅导", "审计\n审批", "报告\n沉淀"];
    stages.forEach((t, i) => {
      const x = 52 + i * 146;
      const fill = i === 6 ? C.redPale : (i === 7 ? C.greenPale : C.pale);
      const color = i === 6 ? C.red : (i === 7 ? C.green : C.blue);
      addText(s, `stage-${i}`, t, x, 174, 116, 100, { geometry: "roundRect", fill, lineFill: fill, radius: "rounded-xl", size: 18, bold: true, color, align: "center", valign: "middle" });
      if (i < stages.length - 1) addText(s, `stage-arrow-${i}`, "→", x + 117, 204, 29, 36, { size: 20, color: C.faint, align: "center", valign: "middle" });
    });
    addText(s, "state-label", "主状态机", 52, 300, 100, 24, { size: 13, bold: true, color: C.faint, insets: { top: 0, right: 0, bottom: 0, left: 0 } });
    addText(s, "state-code", "RECEIVED → CONSENTED → PARSED → PROFILE_GROUNDED → JOBS_NORMALIZED → MATCHED → COACHED → AUDITED → APPROVAL_PENDING → EXPORTED", 52, 330, 1140, 72, { geometry: "roundRect", fill: C.ink, lineFill: C.ink, radius: "rounded-xl", size: 16, color: "#E7EEF7", bold: true, align: "center", valign: "middle" });
    addText(s, "abnormal-label", "异常分支", 52, 438, 100, 24, { size: 13, bold: true, color: C.faint, insets: { top: 0, right: 0, bottom: 0, left: 0 } });
    const bad = [
      ["NEEDS_INPUT", "缺材料"], ["RETRYING", "工具失败"], ["BLOCKED", "无证据事实"], ["ESCALATED", "风险条件"], ["DEGRADED", "服务降级"],
    ];
    bad.forEach((b, i) => {
      const x = 52 + i * 228;
      addText(s, `bad-${i}`, `${b[0]}\n${b[1]}`, x, 475, 204, 78, { geometry: "roundRect", fill: i === 2 || i === 3 ? C.redPale : C.panel, lineFill: i === 2 || i === 3 ? "#F3B7B7" : C.line, lineWidth: 1, radius: "rounded-xl", size: 15, bold: true, color: i === 2 || i === 3 ? C.red : C.ink, align: "center", valign: "middle" });
    });
    addText(s, "human-takeover", "任意异常均可转人工；导出永远需要审批。", 52, 584, 1140, 38, { size: 22, bold: true, color: C.navy, align: "center" });
    addFooter(s, 5);
    setNotes(s, "任务不是一次问答，而是一条可恢复状态机。每个 Agent 都读写标准任务信封；工具失败会重试，缺材料会向用户提问，高风险条件和无证据事实会进入阻断或人工升级。");
  }

  // 06 AgentTeams architecture
  {
    const s = deck.slides.add(); s.background.fill = C.bg; addHeader(s, 6, "AgentTeams 让六类 Agent 透明协作");
    addPanel(s, "human-panel", 52, 195, 170, 270, "#FAFAFB", C.line);
    addText(s, "human-title", "人类参与者", 72, 218, 130, 32, { size: 20, bold: true, align: "center" });
    addText(s, "human-body", "学生\n就业老师\n评审者", 72, 273, 130, 120, { size: 20, color: C.muted, bold: true, align: "center", valign: "middle" });
    addPill(s, "human-approve", "观察 · 纠正 · 批准", 67, 407, 140, C.greenPale, C.green, 12);
    addText(s, "h2m-arrow", "↔", 230, 290, 50, 45, { size: 27, color: C.faint, bold: true, align: "center" });
    addPanel(s, "manager-panel", 287, 187, 260, 286, C.navy, C.navy);
    addText(s, "manager-label", "MANAGER", 317, 217, 200, 26, { size: 13, bold: true, color: "#BBD4F3", align: "center" });
    addText(s, "manager-title", "Career Navigator", 307, 259, 220, 52, { size: 25, bold: true, color: "#FFFFFF", align: "center", valign: "middle" });
    addText(s, "manager-body", "目标拆解\n状态传递\n失败重试\n结果汇总", 332, 333, 170, 108, { size: 18, color: "#E1ECFA", bold: true, align: "center", valign: "middle" });
    addText(s, "m2w-arrow", "→", 552, 293, 50, 45, { size: 27, color: C.faint, bold: true, align: "center" });
    const workers = [
      ["Profile", "画像 + 证据", C.pale, C.blue], ["Job", "JD 分类 + 风险", C.pale, C.blue], ["Match", "逐项匹配", C.violetPale, C.violet],
      ["Coach", "辅导 + 面试", C.amberPale, C.amber], ["Audit", "PASS / BLOCK", C.redPale, C.red],
    ];
    workers.forEach((w, i) => {
      const col = i % 3, row = Math.floor(i / 3);
      const x = 610 + col * 198, y = 177 + row * 145;
      addText(s, `worker-${i}`, `${w[0]} Agent\n${w[1]}`, x, y, 176, 112, { geometry: "roundRect", fill: w[2], lineFill: w[2], radius: "rounded-xl", size: 18, bold: true, color: w[3], align: "center", valign: "middle" });
    });
    addText(s, "worker-note", "每个 Worker 只负责单一能力，并提交结构化输出", 610, 479, 572, 36, { size: 16, color: C.muted, align: "center" });
    addPanel(s, "infra-strip", 52, 554, 1130, 82, C.panel, C.line);
    const infra = ["Skills", "MCP / 工具", "共享文件", "Trace / 日志", "Human-in-the-loop"];
    infra.forEach((t, i) => addText(s, `infra-${i}`, t, 79 + i * 216, 576, 180, 38, { size: 16, bold: true, color: i === 4 ? C.green : C.ink, align: "center", valign: "middle" }));
    addFooter(s, 6);
    setNotes(s, "Manager 只做目标、编排和汇总，五个 Worker 各自负责单一能力。大文件通过引用共享，不在对话中重复复制；Worker 不持有真实凭据，外部调用经网关治理。人可以进入协作空间观察、纠正和批准。", ["https://github.com/agentscope-ai/AgentTeams", "https://hiclaw.io/"]);
  }

  // 07 boundaries
  {
    const s = deck.slides.add(); s.background.fill = C.bg; addHeader(s, 7, "每个 Agent 都有明确的自主边界");
    const x0 = 52, y0 = 164;
    const cols = [180, 345, 555];
    const heads = ["Agent", "主要输出", "不可越过的边界"];
    let acc = x0;
    heads.forEach((h, i) => { addText(s, `th-${i}`, h, acc, y0, cols[i], 54, { geometry: "rect", fill: C.navy, lineFill: "#FFFFFF", lineWidth: 1, size: 18, bold: true, color: "#FFFFFF", align: i === 0 ? "center" : "left", valign: "middle" }); acc += cols[i]; });
    const rows = [
      ["Profile", "学生画像 + 证据", "不推断无证据能力"],
      ["Job", "规范化要求 + 风险", "风险条件不计分"],
      ["Match", "逐项状态 + 置信度", "不作录用决定"],
      ["Coach", "建议 + 模拟面试", "不虚构经历"],
      ["Audit", "PASS / BLOCK / ESCALATE", "不自行创造证据"],
    ];
    rows.forEach((r, ri) => {
      let x = x0; const y = y0 + 54 + ri * 74; const fill = ri % 2 === 0 ? "#FAFAFB" : "#FFFFFF";
      r.forEach((v, ci) => {
        const color = ci === 0 ? C.blue : (ci === 2 ? C.red : C.ink);
        addText(s, `td-${ri}-${ci}`, v, x, y, cols[ci], 74, { geometry: "rect", fill, lineFill: C.line, lineWidth: 1, size: ci === 2 ? 17 : 18, bold: ci !== 1, color, align: ci === 0 ? "center" : "left", valign: "middle", insets: { top: 8, right: 15, bottom: 8, left: 15 } });
        x += cols[ci];
      });
    });
    addPill(s, "boundary-pill", "Manager 可重试流程，但不能覆盖 Worker 的安全拒绝", 407, 605, 470, C.redPale, C.red, 15);
    addFooter(s, 7);
    setNotes(s, "把安全规则写在角色边界里，而不是只依赖一段总提示词。特别是 Audit 的 BLOCK 不能被 Manager 静默绕过；如果要继续，只能补证、删改或进入人工审批。");
  }

  // 08 evidence object
  {
    const s = deck.slides.add(); s.background.fill = C.bg;
    const panels = [
      ["01 原始文件", "只读保留\nSHA-256 哈希\n访问授权", C.panel, C.ink],
      ["02 行号化 Markdown", "学生与 AI 共览\n段落 / 区块锚点\n可人工纠正", C.pale, C.blue],
      ["03 证据 JSON", "claim + evidence_id\nsource_quote\nstrength + confirmed", C.violetPale, C.violet],
    ];
    panels.forEach((p, i) => {
      const x = 52 + i * 390;
      addPanel(s, `ev-panel-${i}`, x, 164, 340, 218, p[2], p[2]);
      addText(s, `ev-title-${i}`, p[0], x + 22, 187, 296, 40, { size: 21, bold: true, color: p[3] });
      addText(s, `ev-body-${i}`, p[1], x + 22, 248, 296, 100, { size: 18, color: C.ink, bold: true, valign: "middle" });
      if (i < 2) addText(s, `ev-arrow-${i}`, "→", x + 345, 252, 40, 42, { size: 25, color: C.faint, bold: true, align: "center" });
    });
    addText(s, "ev-example-label", "证据对象（合成示例）", 52, 414, 220, 28, { size: 14, bold: true, color: C.faint, insets: { top: 0, right: 0, bottom: 0, left: 0 } });
    addText(s, "ev-code", "claim: 具备办公与信息处理经验\nevidence: E-S001-003\nsource: “我使用 Excel 维护活动报名名单，核对参与者信息。”\nstrength: direct    confirmed: true", 52, 451, 745, 170, { geometry: "roundRect", fill: C.ink, lineFill: C.ink, radius: "rounded-xl", size: 18, color: "#E8EEF6", font: "Consolas", insets: { top: 18, right: 22, bottom: 18, left: 22 } });
    addPanel(s, "ev-rule", 835, 451, 357, 170, C.greenPale, C.greenPale);
    addText(s, "ev-rule-title", "可导出条件", 863, 472, 300, 34, { size: 20, bold: true, color: C.green, align: "center" });
    addText(s, "ev-rule-body", "重要结论有 evidence_id\n原文可定位\n确认状态明确\nAudit 检查通过", 871, 518, 284, 83, { size: 17, color: C.ink, bold: true, align: "center", valign: "middle" });
    addShape(s, "ev-header-band", "rect", 0, 0, 1280, 145, C.bg, C.bg, 0);
    addText(s, "kicker-8", "CAMPUSMATCH", 52, 31, 340, 22, { size: 12, bold: true, color: C.blue, autoFit: "none", insets: { top: 0, right: 0, bottom: 0, left: 0 } });
    addText(s, "title-8", "三层证据链，让每项能力回到原文", 52, 58, 1176, 54, { geometry: "rect", size: 32, bold: true, color: C.ink, autoFit: "none", insets: { top: 0, right: 0, bottom: 0, left: 0 } });
    addShape(s, "header-line-8", "straightConnector1", 52, 128, 1176, 0, "none", C.line, 1);
    addFooter(s, 8);
    setNotes(s, "Markdown 便于学生和 AI 共同查看，但原始文件仍只读保留并计算哈希。每项结构化能力都关联区块、原文和确认状态；任何结论都能追到原文，而不是只追到模型回答。");
  }

  // 09 match visualization
  {
    const s = deck.slides.add(); s.background.fill = C.bg; addHeader(s, 9, "匹配度与证据覆盖度分开展示");
    // left: ring
    addPanel(s, "score-panel", 52, 160, 285, 458, "#FAFAFB", C.line);
    addText(s, "score-title", "岗位匹配度", 78, 181, 233, 35, { size: 19, bold: true, align: "center" });
    addShape(s, "score-outer", "ellipse", 96, 238, 196, 196, C.blue, C.blue, 0);
    addShape(s, "score-inner", "ellipse", 129, 271, 130, 130, "#FFFFFF", "#FFFFFF", 0);
    addText(s, "score-num", "77", 137, 296, 114, 60, { size: 44, bold: true, color: C.navy, align: "center", valign: "middle" });
    addText(s, "score-unit", "/ 100", 156, 354, 75, 24, { size: 14, bold: true, color: C.faint, align: "center" });
    addText(s, "confidence-label", "证据覆盖度 85%", 78, 469, 233, 28, { size: 16, bold: true, color: C.ink, align: "center" });
    addShape(s, "conf-bg", "roundRect", 86, 513, 217, 13, C.line, C.line, 0, "rounded-xl");
    addShape(s, "conf-fill", "roundRect", 86, 513, 184, 13, C.green, C.green, 0, "rounded-xl");
    addText(s, "score-note", "匹配 ≠ 录用概率", 91, 550, 207, 30, { size: 15, bold: true, color: C.red, align: "center" });
    // middle radar
    addPanel(s, "radar-panel", 360, 160, 405, 458, "#FFFFFF", C.line);
    addText(s, "radar-title", "五维证据画像", 389, 181, 346, 34, { size: 19, bold: true, align: "center" });
    s.charts.add("radar", {
      position: { left: 386, top: 224, width: 352, height: 322 },
      categories: ["硬技能", "项目深度", "领域经验", "协作沟通", "成长潜力"],
      series: [{ name: "合成候选人", values: [80, 70, 85, 65, 78], line: { style: "solid", fill: C.blue, width: 3 }, fill: "#CFE2FA" }],
      hasLegend: false,
      yAxis: { minimumScale: 0, maximumScale: 100, majorUnit: 20, majorGridlines: { style: "solid", fill: C.line, width: 1 } },
    });
    addText(s, "radar-note", "基于已确认材料", 446, 560, 232, 26, { size: 14, color: C.muted, align: "center" });
    // right matrix
    addPanel(s, "matrix-panel", 788, 160, 404, 458, "#FAFAFB", C.line);
    addText(s, "matrix-title", "要求证据矩阵", 816, 181, 348, 34, { size: 19, bold: true, align: "center" });
    const reqs = [
      ["Excel 信息整理", "符合", C.greenPale, C.green],
      ["基础文档写作", "部分符合", C.amberPale, C.amber],
      ["内容发布经验", "缺少证据", C.panel, C.muted],
      ["女性优先", "风险排除", C.redPale, C.red],
    ];
    reqs.forEach((r, i) => {
      const y = 238 + i * 72;
      addText(s, `req-name-${i}`, r[0], 819, y, 172, 50, { size: 17, bold: true, valign: "middle" });
      addText(s, `req-state-${i}`, r[1], 1007, y + 7, 143, 36, { geometry: "roundRect", fill: r[2], lineFill: r[2], radius: "rounded-xl", size: 14, bold: true, color: r[3], align: "center", valign: "middle" });
      if (i < reqs.length - 1) addShape(s, `req-line-${i}`, "straightConnector1", 819, y + 60, 331, 0, "none", C.line, 1);
    });
    addText(s, "state-legend", "状态：符合 / 部分符合 / 缺证 / 冲突 / 风险排除", 815, 548, 350, 44, { size: 13, color: C.muted, align: "center", valign: "middle" });
    addText(s, "synthetic-note", "合成演示数据，不代表录用概率", 52, 637, 1140, 22, { size: 13, bold: true, color: C.red, align: "center", insets: { top: 0, right: 0, bottom: 0, left: 0 } });
    addFooter(s, 9, "复杂任务多 Agent 自主协同｜合成演示数据");
    setNotes(s, "本页使用当前可执行合成案例：岗位匹配度 77、证据覆盖度 85。逐项状态来自真实 Demo 输出；“女性优先”被标记为 POLICY_EXCLUDED，不参与评分。匹配分不代表录用概率，缺少证据不等于缺少能力。", ["Internal verification: show/19-Demo实机验收记录.md"]);
  }

  // 10 audit gates
  {
    const s = deck.slides.add(); s.background.fill = C.bg; addHeader(s, 10, "Audit Agent 在导出前设置两道门");
    addPanel(s, "pre-audit", 52, 165, 300, 188, C.pale, C.pale);
    addText(s, "pre-num", "01", 74, 185, 50, 28, { size: 14, bold: true, color: C.blue });
    addText(s, "pre-title", "前置审查", 74, 222, 240, 35, { size: 23, bold: true, color: C.navy });
    addText(s, "pre-body", "授权与目标\n最小化收集\nJD 公平条件\n工具权限", 74, 269, 240, 72, { size: 16, color: C.ink, bold: true });
    addText(s, "audit-arrow1", "→", 361, 234, 48, 45, { size: 25, color: C.faint, bold: true, align: "center" });
    addPanel(s, "work-stage", 418, 165, 300, 188, "#FAFAFB", C.line);
    addText(s, "work-num", "02", 440, 185, 50, 28, { size: 14, bold: true, color: C.faint });
    addText(s, "work-title", "Agent 协同执行", 440, 222, 240, 35, { size: 23, bold: true, color: C.ink });
    addText(s, "work-body", "画像 → 解析 → 匹配\n→ 辅导 → 结果汇总", 440, 275, 240, 62, { size: 17, color: C.muted, bold: true, align: "center" });
    addText(s, "audit-arrow2", "→", 727, 234, 48, 45, { size: 25, color: C.faint, bold: true, align: "center" });
    addPanel(s, "post-audit", 784, 165, 408, 188, C.redPale, C.redPale);
    addText(s, "post-num", "03", 806, 185, 50, 28, { size: 14, bold: true, color: C.red });
    addText(s, "post-title", "后置审查 + 人工批准", 806, 222, 350, 35, { size: 23, bold: true, color: C.red });
    addText(s, "post-body", "经历真实性 · 证据覆盖 · 隐私\n内容安全 · Trace 完整性", 806, 277, 350, 62, { size: 16, color: C.ink, bold: true, align: "center" });
    addText(s, "case-label", "演示案例：无证据量化被阻断", 52, 394, 300, 26, { size: 14, bold: true, color: C.faint, insets: { top: 0, right: 0, bottom: 0, left: 0 } });
    addText(s, "bad-claim", "Coach 输出\n“将处理效率提升 30%”", 52, 435, 292, 112, { geometry: "roundRect", fill: C.amberPale, lineFill: C.amberPale, radius: "rounded-xl", size: 19, bold: true, color: C.amber, align: "center", valign: "middle" });
    addText(s, "case-arrow1", "→", 351, 467, 46, 40, { size: 24, color: C.faint, bold: true, align: "center" });
    addText(s, "blocked", "BLOCK\n材料中没有证据", 406, 435, 246, 112, { geometry: "roundRect", fill: C.red, lineFill: C.red, radius: "rounded-xl", size: 20, bold: true, color: "#FFFFFF", align: "center", valign: "middle" });
    addText(s, "case-arrow2", "→", 659, 467, 46, 40, { size: 24, color: C.faint, bold: true, align: "center" });
    addText(s, "fix", "删除数字 / 补充证据\n用户确认", 714, 435, 246, 112, { geometry: "roundRect", fill: C.pale, lineFill: C.pale, radius: "rounded-xl", size: 19, bold: true, color: C.blue, align: "center", valign: "middle" });
    addText(s, "case-arrow3", "→", 967, 467, 46, 40, { size: 24, color: C.faint, bold: true, align: "center" });
    addText(s, "passed", "PASS\n允许导出", 1022, 435, 170, 112, { geometry: "roundRect", fill: C.green, lineFill: C.green, radius: "rounded-xl", size: 20, bold: true, color: "#FFFFFF", align: "center", valign: "middle" });
    addPill(s, "audit-bottom", "安全规则：隐私最小化 · 禁止违法内容 · 不基于敏感属性排序 · 高风险信号转人工", 167, 584, 910, C.panel, C.ink, 14);
    addText(s, "law-hint", "法规来源见备注", 1015, 624, 177, 20, { size: 10, color: C.faint, align: "right" });
    addFooter(s, 10);
    setNotes(s, "Audit 不只是最后一遍敏感词过滤。前置审查处理授权、隐私和岗位公平；后置审查处理事实、证据、内容安全和 Trace。演示中，Coach 写出材料没有支撑的“提升 30%”，系统必须 BLOCK，直到删除或补证并由用户确认。", ["https://www.npc.gov.cn/WZWSREL25wYy9jMi9jMzA4MzQvMjAyMTA4L3QyMDIxMDgyMF8zMTMwODguaHRtbD9yZWY9aW1i", "https://app.www.gov.cn/govdata/gov/202408/29/518774/article.html"]);
  }

  // 11 skills
  {
    const s = deck.slides.add(); s.background.fill = C.bg; addHeader(s, 11, "Skills 把专家流程沉淀为可复用能力");
    const groups = [
      ["材料", "document_to_markdown\nevidence_extractor\nprivacy_minimizer", C.pale, C.blue],
      ["岗位", "jd_normalizer\nfairness_scanner\nrequirement_classifier", C.violetPale, C.violet],
      ["决策", "evidence_matcher\nscore_explainer\ngap_plan_builder", C.amberPale, C.amber],
      ["治理", "claim_auditor\nreport_exporter\nsls_trace_query", C.greenPale, C.green],
    ];
    groups.forEach((g, i) => {
      const x = 52 + (i % 2) * 578, y = 166 + Math.floor(i / 2) * 222;
      addPanel(s, `skill-group-${i}`, x, y, 552, 190, g[2], g[2]);
      addText(s, `skill-label-${i}`, g[0], x + 22, y + 20, 82, 38, { geometry: "roundRect", fill: g[3], lineFill: g[3], radius: "rounded-xl", size: 17, bold: true, color: "#FFFFFF", align: "center", valign: "middle" });
      addText(s, `skill-list-${i}`, g[1], x + 126, y + 25, 390, 135, { size: 18, font: "Consolas", color: C.ink, bold: true, valign: "middle" });
    });
    addShape(s, "skills-rule", "straightConnector1", 52, 612, 1140, 0, "none", C.line, 1);
    addText(s, "skills-thesis", "Skill 定义输入、输出、失败处理与安全边界；MCP / 等价契约连接文件、岗位、知识库和日志。", 80, 626, 1084, 35, { size: 17, color: C.navy, bold: true, align: "center" });
    addFooter(s, 11);
    setNotes(s, "Skill 不是工具名清单，而是可复用的专家流程：定义输入、输出、失败处理和安全边界。MCP 或等价契约负责连接文件、岗位、知识库和日志。日志侧可接入阿里云 SLS 查询 Skill，便于复赛展示可观测性。", ["https://skills.aliyun.com/skills", "https://skills.aliyun.com/skills/alibabacloud-sls-query", "https://opentelemetry.io/docs/specs/semconv/"]);
  }

  // 12 demo
  {
    const s = deck.slides.add(); s.background.fill = C.bg; addHeader(s, 12, "固定异常分支，验证系统真正可控");
    const flow = [
      ["1", "合成简历 + JD"], ["2", "证据画像"], ["3", "匹配可视化"], ["4", "Coach 生成建议"], ["5", "Audit 阻断"], ["6", "人工修复批准"], ["7", "报告 + Trace"],
    ];
    flow.forEach((f, i) => {
      const x = 52 + i * 164;
      const isBlock = i === 4;
      const isPass = i >= 5;
      const fill = isBlock ? C.redPale : (isPass ? C.greenPale : C.pale);
      const color = isBlock ? C.red : (isPass ? C.green : C.blue);
      addText(s, `demo-n-${i}`, f[0], x + 48, 174, 40, 40, { geometry: "ellipse", fill: color, lineFill: color, size: 16, bold: true, color: "#FFFFFF", align: "center", valign: "middle" });
      addText(s, `demo-box-${i}`, f[1], x, 234, 136, 88, { geometry: "roundRect", fill, lineFill: fill, radius: "rounded-xl", size: 16, bold: true, color, align: "center", valign: "middle" });
      if (i < flow.length - 1) addText(s, `demo-arrow-${i}`, "→", x + 137, 258, 27, 32, { size: 18, color: C.faint, bold: true, align: "center" });
    });
    addPanel(s, "demo-exception", 52, 364, 1140, 151, "#FAFAFB", C.line);
    addText(s, "demo-ex-title", "固定异常：建议中出现材料未支持的“提升 30%”", 81, 386, 540, 42, { size: 22, bold: true, color: C.red });
    addText(s, "demo-ex-body", "Audit → BLOCK → 回传 evidence_gap → Coach 删除无证据数字 → 用户确认 → PASS", 81, 445, 1040, 40, { size: 18, bold: true, color: C.ink, align: "center" });
    addText(s, "offline", "浏览器确定性链路", 110, 556, 255, 62, { geometry: "roundRect", fill: C.navy, lineFill: C.navy, radius: "rounded-xl", size: 19, bold: true, color: "#FFFFFF", align: "center", valign: "middle" });
    addText(s, "offline-desc", "50 项测试，77 / 85 可复现", 381, 566, 235, 40, { size: 16, color: C.muted, bold: true, valign: "middle" });
    addText(s, "online", "HiClaw Team 实机链路", 680, 556, 272, 62, { geometry: "roundRect", fill: C.pale, lineFill: C.blue, lineWidth: 2, radius: "rounded-xl", size: 19, bold: true, color: C.blue, align: "center", valign: "middle" });
    addText(s, "online-desc", "6 Worker，5 阶段，状态 READY", 968, 566, 224, 40, { size: 16, color: C.muted, bold: true, valign: "middle" });
    addFooter(s, 12, "复杂任务多 Agent 自主协同｜本地 MVP 实测");
    setNotes(s, "两条演示路径均已验证：浏览器确定性链路便于非技术评委复现；HiClaw Team 链路由 Career Navigator 委派 Profile、Job、Match、Coach、Audit 五阶段执行。Audit 在未人工批准时返回 BLOCK + APPROVAL_REQUIRED，证明人工门没有被绕过。", ["Internal verification: demo/README.md", "Internal verification: show/19-Demo实机验收记录.md"]);
  }

  // 13 verified local MVP evidence
  {
    const s = deck.slides.add(); s.background.fill = C.bg; addHeader(s, 13, "固定数据 + 实机链路：当前可复现证据");
    addPill(s, "target-disclaimer", "本地 MVP 实测｜2026-08-14", 52, 151, 270, C.redPale, C.red, 14);
    const metrics = [
      ["50", "自动化测试全部通过", C.blue],
      ["0", "浏览器控制台错误", C.red],
      ["0", "歧视条件进入评分", C.red],
      ["6 / 6", "Worker MCP 健康", C.green],
      ["5 / 5", "Team 专业阶段完成", C.green],
      ["READY", "最终业务状态", C.blue],
    ];
    metrics.forEach((m, i) => {
      const x = 52 + (i % 3) * 386, y = 208 + Math.floor(i / 3) * 190;
      addPanel(s, `metric-${i}`, x, y, 360, 156, "#FAFAFB", C.line);
      addText(s, `metric-num-${i}`, m[0], x + 22, y + 20, 316, 67, { size: 40, bold: true, color: m[2], align: "center", valign: "middle" });
      addText(s, `metric-label-${i}`, m[1], x + 24, y + 96, 312, 37, { size: 17, bold: true, color: C.ink, align: "center", valign: "middle" });
    });
    addText(s, "metric-method", "浏览器桌面/移动端 + API + MCP + Worker Skills + Team Room + 共享结果", 52, 610, 1140, 40, { size: 17, bold: true, color: C.navy, align: "center" });
    addFooter(s, 13, "复杂任务多 Agent 自主协同｜实机记录见 show/19");
    setNotes(s, "本页只列 2026-08-14 本地实测：50 项自动化测试通过；浏览器控制台 0 错误；风险性别条件 0 次进入评分；六个 Worker MCP 全部健康；真实 Team 的五个专业阶段全部完成；最终业务状态 READY。77/85 是合成案例输出，不代表招聘效果。", ["Internal verification: show/19-Demo实机验收记录.md"]);
  }

  // 14 close
  {
    const s = deck.slides.add(); s.background.fill = C.bg; addHeader(s, 14, "从高校场景出发，开放一套可信求职 Agent Infra");
    const outs = [
      ["Identity", "六类 Agent 的职责、输入、输出与边界"],
      ["Skills", "证据抽取、匹配、审计和导出流程"],
      ["Schemas", "任务信封、证据对象、匹配矩阵与 Trace"],
      ["Eval", "合成数据、测试用例、适配器与回放样例"],
    ];
    outs.forEach((o, i) => {
      const x = 52 + i * 290;
      addText(s, `out-num-${i}`, `0${i + 1}`, x, 177, 250, 28, { size: 13, bold: true, color: C.blue, align: "center" });
      addPanel(s, `out-${i}`, x, 217, 250, 190, i === 0 ? C.pale : "#FAFAFB", i === 0 ? C.pale : C.line);
      addText(s, `out-title-${i}`, o[0], x + 20, 246, 210, 45, { size: 24, bold: true, color: C.navy, align: "center" });
      addText(s, `out-body-${i}`, o[1], x + 24, 310, 202, 72, { size: 16, color: C.muted, bold: true, align: "center", valign: "middle" });
    });
    addText(s, "close-statement", "不替学生编造经历，不替企业自动淘汰；\n让每一次匹配都有证据，让每一次自动化都能被人接管。", 128, 466, 1024, 102, { size: 28, bold: true, color: C.ink, align: "center", valign: "middle" });
    addPill(s, "close-scope1", "高校就业中心", 310, 602, 170, C.pale, C.blue, 14);
    addPill(s, "close-scope2", "职业培训", 500, 602, 132, C.violetPale, C.violet, 14);
    addPill(s, "close-scope3", "校招平台", 652, 602, 132, C.greenPale, C.green, 14);
    addPill(s, "close-scope4", "可信求职 Infra", 804, 602, 170, C.navy, "#FFFFFF", 14);
    addFooter(s, 14);
    setNotes(s, "CampusMatch 从高校就业服务这个真实场景出发，开放 Agent Identity、Skills、Schema、合成数据、评测用例、工具适配器和 Trace 示例。它不替学生编造经历，也不替企业自动淘汰，让每次匹配都有证据，让每次自动化都能被人接管。");
  }

  for (const [index, slide] of deck.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    const png = await deck.export({ slide, format: "png", scale: 1 });
    await fs.writeFile(path.join(TMP_DIR, `${stem}.png`), new Uint8Array(await png.arrayBuffer()));
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(path.join(TMP_DIR, `${stem}.layout.json`), await layout.text());
  }
  const montage = await deck.export({ format: "webp", montage: true, scale: 1 });
  await fs.writeFile(path.join(TMP_DIR, "deck-montage.webp"), new Uint8Array(await montage.arrayBuffer()));
  const pptx = await PresentationFile.exportPptx(deck);
  await pptx.save(path.join(OUT_DIR, "CampusMatch-初赛方案.pptx"));
}

build().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
