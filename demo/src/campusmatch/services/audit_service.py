import re

from campusmatch.contracts import (
    AuditIssue,
    AuditResult,
    CoachingResult,
    MatchResult,
    Profile,
)


PRIVATE_PATTERN = re.compile(
    r"1[3-9]\d{9}|(?<!\d)\d{17}[\dXx](?!\d)|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
)


def issue(code: str, message: str, action: str) -> AuditIssue:
    return AuditIssue(code=code, message=message, action=action)


def audit_coaching(
    profile: Profile,
    match: MatchResult,
    coaching: CoachingResult,
    *,
    task_id: str,
    consent_granted: bool,
    trace_present: bool,
    human_approved: bool,
) -> AuditResult:
    issues: list[AuditIssue] = []
    evidence = {item.evidence_id: item for item in profile.evidence}

    private_evidence = [
        item.evidence_id
        for item in profile.evidence
        if PRIVATE_PATTERN.search(item.quote)
    ]
    if private_evidence:
        issues.append(
            issue(
                "PRIVACY_IN_SOURCE",
                f"原始证据中包含需脱敏的联系方式或身份信息：{', '.join(private_evidence)}。",
                "请在共享与导出前遮盖敏感字段，并重新确认脱敏后的原文。",
            )
        )

    unsafe_policy_items = [
        item.requirement_id
        for item in match.items
        if item.category == "POLICY_RISK"
        and (item.counted or item.weight != 0 or item.state != "POLICY_EXCLUDED")
    ]
    if unsafe_policy_items:
        issues.append(
            issue(
                "POLICY_RISK_SCORED",
                f"风险条件被错误计入匹配：{', '.join(unsafe_policy_items)}。",
                "从评分中移除风险条件，并交由人工进行公平性核查。",
            )
        )

    if not consent_granted:
        issues.append(
            issue(
                "CONSENT_REQUIRED",
                "用户尚未授权处理和导出求职材料。",
                "请用户确认授权范围后重新审计。",
            )
        )

    for suggestion in coaching.resume_suggestions:
        missing_refs = [ref for ref in suggestion.evidence_refs if ref not in evidence]
        if missing_refs:
            issues.append(
                issue(
                    "EVIDENCE_REF_MISSING",
                    f"建议引用了不存在的证据：{', '.join(missing_refs)}。",
                    "删除无效引用或重新选择真实材料。",
                )
            )
            continue

        sources = " ".join(evidence[ref].quote for ref in suggestion.evidence_refs)
        new_numbers = [
            token
            for token in re.findall(r"\d+(?:\.\d+)?%?", suggestion.suggestion)
            if token not in sources
        ]
        if new_numbers:
            issues.append(
                issue(
                    "UNGROUNDED_NUMERIC_CLAIM",
                    f"建议包含材料未支持的数字：{', '.join(new_numbers)}。",
                    "删除该数字，或补充并确认能够证明该数字的材料。",
                )
            )

        unsupported_markers = ["独立策划", "统筹全流程", "主导大型"]
        if any(
            marker in suggestion.suggestion and marker not in sources
            for marker in unsupported_markers
        ):
            issues.append(
                issue(
                    "UNGROUNDED_FACT_CLAIM",
                    "建议把协助性经历扩大成了独立负责或主导经历。",
                    "恢复材料中的职责边界，或补充并确认新的证明材料。",
                )
            )

        if PRIVATE_PATTERN.search(suggestion.suggestion):
            issues.append(
                issue(
                    "PRIVACY_LEAK",
                    "建议文本中包含不应直接导出的联系方式或身份信息。",
                    "脱敏后重新审计。",
                )
            )

    if not trace_present:
        issues.append(
            issue(
                "TRACE_REQUIRED",
                "缺少可核查的运行记录。",
                "补齐执行 Trace 后重新审计。",
            )
        )

    if not human_approved:
        issues.append(
            issue(
                "APPROVAL_REQUIRED",
                "最终版本尚未获得人工批准。",
                "请用户或就业老师确认最终内容。",
            )
        )

    passed = not issues
    return AuditResult(
        task_id=task_id,
        status="PASS" if passed else "BLOCK",
        export_allowed=passed,
        issues=issues,
    )
