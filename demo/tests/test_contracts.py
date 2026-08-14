import json
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from campusmatch.contracts import (
    Competency,
    Evidence,
    JobProfile,
    JobRequirement,
    Profile,
)


FIXTURES = Path(__file__).parents[1] / "fixtures"


def sample_evidence() -> Evidence:
    return Evidence(
        evidence_id="E-S001-001",
        source_id="student-materials",
        source_type="course",
        line_start=5,
        line_end=5,
        quote="协调 5 人分工，整理汇报提纲并完成课堂展示。",
        confirmed_by_user=True,
    )


def test_profile_rejects_competency_without_existing_evidence() -> None:
    """A broken evidence reference must never reach matching or coaching."""
    with pytest.raises(ValidationError, match="unknown evidence_refs"):
        Profile(
            schema_version="1.0",
            user_id="S001",
            evidence=[sample_evidence()],
            competencies=[
                Competency(
                    competency_id="C-COMMUNICATION",
                    label="沟通表达",
                    evidence_refs=["E-NOT-FOUND"],
                )
            ],
        )


def test_job_rejects_legal_weights_that_do_not_total_100() -> None:
    """A wrong denominator must not produce a plausible-looking score."""
    with pytest.raises(ValidationError, match="sum to 100"):
        JobProfile(
            schema_version="1.0",
            job_id="J001",
            title="综合运营实习生",
            mode="job_search",
            requirements=[
                JobRequirement(
                    requirement_id="R-COMMUNICATION",
                    label="沟通表达",
                    category="MUST",
                    weight=90,
                )
            ],
        )


def test_job_rejects_policy_risk_with_nonzero_weight() -> None:
    """Sensitive conditions must be impossible to include in scoring."""
    with pytest.raises(ValidationError, match="POLICY_RISK weight must be 0"):
        JobProfile(
            schema_version="1.0",
            job_id="J001",
            title="综合运营实习生",
            mode="job_search",
            requirements=[
                JobRequirement(
                    requirement_id="R-COMMUNICATION",
                    label="沟通表达",
                    category="MUST",
                    weight=100,
                ),
                JobRequirement(
                    requirement_id="R-GENDER",
                    label="女性优先",
                    category="POLICY_RISK",
                    weight=10,
                ),
            ],
        )


def test_valid_profile_keeps_verbatim_evidence_coordinates() -> None:
    """Changing quote or line coordinates must remain visible to consumers."""
    evidence = sample_evidence()
    profile = Profile(
        schema_version="1.0",
        user_id="S001",
        evidence=[evidence],
        competencies=[
            Competency(
                competency_id="C-COMMUNICATION",
                label="沟通表达",
                evidence_refs=[evidence.evidence_id],
            )
        ],
    )

    assert profile.evidence[0].quote == "协调 5 人分工，整理汇报提纲并完成课堂展示。"
    assert (profile.evidence[0].line_start, profile.evidence[0].line_end) == (5, 5)


def test_committed_demo_fixtures_satisfy_contracts() -> None:
    """Malformed competition fixtures must fail before a live demonstration."""
    profile = Profile.model_validate_json(
        (FIXTURES / "expected-profile.json").read_text(encoding="utf-8")
    )
    job = JobProfile.model_validate_json(
        (FIXTURES / "expected-job.json").read_text(encoding="utf-8")
    )

    assert profile.user_id == "S001"
    assert job.job_id == "J001"
    assert len(profile.competencies) == 4
    assert next(
        item for item in profile.competencies if item.competency_id == "C-WRITING"
    ).evidence_strength == "related"
    assert next(
        item for item in job.requirements if item.requirement_id == "R-CONTENT"
    ).competency_ids == ["C-CONTENT"]
    assert sum(item.weight for item in job.requirements if item.category != "POLICY_RISK") == 100


def test_student_fixture_contains_no_contact_or_identity_number() -> None:
    """Accidentally replacing synthetic material with PII must break CI."""
    material = (FIXTURES / "student-materials.md").read_text(encoding="utf-8")
    forbidden_patterns = [
        r"1[3-9]\d{9}",
        r"\b\d{17}[\dXx]\b",
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    ]

    assert not any(re.search(pattern, material) for pattern in forbidden_patterns)


def test_expected_match_fixture_keeps_hand_checked_scores() -> None:
    """Changing the showcased 77/85 result must require an explicit decision."""
    result = json.loads((FIXTURES / "expected-match.json").read_text(encoding="utf-8"))

    assert result["match_score"] == 77
    assert result["evidence_coverage"] == 85
