from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal

from pydantic import BaseModel, Field, model_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


ArtifactStatus = Literal[
    "DRAFT",
    "IN_REVIEW",
    "APPROVED",
    "REJECTED",
    "AUTO_FIX_IN_PROGRESS",
    "AUTO_FIXED_PENDING_REVIEW",
    "IMPACTED",
    "MANUAL_RECOVERY",
    "ARCHIVED",
]


class SourceRef(BaseModel):
    page: int = Field(ge=1)
    bbox: list[float] | None = None
    table_ref: str | None = None


class AuditSourceRef(BaseModel):
    spec_id: str
    page: int = Field(ge=1)
    bbox: list[float] | None = None


class Compliance(BaseModel):
    classes: list[str] = Field(default_factory=list)
    asil: Literal["QM", "A", "B", "C", "D"] | None = None
    cal: Literal["QM", "1", "2", "3", "4"] | None = None


class SpecSection(BaseModel):
    id: str
    artifact_type: Literal["spec_section"] = "spec_section"
    schema_version: str
    status: Literal["DRAFT", "APPROVED", "ARCHIVED"] = "DRAFT"
    version: str
    section_key: str
    title: str
    text: str
    normalized_text: str | None = None
    parser_warnings: list[str] = Field(default_factory=list)
    source_refs: list[SourceRef]
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Note(BaseModel):
    id: str
    artifact_type: Literal["note"] = "note"
    schema_version: str
    status: ArtifactStatus = "DRAFT"
    version: str
    title: str
    summary: str
    source_spec_ids: list[str]
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class CreateNoteRequest(BaseModel):
    title: str
    summary: str
    source_spec_ids: list[str]


class RequirementTrace(BaseModel):
    graph_node_id: str
    downstream_test_requirement_ids: list[str] = Field(default_factory=list)


class AuditRationale(BaseModel):
    id: str
    artifact_id: str
    source_refs: list[AuditSourceRef]
    prompt_version: str
    model_version: str
    silver_refs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class Requirement(BaseModel):
    id: str
    artifact_type: Literal["requirement"] = "requirement"
    schema_version: str
    status: ArtifactStatus = "DRAFT"
    version: str
    title: str
    statement: str
    source_spec_ids: list[str]
    source_note_ids: list[str]
    compliance: Compliance = Field(default_factory=Compliance)
    trace: RequirementTrace
    audit_rationale_id: str | None = None
    variant_scope: Literal["base", "overlay"]
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_approved_requirement(self) -> "Requirement":
        if self.status == "APPROVED" and not self.audit_rationale_id:
            raise ValueError("APPROVED requirement must include audit_rationale_id")
        return self


class CreateRequirementRequest(BaseModel):
    title: str
    statement: str
    source_spec_ids: list[str]
    source_note_ids: list[str]
    compliance: Compliance = Field(default_factory=Compliance)
    variant_scope: Literal["base", "overlay"]


class PatchRequirementRequest(BaseModel):
    title: str | None = None
    statement: str | None = None
    compliance: Compliance | None = None
    audit_rationale_id: str | None = None


class TestRequirement(BaseModel):
    id: str
    artifact_type: Literal["test_requirement"] = "test_requirement"
    schema_version: str
    status: ArtifactStatus = "DRAFT"
    version: str
    statement: str
    source_requirement_ids: list[str]
    acceptance_criteria: list[str] = Field(default_factory=list)
    audit_rationale_id: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class CreateTestRequirementRequest(BaseModel):
    statement: str
    source_requirement_ids: list[str]
    acceptance_criteria: list[str] = Field(default_factory=list)
    audit_rationale_id: str | None = None


class CreateAuditRationaleRequest(BaseModel):
    artifact_id: str
    source_refs: list[AuditSourceRef]
    prompt_version: str
    model_version: str
    silver_refs: list[str] = Field(default_factory=list)


class SubmitReviewRequest(BaseModel):
    reviewer_id: str
    review_note: str | None = None


class ReviewRecord(BaseModel):
    id: str
    artifact_id: str
    decision: Literal["APPROVED", "REJECTED"]
    reviewer_id: str
    rejection_tags: list[
        Literal[
            "missing_constraint",
            "unclear_condition",
            "wrong_unit",
            "missing_trace",
            "safety_risk",
            "security_risk",
        ]
    ] = Field(default_factory=list)
    review_note: str | None = None
    reviewed_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_rejection_tags(self) -> "ReviewRecord":
        if self.decision == "REJECTED" and not self.rejection_tags:
            raise ValueError("REJECTED review must include rejection_tags")
        return self


class CreateReviewRequest(BaseModel):
    artifact_id: str
    decision: Literal["APPROVED", "REJECTED"]
    reviewer_id: str
    rejection_tags: list[
        Literal[
            "missing_constraint",
            "unclear_condition",
            "wrong_unit",
            "missing_trace",
            "safety_risk",
            "security_risk",
        ]
    ] = Field(default_factory=list)
    review_note: str | None = None

    @model_validator(mode="after")
    def validate_rejection_tags(self) -> "CreateReviewRequest":
        if self.decision == "REJECTED" and not self.rejection_tags:
            raise ValueError("REJECTED review must include rejection_tags")
        return self


class ReviewDecisionResponse(BaseModel):
    review: ReviewRecord
    artifact: Requirement


class SectionLock(BaseModel):
    section_key: str
    owner_id: str
    expires_at: datetime
    status: Literal["LOCKED"] = "LOCKED"


class LockRequest(BaseModel):
    owner_id: str
    ttl_minutes: int = Field(default=30, ge=1, le=30)

    def expires_at(self) -> datetime:
        return utc_now() + timedelta(minutes=self.ttl_minutes)


class LockConflictResponse(BaseModel):
    error: str
    current_lock: SectionLock


class TraceMapEntry(BaseModel):
    artifact_id: str
    artifact_type: str
    upstream_ids: list[str]
    downstream_ids: list[str]
    status: str
    version: str
    schema_version: str
    last_review_id: str | None = None
    audit_rationale_id: str | None = None


class CodebeamerExportRequest(BaseModel):
    requirement_id: str
    requested_by: str
    idempotency_key: str | None = None


class ExportJobResponse(BaseModel):
    job_id: str
    status: Literal["QUEUED", "RUNNING", "SUCCEEDED", "FAILED"] = "QUEUED"
    integration_log_id: str | None = None


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
