from pathlib import Path

from campusmatch.contracts import CoachingResult, JobProfile, Profile
from campusmatch.services.audit_service import audit_coaching
from campusmatch.services.coach_service import generate_coaching
from campusmatch.services.match_service import calculate_match
from campusmatch.services.profile_service import extract_profile


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
        match,
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
        match,
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
        match,
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
        match,
        coaching,
        task_id="demo-s001",
        consent_granted=True,
        trace_present=True,
        human_approved=False,
    )

    assert audit.status == "BLOCK"
    assert audit.export_allowed is False
    assert "APPROVAL_REQUIRED" in {issue.code for issue in audit.issues}


def test_coach_handles_general_evidence_without_demo_ids() -> None:
    profile = extract_profile(
        "# 项目经历\n协调团队完成活动，并使用 Excel 整理报名名单。",
        user_id="U100",
        source_id="upload-resume",
    )
    job = JobProfile.model_validate_json(
        (FIXTURES / "expected-job.json").read_text(encoding="utf-8")
    )
    match = calculate_match(profile, job, task_id="general-001")

    coaching = generate_coaching(profile, match, task_id="general-001")

    assert coaching.resume_suggestions
    evidence_ids = {item.evidence_id for item in profile.evidence}
    assert all(
        set(suggestion.evidence_refs) <= evidence_ids
        for suggestion in coaching.resume_suggestions
    )


def test_private_contact_in_source_evidence_blocks_export() -> None:
    """PII in quoted source evidence must not leak into an exported report."""
    profile, match = load_context()
    private_profile = profile.model_copy(deep=True)
    private_profile.evidence[0].quote += " 联系邮箱 student@example.com"
    coaching = generate_coaching(private_profile, match, task_id="privacy-001")

    audit = audit_coaching(
        private_profile,
        match,
        coaching,
        task_id="privacy-001",
        consent_granted=True,
        trace_present=True,
        human_approved=True,
    )

    assert audit.export_allowed is False
    assert "PRIVACY_IN_SOURCE" in {issue.code for issue in audit.issues}


def test_policy_risk_must_remain_excluded_from_scoring() -> None:
    """Audit must block any regression that lets a policy-risk item affect score."""
    profile, match = load_context()
    unsafe_match = match.model_copy(deep=True)
    risk_item = next(item for item in unsafe_match.items if item.category == "POLICY_RISK")
    risk_item.counted = True
    risk_item.weight = 10
    risk_item.state = "MATCH"
    coaching = generate_coaching(profile, unsafe_match, task_id="policy-001")

    audit = audit_coaching(
        profile,
        unsafe_match,
        coaching,
        task_id="policy-001",
        consent_granted=True,
        trace_present=True,
        human_approved=True,
    )

    assert audit.export_allowed is False
    assert "POLICY_RISK_SCORED" in {issue.code for issue in audit.issues}
