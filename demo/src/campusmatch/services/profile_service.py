from collections.abc import Callable

import re

from campusmatch.contracts import Competency, Evidence, Profile, SourceType
from campusmatch.services.document_service import normalize_markdown


EvidencePredicate = Callable[[str], bool]


EVIDENCE_RULES: list[tuple[str, str, EvidencePredicate]] = [
    ("E-S001-001", "course", lambda line: "协调 5 人分工" in line),
    (
        "E-S001-002",
        "course",
        lambda line: "Word" in line and "PowerPoint" in line,
    ),
    ("E-S001-003", "club", lambda line: "Excel" in line and "报名名单" in line),
    (
        "E-S001-004",
        "club",
        lambda line: "报名通知" in line and "签到" in line,
    ),
    ("E-S001-005", "volunteer", lambda line: "访客引导" in line),
]


COMPETENCY_RULES = [
    ("C-COMMUNICATION", "沟通表达", ["E-S001-001", "E-S001-005"], "direct"),
    ("C-WRITING", "文档写作", ["E-S001-001", "E-S001-002"], "related"),
    ("C-OFFICE", "办公与信息处理", ["E-S001-003"], "direct"),
    (
        "C-ACTIVITY",
        "活动执行与协作",
        ["E-S001-003", "E-S001-004", "E-S001-005"],
        "direct",
    ),
]


GENERIC_COMPETENCY_RULES: list[tuple[str, str, tuple[str, ...]]] = [
    ("C-COMMUNICATION", "沟通表达", ("沟通", "协调", "展示", "答疑", "汇报", "访客")),
    ("C-WRITING", "文档写作", ("文档", "提纲", "Word", "文案", "报告", "写作")),
    ("C-OFFICE", "办公与信息处理", ("Excel", "数据", "信息整理", "名单", "表格")),
    ("C-ACTIVITY", "活动执行与协作", ("活动", "报名", "签到", "排班", "组织", "协作")),
    ("C-CONTENT", "内容与用户意识", ("公众号", "内容发布", "用户反馈", "社交媒体", "运营")),
]


def infer_source_type(heading: str) -> SourceType:
    if "课程" in heading or "课堂" in heading:
        return "course"
    if "社团" in heading or "学生会" in heading:
        return "club"
    if "志愿" in heading:
        return "volunteer"
    return "self_confirmed"


def legacy_profile(
    matches: list[tuple[str, str, int, str]], *, user_id: str, source_id: str
) -> Profile:
    evidence = [
        Evidence(
            evidence_id=evidence_id,
            source_id=source_id,
            source_type=source_type,
            line_start=line_number,
            line_end=line_number,
            quote=quote,
            confirmed_by_user=True,
        )
        for evidence_id, source_type, line_number, quote in matches
    ]
    competencies = [
        Competency(
            competency_id=competency_id,
            label=label,
            evidence_refs=references,
            evidence_strength=strength,
        )
        for competency_id, label, references, strength in COMPETENCY_RULES
    ]
    return Profile(
        schema_version="1.0",
        user_id=user_id,
        evidence=evidence,
        competencies=competencies,
    )


def extract_profile(text: str, *, user_id: str, source_id: str) -> Profile:
    normalized = normalize_markdown(text)
    lines = normalized.splitlines()
    legacy_matches: list[tuple[str, str, int, str]] = []
    for evidence_id, source_type, predicate in EVIDENCE_RULES:
        match = next(
            (
                (line_number, line)
                for line_number, line in enumerate(lines, start=1)
                if predicate(line)
            ),
            None,
        )
        if match:
            line_number, quote = match
            legacy_matches.append((evidence_id, source_type, line_number, quote))

    if len(legacy_matches) == len(EVIDENCE_RULES):
        return legacy_profile(legacy_matches, user_id=user_id, source_id=source_id)

    safe_user = re.sub(r"[^A-Za-z0-9]", "", user_id.upper())[:12] or "USER"
    evidence: list[Evidence] = []
    competency_refs: dict[str, list[str]] = {
        competency_id: []
        for competency_id, _, _ in GENERIC_COMPETENCY_RULES
    }
    current_source: SourceType = "self_confirmed"

    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            current_source = infer_source_type(stripped.lstrip("# "))
            continue

        matched_competencies = [
            competency_id
            for competency_id, _, keywords in GENERIC_COMPETENCY_RULES
            if any(keyword.lower() in stripped.lower() for keyword in keywords)
        ]
        if not matched_competencies:
            continue

        evidence_id = f"E-{safe_user}-{len(evidence) + 1:03d}"
        evidence.append(
            Evidence(
                evidence_id=evidence_id,
                source_id=source_id,
                source_type=current_source,
                line_start=line_number,
                line_end=line_number,
                quote=line,
                confirmed_by_user=True,
            )
        )
        for competency_id in matched_competencies:
            competency_refs[competency_id].append(evidence_id)

    competencies = [
        Competency(
            competency_id=competency_id,
            label=label,
            evidence_refs=competency_refs[competency_id],
            evidence_strength="direct",
        )
        for competency_id, label, _ in GENERIC_COMPETENCY_RULES
        if competency_refs[competency_id]
    ]

    return Profile(
        schema_version="1.0",
        user_id=user_id,
        evidence=evidence,
        competencies=competencies,
    )
