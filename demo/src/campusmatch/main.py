import os
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from campusmatch.contracts import (
    AnalysisRunRequest,
    AuditResult,
    AuditToolRequest,
    CoachingResult,
    DemoRunRequest,
    DemoRunResult,
    DocumentConversion,
    JobProfile,
    JobToolRequest,
    MatchResult,
    Profile,
    ProfileToolRequest,
    ToolRequest,
)
from campusmatch.services.audit_service import audit_coaching
from campusmatch.services.coach_service import generate_coaching
from campusmatch.services.document_service import DocumentError, convert_document
from campusmatch.services.job_service import parse_job
from campusmatch.services.job_service import JobParseError
from campusmatch.services.match_service import calculate_match
from campusmatch.services.profile_service import extract_profile
from campusmatch.services.report_service import build_markdown_report
from campusmatch.workflow import run_analysis, run_demo


app = FastAPI(title="CampusMatch Demo", version="0.1.0")
STATIC_ROOT = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_ROOT), name="static")
TASKS: dict[str, dict[str, Any]] = {}
PUBLIC_RUNS: dict[str, DemoRunResult] = {}


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
    record: dict[str, Any], scope: str, key: str, compute: Callable[[], Any]
) -> Any:
    cache = record["idempotency"].setdefault(scope, {})
    cached = cache.get(key)
    if cached is not None:
        return cached
    result = compute()
    cache[key] = result
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


@app.post("/api/v1/documents/convert", response_model=DocumentConversion)
async def convert_uploaded_document(file: UploadFile = File(...)) -> DocumentConversion:
    content = await file.read(5 * 1024 * 1024 + 1)
    try:
        return convert_document(file.filename or "unnamed", content)
    except DocumentError as error:
        raise HTTPException(
            status_code=422,
            detail={"code": error.code, "message": str(error)},
        ) from error


@app.post("/api/v1/demo/run", response_model=DemoRunResult)
def demo_run(request: DemoRunRequest) -> DemoRunResult:
    return run_demo(
        task_id=request.task_id,
        human_approved=request.human_approved,
    )


@app.post("/api/v1/analyze", response_model=DemoRunResult)
def public_analysis(request: AnalysisRunRequest) -> DemoRunResult:
    try:
        result = run_analysis(
            task_id=request.task_id,
            markdown=request.markdown,
            job_markdown=request.job_markdown,
            mode=request.mode,
            consent_granted=request.consent_granted,
            human_approved=request.human_approved,
        )
    except (DocumentError, JobParseError) as error:
        raise HTTPException(
            status_code=422,
            detail={"code": error.code, "message": str(error)},
        ) from error
    PUBLIC_RUNS[request.task_id] = result
    return result


@app.get("/api/v1/reports/{task_id}.md", response_class=PlainTextResponse)
def export_markdown_report(task_id: str) -> PlainTextResponse:
    result = PUBLIC_RUNS.get(task_id)
    if result is None or not result.audit.export_allowed:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "EXPORT_BLOCKED",
                "message": "报告尚未通过审计和人工批准，暂时不能导出。",
            },
        )
    return PlainTextResponse(
        build_markdown_report(result),
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="campusmatch-{task_id}.md"'
        },
    )


@app.post("/api/v1/profile", response_model=Profile)
def profile_tool(
    request: ProfileToolRequest, _: None = Depends(require_mcp_auth)
) -> Profile:
    record = record_for(request.task_id)
    profile = cached_or_compute(
        record,
        "profile",
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
        "job",
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
        "match",
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
        "coach",
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
    require_stages(record, "profile", "match", "coach")
    audit = cached_or_compute(
        record,
        "audit",
        request.idempotency_key,
        lambda: audit_coaching(
            record["profile"],
            record["match"],
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
