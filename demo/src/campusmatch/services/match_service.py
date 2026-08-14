from campusmatch.contracts import JobProfile, MatchItem, MatchResult, Profile


DIRECT_REASONS = {
    "R-COMMUNICATION": "课堂展示和志愿服务答疑提供了直接证据",
    "R-OFFICE": "使用 Excel 维护报名名单提供了直接证据",
    "R-ACTIVITY": "报名、通知、签到和临时排班经历提供了直接证据",
}

PARTIAL_REASONS = {
    "R-WRITING": "有提纲和展示材料，但缺少正式运营文案证据",
}

NO_EVIDENCE_REASONS = {
    "R-CONTENT": "当前材料没有公众号、平台内容发布或用户反馈整理证据",
}


def calculate_match(
    profile: Profile, job: JobProfile, *, task_id: str
) -> MatchResult:
    competencies = {item.competency_id: item for item in profile.competencies}
    confirmed_evidence = {
        item.evidence_id for item in profile.evidence if item.confirmed_by_user
    }
    items: list[MatchItem] = []

    for requirement in job.requirements:
        if requirement.category == "AMBIGUOUS":
            continue

        if requirement.category == "POLICY_RISK":
            items.append(
                MatchItem(
                    requirement_id=requirement.requirement_id,
                    label=requirement.label,
                    category=requirement.category,
                    weight=0,
                    state="POLICY_EXCLUDED",
                    coefficient=0,
                    evidence_refs=[],
                    reason="与岗位能力无直接关系，不参与匹配并转人工核查",
                    counted=False,
                )
            )
            continue

        competency = next(
            (
                competencies[competency_id]
                for competency_id in requirement.competency_ids
                if competency_id in competencies
            ),
            None,
        )
        evidence_refs = (
            [
                reference
                for reference in competency.evidence_refs
                if reference in confirmed_evidence
            ]
            if competency
            else []
        )

        if not competency or not evidence_refs:
            state = "NO_EVIDENCE"
            coefficient = 0.0
            reason = NO_EVIDENCE_REASONS.get(
                requirement.requirement_id,
                "当前材料没有能够支持这一要求的证据",
            )
        elif competency.evidence_strength == "related":
            state = "PARTIAL"
            coefficient = 0.6
            reason = PARTIAL_REASONS.get(
                requirement.requirement_id,
                "现有材料提供了相关证据，但与岗位要求并非完全对应",
            )
        else:
            state = "MATCH"
            coefficient = 1.0
            reason = DIRECT_REASONS.get(
                requirement.requirement_id,
                "现有材料提供了直接证据",
            )

        items.append(
            MatchItem(
                requirement_id=requirement.requirement_id,
                label=requirement.label,
                category=requirement.category,
                weight=requirement.weight,
                state=state,
                coefficient=coefficient,
                evidence_refs=evidence_refs,
                reason=reason,
                counted=True,
            )
        )

    match_score = sum(
        item.weight * item.coefficient for item in items if item.counted
    )
    evidence_coverage = sum(
        item.weight for item in items if item.counted and item.evidence_refs
    )

    return MatchResult(
        task_id=task_id,
        match_score=round(match_score, 2),
        evidence_coverage=round(evidence_coverage, 2),
        disclaimer="证据匹配度不是录用概率；缺少证据不等于缺少能力。",
        items=items,
    )
