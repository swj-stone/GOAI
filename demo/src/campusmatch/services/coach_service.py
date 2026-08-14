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
    first = evidence["E-S001-001"]
    excel = evidence["E-S001-003"]

    return CoachingResult(
        task_id=task_id,
        resume_suggestions=[
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
        ],
        learning_plan=[
            LearningAction(
                target="内容与用户意识",
                action_type="EVIDENCE",
                action="完成一篇活动通知或用户反馈整理样稿，并保留可确认的作品。",
            )
        ],
        interview_questions=[
            InterviewQuestion(
                question="请介绍一次你协调多人完成课程任务的经历，你具体承担了什么？",
                evidence_refs=["E-S001-001"],
            ),
            InterviewQuestion(
                question="活动现场人员安排发生变化时，你如何调整并通知相关人员？",
                evidence_refs=["E-S001-005"],
            ),
        ],
    )
