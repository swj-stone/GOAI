from campusmatch.contracts import DemoRunResult


STATE_LABELS = {
    "MATCH": "符合",
    "PARTIAL": "部分符合",
    "NO_EVIDENCE": "缺少证据",
    "GAP": "待提升",
    "CONFLICT": "信息冲突",
    "POLICY_EXCLUDED": "合规排除",
}


def build_markdown_report(result: DemoRunResult) -> str:
    lines = [
        "# CampusMatch 证据化求职报告",
        "",
        f"- 任务编号：{result.task_id}",
        f"- 证据匹配度：{result.match.match_score:g}",
        f"- 材料覆盖度：{result.match.evidence_coverage:g}%",
        f"- 审计状态：{result.audit.status}",
        "",
        f"> {result.match.disclaimer}",
        "",
        "## 能力与原文证据",
        "",
    ]

    evidence = {item.evidence_id: item for item in result.profile.evidence}
    for competency in result.profile.competencies:
        lines.append(f"### {competency.label}")
        for reference in competency.evidence_refs:
            source = evidence[reference]
            lines.append(
                f"- `{reference}` 第 {source.line_start} 行：{source.quote}"
            )
        lines.append("")

    lines.extend(["## 岗位匹配解释", ""])
    for item in result.match.items:
        label = STATE_LABELS[item.state]
        counted = "参与评分" if item.counted else "不参与评分"
        lines.append(f"- **{item.label}｜{label}｜{counted}**：{item.reason}")

    lines.extend(["", "## 简历与准备建议", ""])
    if result.coaching.resume_suggestions:
        for suggestion in result.coaching.resume_suggestions:
            refs = "、".join(suggestion.evidence_refs)
            lines.append(f"- {suggestion.suggestion}（证据：{refs}）")
    else:
        lines.append("- 当前没有足够证据生成简历表述，请先补充或确认材料。")

    lines.extend(["", "### 学习 / 补证计划", ""])
    for action in result.coaching.learning_plan:
        lines.append(f"- **{action.target}**：{action.action}")

    lines.extend(["", "### 模拟面试题", ""])
    for question in result.coaching.interview_questions:
        lines.append(f"- {question.question}")

    lines.extend(["", "## 审计与执行记录", ""])
    for event in result.trace:
        lines.append(f"- {event.agent}：{event.detail}")

    return "\n".join(lines).rstrip() + "\n"
