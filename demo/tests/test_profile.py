import json
from pathlib import Path

import pytest

from campusmatch.services.document_service import DocumentError, normalize_markdown
from campusmatch.services.profile_service import extract_profile


FIXTURES = Path(__file__).parents[1] / "fixtures"


def test_profile_extraction_returns_only_verbatim_grounded_evidence() -> None:
    """Paraphrasing evidence or losing line numbers must break extraction."""
    material = (FIXTURES / "student-materials.md").read_text(encoding="utf-8")
    expected = json.loads(
        (FIXTURES / "expected-profile.json").read_text(encoding="utf-8")
    )

    profile = extract_profile(material, user_id="S001", source_id="student-materials")

    assert profile.model_dump(mode="json") == expected


def test_every_evidence_quote_exists_at_its_reported_line() -> None:
    """An off-by-one source pointer must fail even if the quote text is correct."""
    material = (FIXTURES / "student-materials.md").read_text(encoding="utf-8")
    profile = extract_profile(material, user_id="S001", source_id="student-materials")
    lines = material.splitlines()

    for evidence in profile.evidence:
        selected = "\n".join(lines[evidence.line_start - 1 : evidence.line_end])
        assert selected == evidence.quote


def test_normalize_markdown_rejects_blank_material() -> None:
    """Blank uploads must request input instead of producing an empty profile."""
    with pytest.raises(DocumentError) as error:
        normalize_markdown(" \r\n\t")

    assert error.value.code == "DOCUMENT_EMPTY"


def test_normalize_markdown_keeps_stable_line_boundaries() -> None:
    """Windows newlines and trailing spaces must not change evidence coordinates."""
    normalized = normalize_markdown("# 标题  \r\n\r\n内容\t\r\n")

    assert normalized == "# 标题\n\n内容"


def test_general_material_gets_dynamic_grounded_evidence() -> None:
    material = "# 项目经历\n协调团队完成活动，并使用 Excel 整理报名名单。"

    profile = extract_profile(material, user_id="U100", source_id="upload-resume")

    assert profile.evidence
    assert {item.label for item in profile.competencies} >= {
        "沟通表达",
        "办公与信息处理",
        "活动执行与协作",
    }
    for evidence in profile.evidence:
        assert evidence.quote in material
