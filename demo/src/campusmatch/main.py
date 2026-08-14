import os
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from campusmatch.contracts import (
    AuditResult,
    AuditToolRequest,
    CoachingResult,
    DemoRunRequest,
    DemoRunResult,
    JobProfile,
    JobToolRequest,
    MatchResult,
    Profile,
    ProfileToolRequest,
    ToolRequest,
)
from campusmatch.services.audit_service import audit_coaching
from campusmatch.services.coach_service import generate_coaching
from campusmatch.services.job_service import parse_job
from campusmatch.services.match_service import calculate_match
from campusmatch.services.profile_service import extract_profile
from campusmatch.workflow import run_demo


app = FastAPI(title="CampusMatch Demo", version="0.1.0")
STATIC_ROOT = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_ROOT), name="static")
TASKS: dict[str, dict[str, Any]] = {}


def require_mcp_auth(
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    expected = os.environ.get("CAMPUSMATCH_MCP_TOKEN")
    if expected and authorization != f"Bearer {expected}":
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "MCP access token is invalid."},
        )


def record_for(task_id: str) -> dict[str, Any]:
    return TASKS.setdefault(task_id, {"idempotency": {}})


def cached_or_compute(
    record: dict[str, Any], key: str, compute: Callable[[], Any]
) -> Any:
    cached = record["idempotency"].get(key)
    if cached is not None:
        return cached
    result = compute()
    record["idempotency"][key] = result
    return result


def require_stages(record: dict[str, Any], *stages: str) -> None:
    missing = [stage for stage in stages if stage not in record]
    if missing:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "TASK_INPUTS_MISSING",
                "message": f"Missing stages: {', '.join(missing)}",
            },
        )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "offline", "version": "0.1.0"}


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(STATIC_ROOT / "index.html")


@app.post("/api/v1/demo/run", response_model=DemoRunResult)
def demo_run(request: DemoRunRequest) -> DemoRunResult:
    return run_demo(
        task_id=request.task_id,
        human_approved=request.human_approved,
    )


@app.post("/api/v1/profile", response_model=Profile)
def profile_tool(
    request: ProfileToolRequest, _: None = Depends(require_mcp_auth)
) -> Profile:
    record = record_for(request.task_id)
    profile = cached_or_compute(
        record,
        request.idempotency_key,
        lambda: extract_profile(
            request.markdown,
            user_id=request.user_id,
            source_id=request.source_id,
        ),
    )
    record["profile"] = profile
    return profile


@app.post("/api/v1/job", response_model=JobProfile, response_model_exclude_none=True)
def job_tool(
    request: JobToolRequest, _: None = Depends(require_mcp_auth)
) -> JobProfile:
    record = record_for(request.task_id)
    job = cached_or_compute(
        record,
        request.idempotency_key,
        lambda: parse_job(
            request.jd_markdown,
            job_id=request.job_id,
            mode=request.mode,
        ),
    )
    record["job"] = job
    return job


@app.post("/api/v1/match", response_model=MatchResult)
def match_tool(
    request: ToolRequest, _: None = Depends(require_mcp_auth)
) -> MatchResult:
    record = record_for(request.task_id)
    require_stages(record, "profile", "job")
    match = cached_or_compute(
        record,
        request.idempotency_key,
        lambda: calculate_match(
            record["profile"], record["job"], task_id=request.task_id
        ),
    )
    record["match"] = match
    return match


@app.post("/api/v1/coach", response_model=CoachingResult)
def coach_tool(
    request: ToolRequest, _: None = Depends(require_mcp_auth)
) -> CoachingResult:
    record = record_for(request.task_id)
    require_stages(record, "profile", "match")
    coaching = cached_or_compute(
        record,
        request.idempotency_key,
        lambda: generate_coaching(
            record["profile"], record["match"], task_id=request.task_id
        ),
    )
    record["coach"] = coaching
    return coaching


@app.post("/api/v1/audit", response_model=AuditResult)
def audit_tool(
    request: AuditToolRequest, _: None = Depends(require_mcp_auth)
) -> AuditResult:
    record = record_for(request.task_id)
    require_stages(record, "profile", "coach")
    audit = cached_or_compute(
        record,
        request.idempotency_key,
        lambda: audit_coaching(
            record["profile"],
            record["coach"],
            task_id=request.task_id,
            consent_granted=request.consent_granted,
            trace_present=request.trace_present,
            human_approved=request.human_approved,
        ),
    )
    record["audit"] = audit
    return audit


@app.get("/api/v1/tasks/{task_id}")
def task_status(
    task_id: str, _: None = Depends(require_mcp_auth)
) -> dict[str, Any]:
    record = TASKS.get(task_id, {})
    stages = [
        stage
        for stage in ["profile", "job", "match", "coach", "audit"]
        if stage in record
    ]
    return {
        "schema_version": "1.0",
        "task_id": task_id,
        "completed_stages": stages,
        "status": "READY" if "audit" in record else "IN_PROGRESS",
    }
