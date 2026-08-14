import re
from pathlib import Path


AGENTTEAMS = Path(__file__).parents[1] / "agentteams"


def test_worker_skills_reference_registered_mcp_server_name() -> None:
    skill_files = sorted((AGENTTEAMS / "skills").glob("*/SKILL.md"))

    assert skill_files
    for skill_file in skill_files:
        text = skill_file.read_text(encoding="utf-8")
        if "mcporter" in text:
            assert "mcp-campusmatch" in text, skill_file
            assert re.search(r"(?<!mcp-)campusmatch\.", text) is None, skill_file


def test_worker_skills_do_not_send_undeclared_schema_argument() -> None:
    for skill_file in (AGENTTEAMS / "skills").glob("*/SKILL.md"):
        text = skill_file.read_text(encoding="utf-8")
        assert "schema_version=" not in text, skill_file


def test_worker_mcp_helper_uses_runtime_credential_without_embedding_it() -> None:
    helper = (AGENTTEAMS / "configure-worker-mcp.sh").read_text(encoding="utf-8")

    assert "AGENTTEAMS_WORKER_GATEWAY_KEY" in helper
    assert "mcp-campusmatch" in helper
    assert "Bearer " in helper
    assert "CAMPUSMATCH_MCP_TOKEN" not in helper


def test_registered_mcp_exposes_the_six_documented_tools() -> None:
    config = (AGENTTEAMS / "mcp-campusmatch.yaml").read_text(encoding="utf-8")
    tool_names = re.findall(r"^- name: ([a-z_]+)$", config, flags=re.MULTILINE)

    assert tool_names == [
        "profile_materials",
        "parse_job",
        "match_evidence",
        "generate_coaching",
        "audit_export",
        "get_task_status",
    ]


def test_team_delegation_uses_a_real_matrix_mention() -> None:
    helper = (AGENTTEAMS / "delegate-team-smoke.sh").read_text(encoding="utf-8")

    assert 'format:"org.matrix.custom.html"' in helper
    assert '"m.mentions":{user_ids:[$user]}' in helper
    assert "https://matrix.to/#/${leader_matrix_id}" in helper
    assert "$(date +%s)" in helper
