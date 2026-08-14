from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator


SourceType = Literal["course", "club", "volunteer", "self_confirmed"]
RequirementCategory = Literal["MUST", "BONUS", "AMBIGUOUS", "POLICY_RISK"]
UserMode = Literal["job_search", "career_change", "explore"]
MatchState = Literal[
    "MATCH",
    "PARTIAL",
    "NO_EVIDENCE",
    "GAP",
    "CONFLICT",
    "POLICY_EXCLUDED",
]
TaskId = Annotated[
    str,
    Field(
        min_length=1,
        max_length=100,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$",
    ),
]


class Evidence(BaseModel):
    evidence_id: str
    source_id: str
    source_type: SourceType
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)
    quote: str = Field(min_length=1)
    confirmed_by_user: bool


class Competency(BaseModel):
    competency_id: str
    label: str
    evidence_refs: list[str] = Field(min_length=1)
    evidence_strength: Literal["direct", "related"] = "direct"


class Profile(BaseModel):
    schema_version: Literal["1.0"]
    user_id: str
    evidence: list[Evidence]
    competencies: list[Competency]

    @model_validator(mode="after")
    def validate_evidence_references(self) -> "Profile":
        evidence_ids = {item.evidence_id for item in self.evidence}
        unknown = sorted(
            {
                reference
                for competency in self.competencies
                for reference in competency.evidence_refs
                if reference not in evidence_ids
            }
        )
        if unknown:
            raise ValueError(f"unknown evidence_refs: {', '.join(unknown)}")
        return self


class JobRequirement(BaseModel):
    requirement_id: str
    label: str
    category: RequirementCategory
    weight: float = Field(ge=0, le=100)
    competency_ids: list[str] = Field(default_factory=list)
    raw_text: str | None = None
    behavior_question: str | None = None


class JobProfile(BaseModel):
    schema_version: Literal["1.0"]
    job_id: str
    title: str
    mode: UserMode
    requirements: list[JobRequirement]

    @model_validator(mode="after")
    def validate_scoring_weights(self) -> "JobProfile":
        for requirement in self.requirements:
            if requirement.category == "POLICY_RISK" and requirement.weight != 0:
                raise ValueError("POLICY_RISK weight must be 0")

        legal_total = sum(
            item.weight
            for item in self.requirements
            if item.category != "POLICY_RISK"
        )
        if abs(legal_total - 100) > 1e-6:
            raise ValueError("legal requirement weights must sum to 100")
        return self


class MatchItem(BaseModel):
    requirement_id: str
    label: str
    category: RequirementCategory
    weight: float
    state: MatchState
    coefficient: float
    evidence_refs: list[str]
    reason: str
    counted: bool


class MatchResult(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    task_id: str
    match_score: float
    evidence_coverage: float
    disclaimer: str
    items: list[MatchItem]


class ResumeSuggestion(BaseModel):
    original: str
    suggestion: str
    evidence_refs: list[str] = Field(min_length=1)
    needs_confirmation: bool = False


class LearningAction(BaseModel):
    target: str
    action_type: Literal["EVIDENCE", "LEARN"]
    action: str


class InterviewQuestion(BaseModel):
    question: str
    evidence_refs: list[str]


class CoachingResult(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    task_id: str
    resume_suggestions: list[ResumeSuggestion]
    learning_plan: list[LearningAction]
    interview_questions: list[InterviewQuestion]


class AuditIssue(BaseModel):
    code: str
    message: str
    action: str


class AuditResult(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    task_id: str
    status: Literal["PASS", "BLOCK"]
    export_allowed: bool
    issues: list[AuditIssue]


class DocumentConversion(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    filename: str
    source_format: Literal["md", "txt", "docx", "pdf"]
    markdown: str
    char_count: int = Field(ge=1)


class TraceEvent(BaseModel):
    stage: Literal["profile", "job", "match", "coach", "audit"]
    agent: str
    status: Literal["COMPLETED"] = "COMPLETED"
    detail: str


class AnalysisRunRequest(BaseModel):
    task_id: TaskId
    markdown: str
    job_markdown: str
    mode: UserMode = "job_search"
    consent_granted: bool
    human_approved: bool = False


class DemoRunRequest(BaseModel):
    task_id: TaskId = "demo-s001"
    human_approved: bool = False


class DemoRunResult(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    task_id: str
    state: Literal["BLOCKED", "APPROVED"]
    markdown: str
    job_markdown: str
    profile: Profile
    job: JobProfile
    match: MatchResult
    coaching: CoachingResult
    audit: AuditResult
    trace: list[TraceEvent]


class ToolRequest(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    task_id: TaskId
    idempotency_key: str = Field(min_length=1, max_length=200)


class ProfileToolRequest(ToolRequest):
    user_id: str
    source_id: str
    markdown: str


class JobToolRequest(ToolRequest):
    job_id: str
    mode: UserMode
    jd_markdown: str


class AuditToolRequest(ToolRequest):
    consent_granted: bool
    trace_present: bool
    human_approved: bool
