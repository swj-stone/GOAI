import os
from pathlib import Path

import anyio
from httpx import ASGITransport, AsyncClient

from campusmatch.main import app


FIXTURES = Path(__file__).parents[1] / "fixtures"


def request(method: str, path: str, **kwargs):
    async def send_request():
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            return await client.request(method, path, **kwargs)

    return anyio.run(send_request)


def test_health_reports_offline_service_version() -> None:
    """Removing the health route must break the public service contract."""
    response = request("GET", "/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "mode": "offline",
        "version": "0.1.0",
    }


def test_demo_run_exposes_explainable_scores_and_approval_block() -> None:
    """The public workflow must not hide scores or bypass human approval."""
    response = request(
        "POST", "/api/v1/demo/run", json={"task_id": "demo-s001", "human_approved": False}
    )

    assert response.status_code == 200
    result = response.json()
    assert result["state"] == "BLOCKED"
    assert result["match"]["match_score"] == 77
    assert result["match"]["evidence_coverage"] == 85
    assert "APPROVAL_REQUIRED" in {
        issue["code"] for issue in result["audit"]["issues"]
    }


def test_demo_run_passes_only_after_explicit_approval() -> None:
    """Changing the approval input must be the event that opens export."""
    response = request(
        "POST", "/api/v1/demo/run", json={"task_id": "demo-s001", "human_approved": True}
    )

    assert response.status_code == 200
    result = response.json()
    assert result["state"] == "APPROVED"
    assert result["audit"]["status"] == "PASS"
    assert result["audit"]["export_allowed"] is True


def test_home_page_offers_plain_language_demo_entry() -> None:
    """Replacing the student entry with a developer-only UI must break this test."""
    response = request("GET", "/")

    assert response.status_code == 200
    assert "CampusMatch" in response.text
    assert "使用演示案例" in response.text
    assert "API Key" not in response.text


def test_agent_tool_endpoints_share_one_task_state() -> None:
    """Breaking structured hand-offs between Workers must fail end-to-end."""
    material = (FIXTURES / "student-materials.md").read_text(encoding="utf-8")
    jd = (FIXTURES / "job-general-operations.md").read_text(encoding="utf-8")
    task_id = "agent-e2e-001"

    profile = request(
        "POST",
        "/api/v1/profile",
        json={
            "schema_version": "1.0",
            "task_id": task_id,
            "idempotency_key": f"{task_id}:profile:v1",
            "user_id": "S001",
            "source_id": "student-materials",
            "markdown": material,
        },
    )
    job = request(
        "POST",
        "/api/v1/job",
        json={
            "schema_version": "1.0",
            "task_id": task_id,
            "idempotency_key": f"{task_id}:job:v1",
            "job_id": "J001",
            "mode": "job_search",
            "jd_markdown": jd,
        },
    )
    match = request(
        "POST",
        "/api/v1/match",
        json={
            "schema_version": "1.0",
            "task_id": task_id,
            "idempotency_key": f"{task_id}:match:v1",
        },
    )
    coaching = request(
        "POST",
        "/api/v1/coach",
        json={
            "schema_version": "1.0",
            "task_id": task_id,
            "idempotency_key": f"{task_id}:coach:v1",
        },
    )
    audit = request(
        "POST",
        "/api/v1/audit",
        json={
            "schema_version": "1.0",
            "task_id": task_id,
            "idempotency_key": f"{task_id}:audit:v1",
            "consent_granted": True,
            "trace_present": True,
            "human_approved": True,
        },
    )
    status = request("GET", f"/api/v1/tasks/{task_id}")

    assert profile.status_code == job.status_code == 200
    assert match.json()["match_score"] == 77
    assert coaching.json()["resume_suggestions"]
    assert audit.json()["export_allowed"] is True
    assert status.json()["completed_stages"] == [
        "profile",
        "job",
        "match",
        "coach",
        "audit",
    ]


def test_match_tool_refuses_to_run_without_profile_and_job() -> None:
    """Out-of-order Worker execution must return a recoverable task error."""
    response = request(
        "POST",
        "/api/v1/match",
        json={
            "schema_version": "1.0",
            "task_id": "missing-inputs",
            "idempotency_key": "missing-inputs:match:v1",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "TASK_INPUTS_MISSING"


def test_agent_tools_require_bearer_token_when_configured() -> None:
    """Enabling a local gateway token must close unauthenticated tool access."""
    previous = os.environ.get("CAMPUSMATCH_MCP_TOKEN")
    os.environ["CAMPUSMATCH_MCP_TOKEN"] = "test-local-token"
    try:
        denied = request(
            "POST",
            "/api/v1/profile",
            json={
                "schema_version": "1.0",
                "task_id": "auth-001",
                "idempotency_key": "auth-001:profile:v1",
                "user_id": "S001",
                "source_id": "student-materials",
                "markdown": "有效材料",
            },
        )
        allowed = request(
            "POST",
            "/api/v1/profile",
            headers={"Authorization": "Bearer test-local-token"},
            json={
                "schema_version": "1.0",
                "task_id": "auth-001",
                "idempotency_key": "auth-001:profile:v1",
                "user_id": "S001",
                "source_id": "student-materials",
                "markdown": "有效材料",
            },
        )
    finally:
        if previous is None:
            os.environ.pop("CAMPUSMATCH_MCP_TOKEN", None)
        else:
            os.environ["CAMPUSMATCH_MCP_TOKEN"] = previous

    assert denied.status_code == 401
    assert allowed.status_code == 200
