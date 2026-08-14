import re

from campusmatch.contracts import JobProfile, JobRequirement, UserMode


class JobParseError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def parse_job(text: str, *, job_id: str, mode: UserMode) -> JobProfile:
    scoring_rules = [
        (
            "R-COMMUNICATION",
            "沟通表达",
            "MUST",
            25,
            ["C-COMMUNICATION"],
            "沟通表达清晰",
            lambda value: "沟通表达" in value,
        ),
        (
            "R-WRITING",
            "文档写作",
            "MUST",
            20,
            ["C-WRITING"],
            "能够完成基础文档写作",
            lambda value: "文档写作" in value,
        ),
        (
            "R-OFFICE",
            "办公与信息处理",
            "MUST",
            20,
            ["C-OFFICE"],
            "能使用 Excel 完成名单和信息整理",
            lambda value: "Excel" in value and "信息整理" in value,
        ),
        (
            "R-ACTIVITY",
            "活动执行与协作",
            "BONUS",
            20,
            ["C-ACTIVITY"],
            "有活动支持经历者优先",
            lambda value: "活动支持" in value,
        ),
        (
            "R-CONTENT",
            "内容与用户意识",
            "BONUS",
            15,
            ["C-CONTENT"],
            "有内容发布或用户反馈整理经验者优先",
            lambda value: "内容发布" in value or "用户反馈" in value,
        ),
    ]

    matched = [rule for rule in scoring_rules if rule[-1](text)]
    if not matched:
        raise JobParseError(
            "JOB_REQUIREMENTS_NOT_FOUND",
            "没有识别到可比较的岗位要求，请补充岗位职责或要求。",
        )

    base_total = sum(rule[3] for rule in matched)
    requirements: list[JobRequirement] = []
    assigned = 0.0
    for index, rule in enumerate(matched):
        requirement_id, label, category, base_weight, competency_ids, raw_text, _ = rule
        if index == len(matched) - 1:
            weight = round(100 - assigned, 2)
        else:
            weight = round(base_weight / base_total * 100, 2)
            assigned += weight
        requirements.append(
            JobRequirement(
                requirement_id=requirement_id,
                label=label,
                category=category,
                weight=weight,
                competency_ids=competency_ids,
                raw_text=raw_text,
            )
        )

    if "抗压能力强" in text or "主人翁意识" in text:
        requirements.append(
            JobRequirement(
                requirement_id="R-RESILIENCE",
                label="抗压能力强、有主人翁意识",
                category="AMBIGUOUS",
                weight=0,
                competency_ids=[],
                raw_text="抗压能力强，有主人翁意识",
                behavior_question="请举例说明计划临时变化时，你如何调整任务并与他人沟通。",
            )
        )

    if "女性优先" in text:
        requirements.append(
            JobRequirement(
                requirement_id="R-GENDER",
                label="女性优先",
                category="POLICY_RISK",
                weight=0,
                competency_ids=[],
                raw_text="女性优先",
            )
        )

    heading = next(
        (line.removeprefix("# ").strip() for line in text.splitlines() if line.startswith("# ")),
        "未命名岗位",
    )
    title = re.sub(r"（[^）]*）$", "", heading)

    return JobProfile(
        schema_version="1.0",
        job_id=job_id,
        title=title,
        mode=mode,
        requirements=requirements,
    )
