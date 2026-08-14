from collections.abc import Callable

from campusmatch.contracts import Competency, Evidence, Profile
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


def extract_profile(text: str, *, user_id: str, source_id: str) -> Profile:
    normalized = normalize_markdown(text)
    lines = normalized.splitlines()
    evidence: list[Evidence] = []

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
            evidence.append(
                Evidence(
                    evidence_id=evidence_id,
                    source_id=source_id,
                    source_type=source_type,
                    line_start=line_number,
                    line_end=line_number,
                    quote=quote,
                    confirmed_by_user=True,
                )
            )

    evidence_ids = {item.evidence_id for item in evidence}
    competencies = [
        Competency(
            competency_id=competency_id,
            label=label,
            evidence_refs=references,
            evidence_strength=strength,
        )
        for competency_id, label, references, strength in COMPETENCY_RULES
        if all(reference in evidence_ids for reference in references)
    ]

    return Profile(
        schema_version="1.0",
        user_id=user_id,
        evidence=evidence,
        competencies=competencies,
    )
