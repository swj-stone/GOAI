from pathlib import Path

from campusmatch.contracts import DemoRunResult
from campusmatch.services.audit_service import audit_coaching
from campusmatch.services.coach_service import generate_coaching
from campusmatch.services.job_service import parse_job
from campusmatch.services.match_service import calculate_match
from campusmatch.services.profile_service import extract_profile


DEMO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = DEMO_ROOT / "fixtures"


def run_demo(*, task_id: str, human_approved: bool) -> DemoRunResult:
    markdown = (FIXTURES / "student-materials.md").read_text(encoding="utf-8")
    job_markdown = (FIXTURES / "job-general-operations.md").read_text(
        encoding="utf-8"
    )
    profile = extract_profile(
        markdown, user_id="S001", source_id="student-materials"
    )
    job = parse_job(job_markdown, job_id="J001", mode="job_search")
    match = calculate_match(profile, job, task_id=task_id)
    coaching = generate_coaching(profile, match, task_id=task_id)
    audit = audit_coaching(
        profile,
        coaching,
        task_id=task_id,
        consent_granted=True,
        trace_present=True,
        human_approved=human_approved,
    )

    return DemoRunResult(
        task_id=task_id,
        state="APPROVED" if audit.export_allowed else "BLOCKED",
        markdown=markdown,
        job_markdown=job_markdown,
        profile=profile,
        job=job,
        match=match,
        coaching=coaching,
        audit=audit,
    )
