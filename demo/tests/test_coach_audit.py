from pathlib import Path

from campusmatch.contracts import CoachingResult, JobProfile, Profile
from campusmatch.services.audit_service import audit_coaching
from campusmatch.services.coach_service import generate_coaching
from campusmatch.services.match_service import calculate_match


FIXTURES = Path(__file__).parents[1] / "fixtures"


def load_context():
    profile = Profile.model_validate_json(
        (FIXTURES / "expected-profile.json").read_text(encoding="utf-8")
    )
    job = JobProfile.model_validate_json(
        (FIXTURES / "expected-job.json").read_text(encoding="utf-8")
    )
    match = calculate_match(profile, job, task_id="demo-s001")
    return profile, match


def test_grounded_coaching_passes_after_human_approval() -> None:
    """Evidence-backed advice must remain exportable after all gates pass."""
    profile, match = load_context()
    coaching = generate_coaching(profile, match, task_id="demo-s001")

    audit = audit_coaching(
        profile,
        coaching,
        task_id="demo-s001",
        consent_granted=True,
        trace_present=True,
        human_approved=True,
    )

    assert audit.status == "PASS"
    assert audit.export_allowed is True
    assert audit.issues == []


def test_ungrounded_numeric_claim_blocks_export() -> None:
    """A new performance number must be blocked even when evidence IDs are valid."""
    profile, match = load_context()
    coaching = generate_coaching(profile, match, task_id="demo-s001")
    poisoned = coaching.model_copy(deep=True)
    poisoned.resume_suggestions[0].suggestion += "，使活动效率提升 30%"

    audit = audit_coaching(
        profile,
        poisoned,
        task_id="demo-s001",
        consent_granted=True,
        trace_present=True,
        human_approved=True,
    )

    assert audit.status == "BLOCK"
    assert audit.export_allowed is False
    assert "UNGROUNDED_NUMERIC_CLAIM" in {issue.code for issue in audit.issues}


def test_unsupported_leadership_claim_blocks_export() -> None:
    """Turning assistance into independent ownership must never pass Audit."""
    profile, match = load_context()
    coaching = generate_coaching(profile, match, task_id="demo-s001")
    poisoned = coaching.model_copy(deep=True)
    poisoned.resume_suggestions[0].suggestion = "独立策划大型活动并统筹全流程"

    audit = audit_coaching(
        profile,
        poisoned,
        task_id="demo-s001",
        consent_granted=True,
        trace_present=True,
        human_approved=True,
    )

    assert "UNGROUNDED_FACT_CLAIM" in {issue.code for issue in audit.issues}
    assert audit.export_allowed is False


def test_approval_gate_is_separate_from_content_quality() -> None:
    """A clean draft must still be blocked until a human approves export."""
    profile, match = load_context()
    coaching: CoachingResult = generate_coaching(
        profile, match, task_id="demo-s001"
    )

    audit = audit_coaching(
        profile,
        coaching,
        task_id="demo-s001",
        consent_granted=True,
        trace_present=True,
        human_approved=False,
    )

    assert audit.status == "BLOCK"
    assert audit.export_allowed is False
    assert "APPROVAL_REQUIRED" in {issue.code for issue in audit.issues}
