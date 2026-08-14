from campusmatch.contracts import (
    CoachingResult,
    InterviewQuestion,
    LearningAction,
    MatchResult,
    Profile,
    ResumeSuggestion,
)


def generate_coaching(
    profile: Profile, match: MatchResult, *, task_id: str
) -> CoachingResult:
    evidence = {item.evidence_id: item for item in profile.evidence}
    if {"E-S001-001", "E-S001-003", "E-S001-004"} <= evidence.keys():
        first = evidence["E-S001-001"]
        excel = evidence["E-S001-003"]
        resume_suggestions = [
            ResumeSuggestion(
                original=first.quote,
                suggestion="协调 5 人完成课程小组汇报：整理提纲、分配任务并完成课堂展示。",
                evidence_refs=[first.evidence_id],
            ),
            ResumeSuggestion(
                original=excel.quote,
                suggestion="使用 Excel 维护活动报名名单，核对参与者信息，并协助完成现场签到。",
                evidence_refs=["E-S001-003", "E-S001-004"],
            ),
        ]
    else:
        resume_suggestions = []
        used_evidence: set[str] = set()
        for item in match.items:
            if not item.evidence_refs:
                continue
            reference = next(
                (ref for ref in item.evidence_refs if ref in evidence and ref not in used_evidence),
                None,
            )
            if reference is None:
                continue
            source = evidence[reference]
            resume_suggestions.append(
                ResumeSuggestion(
                    original=source.quote,
                    suggestion=source.quote.lstrip("- ").strip(),
                    evidence_refs=[reference],
                    needs_confirmation=source.source_type == "self_confirmed",
                )
            )
            used_evidence.add(reference)
            if len(resume_suggestions) == 3:
                break

    missing_items = [
        item
        for item in match.items
        if item.counted and item.state in {"NO_EVIDENCE", "GAP", "PARTIAL"}
    ]
    learning_plan = [
        LearningAction(
            target=item.label,
            action_type="EVIDENCE" if item.state == "PARTIAL" else "LEARN",
            action=(
                f"补充一项能够直接证明“{item.label}”的作品或经历，并由本人确认。"
                if item.state == "PARTIAL"
                else f"完成一项“{item.label}”练习，保留过程和成果作为后续证据。"
            ),
        )
        for item in missing_items[:3]
    ]
    if not learning_plan:
        learning_plan = [
            LearningAction(
                target="证据维护",
                action_type="EVIDENCE",
                action="保存作品、任务说明和本人职责，面试前再次确认表述边界。",
            )
        ]

    interview_questions = [
        InterviewQuestion(
            question=f"请用具体情境说明你在“{item.label}”方面做了什么，结果如何？",
            evidence_refs=[ref for ref in item.evidence_refs if ref in evidence],
        )
        for item in match.items
        if item.counted and item.evidence_refs
    ][:3]
    if not interview_questions:
        interview_questions = [
            InterviewQuestion(
                question="当前材料证据较少：你最近完成过哪些课程、项目、社团或志愿任务？",
                evidence_refs=[],
            )
        ]

    return CoachingResult(
        task_id=task_id,
        resume_suggestions=resume_suggestions,
        learning_plan=learning_plan,
        interview_questions=interview_questions,
    )
