import json
from pathlib import Path

import pytest

from campusmatch.services.job_service import JobParseError, parse_job


FIXTURES = Path(__file__).parents[1] / "fixtures"


def test_job_parser_reproduces_four_requirement_categories() -> None:
    """Collapsing must, bonus, ambiguity, and policy risk must break parsing."""
    text = (FIXTURES / "job-general-operations.md").read_text(encoding="utf-8")
    expected = json.loads((FIXTURES / "expected-job.json").read_text(encoding="utf-8"))

    result = parse_job(text, job_id="J001", mode="job_search")

    assert result.model_dump(mode="json", exclude_none=True) == expected


def test_ambiguous_language_becomes_a_behavior_question() -> None:
    """Vague personality language must become an interviewable behavior prompt."""
    text = (FIXTURES / "job-general-operations.md").read_text(encoding="utf-8")

    result = parse_job(text, job_id="J001", mode="job_search")
    ambiguous = next(item for item in result.requirements if item.category == "AMBIGUOUS")

    assert ambiguous.weight == 0
    assert ambiguous.behavior_question == "请举例说明计划临时变化时，你如何调整任务并与他人沟通。"


def test_sensitive_preference_is_excluded_instead_of_scored() -> None:
    """Gender preference must never become a candidate requirement."""
    text = (FIXTURES / "job-general-operations.md").read_text(encoding="utf-8")

    result = parse_job(text, job_id="J001", mode="job_search")
    risk = next(item for item in result.requirements if item.requirement_id == "R-GENDER")

    assert risk.category == "POLICY_RISK"
    assert risk.weight == 0
    assert risk.competency_ids == []


def test_job_parser_requests_input_when_no_supported_requirement_exists() -> None:
    """Unparseable text must not silently become an all-zero job profile."""
    with pytest.raises(JobParseError) as error:
        parse_job("欢迎加入我们。", job_id="J-EMPTY", mode="job_search")

    assert error.value.code == "JOB_REQUIREMENTS_NOT_FOUND"
