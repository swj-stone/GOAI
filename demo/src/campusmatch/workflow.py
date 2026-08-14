from pathlib import Path

from campusmatch.contracts import DemoRunResult, TraceEvent, UserMode
from campusmatch.services.audit_service import audit_coaching
from campusmatch.services.coach_service import generate_coaching
from campusmatch.services.job_service import parse_job
from campusmatch.services.match_service import calculate_match
from campusmatch.services.profile_service import extract_profile


DEMO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = DEMO_ROOT / "fixtures"


def run_analysis(
    *,
    task_id: str,
    markdown: str,
    job_markdown: str,
    mode: UserMode,
    consent_granted: bool,
    human_approved: bool,
) -> DemoRunResult:
    profile = extract_profile(
        markdown, user_id="S001", source_id="user-materials"
    )
    job = parse_job(job_markdown, job_id="J001", mode=mode)
    match = calculate_match(profile, job, task_id=task_id)
    coaching = generate_coaching(profile, match, task_id=task_id)
    audit = audit_coaching(
        profile,
        match,
        coaching,
        task_id=task_id,
        consent_granted=consent_granted,
        trace_present=True,
        human_approved=human_approved,
    )

    trace = [
        TraceEvent(
            stage="profile",
            agent="Profile Agent",
            detail=f"提取 {len(profile.evidence)} 条证据与 {len(profile.competencies)} 项能力。",
        ),
        TraceEvent(
            stage="job",
            agent="Job Agent",
            detail=f"识别 {len(job.requirements)} 条岗位要求并完成类别划分。",
        ),
        TraceEvent(
            stage="match",
            agent="Match Agent",
            detail=f"计算证据匹配度 {match.match_score:g} 与材料覆盖度 {match.evidence_coverage:g}。",
        ),
        TraceEvent(
            stage="coach",
            agent="Coach Agent",
            detail=f"生成 {len(coaching.resume_suggestions)} 条证据化简历建议。",
        ),
        TraceEvent(
            stage="audit",
            agent="Audit Agent",
            detail="审计通过，可导出。" if audit.export_allowed else "审计未通过，导出保持关闭。",
        ),
    ]

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
        trace=trace,
    )


def run_demo(*, task_id: str, human_approved: bool) -> DemoRunResult:
    markdown = (FIXTURES / "student-materials.md").read_text(encoding="utf-8")
    job_markdown = (FIXTURES / "job-general-operations.md").read_text(
        encoding="utf-8"
    )
    return run_analysis(
        task_id=task_id,
        markdown=markdown,
        job_markdown=job_markdown,
        mode="job_search",
        consent_granted=True,
        human_approved=human_approved,
    )
