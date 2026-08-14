import json
from pathlib import Path

from campusmatch.contracts import JobProfile, Profile
from campusmatch.services.match_service import calculate_match


FIXTURES = Path(__file__).parents[1] / "fixtures"


def load_inputs() -> tuple[Profile, JobProfile]:
    profile = Profile.model_validate_json(
        (FIXTURES / "expected-profile.json").read_text(encoding="utf-8")
    )
    job = JobProfile.model_validate_json(
        (FIXTURES / "expected-job.json").read_text(encoding="utf-8")
    )
    return profile, job


def test_calculate_match_reproduces_hand_checked_77_and_85() -> None:
    """Wrong coefficients, weights, or coverage rules must break this test."""
    profile, job = load_inputs()

    result = calculate_match(profile, job, task_id="demo-s001")

    assert result.match_score == 77
    assert result.evidence_coverage == 85


def test_missing_content_evidence_is_not_claimed_as_a_skill_gap() -> None:
    """Removing evidence must not be reworded as proof that the user lacks ability."""
    profile, job = load_inputs()

    result = calculate_match(profile, job, task_id="demo-s001")
    content = next(item for item in result.items if item.requirement_id == "R-CONTENT")

    assert content.state == "NO_EVIDENCE"
    assert content.evidence_refs == []


def test_policy_risk_is_visible_but_never_counted() -> None:
    """A sensitive preference must not enter either score denominator."""
    profile, job = load_inputs()

    result = calculate_match(profile, job, task_id="demo-s001")
    risk = next(item for item in result.items if item.requirement_id == "R-GENDER")

    assert risk.state == "POLICY_EXCLUDED"
    assert risk.counted is False
    assert risk.weight == 0


def test_match_output_equals_committed_demo_fixture() -> None:
    """The API model and the competition fixture must stay in lockstep."""
    profile, job = load_inputs()
    expected = json.loads((FIXTURES / "expected-match.json").read_text(encoding="utf-8"))

    result = calculate_match(profile, job, task_id="demo-s001")

    assert result.model_dump(mode="json") == expected
