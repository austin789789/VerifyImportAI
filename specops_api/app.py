from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.responses import JSONResponse

from .models import (
    AuditRationale,
    CodebeamerExportRequest,
    CreateAuditRationaleRequest,
    CreateNoteRequest,
    CreateRequirementRequest,
    CreateReviewRequest,
    CreateTestRequirementRequest,
    LockConflictResponse,
    LockRequest,
    Note,
    PatchRequirementRequest,
    Requirement,
    RequirementTrace,
    ReviewRecord,
    SpecSection,
    SubmitReviewRequest,
    TestRequirement,
)
from .repository import InMemoryRepository, Repository, next_id, repository as default_repository


def create_app(repository: Repository | None = None) -> FastAPI:
    repo = repository or default_repository
    app = FastAPI(
        title="SpecOps MVP API",
        version="1.3.0",
        summary="MVP API contract for SpecOps workflows",
    )

    def get_repository() -> Repository:
        return repo

    @app.get("/health")
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/spec-sections", response_model=SpecSection, status_code=status.HTTP_201_CREATED)
    def upsert_spec_section(section: SpecSection, repository: Repository = Depends(get_repository)) -> SpecSection:
        return repository.upsert_spec_section(section)

    @app.get("/spec-sections", response_model=dict[str, list[SpecSection]])
    def list_spec_sections(
        status: str | None = Query(default=None),
        section_key: str | None = Query(default=None),
        repository: Repository = Depends(get_repository),
    ) -> dict[str, list[SpecSection]]:
        return {"items": repository.list_spec_sections(status, section_key)}

    @app.get("/spec-sections/{spec_section_id}", response_model=SpecSection)
    def get_spec_section(spec_section_id: str, repository: Repository = Depends(get_repository)) -> SpecSection:
        return repository.get_spec_section(spec_section_id)

    @app.post("/notes", response_model=Note, status_code=status.HTTP_201_CREATED)
    def create_note(
        request: CreateNoteRequest,
        repository: Repository = Depends(get_repository),
    ) -> Note:
        note = Note(
            id=next_id("N"),
            schema_version="1.0.0",
            version="v1.0",
            title=request.title,
            summary=request.summary,
            source_spec_ids=request.source_spec_ids,
        )
        return repository.create_note(note)

    @app.get("/notes", response_model=dict[str, list[Note]])
    def list_notes(
        status: str | None = Query(default=None),
        source_spec_id: str | None = Query(default=None),
        repository: Repository = Depends(get_repository),
    ) -> dict[str, list[Note]]:
        return {"items": repository.list_notes(status, source_spec_id)}

    @app.get("/notes/{note_id}", response_model=Note)
    def get_note(note_id: str, repository: Repository = Depends(get_repository)) -> Note:
        return repository.get_note(note_id)

    @app.post("/requirements", response_model=Requirement, status_code=status.HTTP_201_CREATED)
    def create_requirement(
        request: CreateRequirementRequest,
        repository: Repository = Depends(get_repository),
    ) -> Requirement:
        requirement = Requirement(
            id=next_id("R"),
            schema_version="1.0.0",
            version="v1.0",
            title=request.title,
            statement=request.statement,
            source_spec_ids=request.source_spec_ids,
            source_note_ids=request.source_note_ids,
            compliance=request.compliance,
            trace=RequirementTrace(graph_node_id=next_id("GN")),
            variant_scope=request.variant_scope,
        )
        return repository.create_requirement(requirement)

    @app.get("/requirements", response_model=dict[str, list[Requirement]])
    def list_requirements(
        status: str | None = Query(default=None),
        source_spec_id: str | None = Query(default=None),
        review_queue: str | None = Query(default=None),
        repository: Repository = Depends(get_repository),
    ) -> dict[str, list[Requirement]]:
        items = repository.list_requirements(status, source_spec_id)
        if review_queue == "impacted":
            items = [item for item in items if item.status == "IMPACTED"]
        elif review_queue == "manual_recovery":
            items = [item for item in items if item.status == "MANUAL_RECOVERY"]
        elif review_queue == "pending_review":
            items = [item for item in items if item.status == "IN_REVIEW"]
        return {"items": items}

    @app.get("/requirements/{requirement_id}", response_model=Requirement)
    def get_requirement(requirement_id: str, repository: Repository = Depends(get_repository)) -> Requirement:
        return repository.get_requirement(requirement_id)

    @app.patch("/requirements/{requirement_id}", response_model=Requirement)
    def patch_requirement(
        requirement_id: str,
        request: PatchRequirementRequest,
        repository: Repository = Depends(get_repository),
    ) -> Requirement:
        return repository.patch_requirement(
            requirement_id,
            request.title,
            request.statement,
            request.compliance,
            request.audit_rationale_id,
        )

    @app.post("/test-requirements", response_model=TestRequirement, status_code=status.HTTP_201_CREATED)
    def create_test_requirement(
        request: CreateTestRequirementRequest,
        repository: Repository = Depends(get_repository),
    ) -> TestRequirement:
        test_requirement = TestRequirement(
            id=next_id("T"),
            schema_version="1.0.0",
            version="v1.0",
            statement=request.statement,
            source_requirement_ids=request.source_requirement_ids,
            acceptance_criteria=request.acceptance_criteria,
            audit_rationale_id=request.audit_rationale_id,
        )
        return repository.create_test_requirement(test_requirement)

    @app.get("/test-requirements", response_model=dict[str, list[TestRequirement]])
    def list_test_requirements(
        status: str | None = Query(default=None),
        source_requirement_id: str | None = Query(default=None),
        repository: Repository = Depends(get_repository),
    ) -> dict[str, list[TestRequirement]]:
        return {"items": repository.list_test_requirements(status, source_requirement_id)}

    @app.get("/test-requirements/{test_requirement_id}", response_model=TestRequirement)
    def get_test_requirement(
        test_requirement_id: str,
        repository: Repository = Depends(get_repository),
    ) -> TestRequirement:
        return repository.get_test_requirement(test_requirement_id)

    @app.post("/audit-rationales", response_model=AuditRationale, status_code=status.HTTP_201_CREATED)
    def create_audit_rationale(
        request: CreateAuditRationaleRequest,
        repository: Repository = Depends(get_repository),
    ) -> AuditRationale:
        audit_rationale = AuditRationale(
            id=next_id("AR"),
            artifact_id=request.artifact_id,
            source_refs=request.source_refs,
            prompt_version=request.prompt_version,
            model_version=request.model_version,
            silver_refs=request.silver_refs,
        )
        return repository.create_audit_rationale(audit_rationale)

    @app.get("/audit-rationales/{audit_rationale_id}", response_model=AuditRationale)
    def get_audit_rationale(
        audit_rationale_id: str,
        repository: Repository = Depends(get_repository),
    ) -> AuditRationale:
        return repository.get_audit_rationale(audit_rationale_id)

    @app.post("/requirements/{requirement_id}/submit-review", response_model=Requirement)
    def submit_requirement_review(
        requirement_id: str,
        request: SubmitReviewRequest,
        repository: Repository = Depends(get_repository),
    ) -> Requirement:
        _ = request
        return repository.submit_requirement_review(requirement_id)

    @app.post("/reviews", status_code=status.HTTP_201_CREATED)
    def create_review(
        request: CreateReviewRequest,
        repository: Repository = Depends(get_repository),
    ):
        review = ReviewRecord(
            id=next_id("RV"),
            artifact_id=request.artifact_id,
            decision=request.decision,
            reviewer_id=request.reviewer_id,
            rejection_tags=request.rejection_tags,
            review_note=request.review_note,
        )
        return repository.create_review(review)

    @app.get("/reviews/{review_id}", response_model=ReviewRecord)
    def get_review(review_id: str, repository: Repository = Depends(get_repository)) -> ReviewRecord:
        return repository.get_review(review_id)

    @app.post("/locks/{section_key}")
    def acquire_or_renew_lock(
        section_key: str,
        request: LockRequest,
        repository: Repository = Depends(get_repository),
    ):
        try:
            return repository.acquire_or_renew_lock(section_key, request)
        except HTTPException as exc:
            if exc.status_code == status.HTTP_409_CONFLICT and isinstance(exc.detail, dict):
                payload = LockConflictResponse(**exc.detail)
                return JSONResponse(status_code=409, content=payload.model_dump(mode="json"))
            raise

    @app.delete("/locks/{section_key}", status_code=status.HTTP_204_NO_CONTENT)
    def release_lock(
        section_key: str,
        owner_id: str = Query(...),
        repository: Repository = Depends(get_repository),
    ) -> Response:
        repository.release_lock(section_key, owner_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.get("/trace/{artifact_id}")
    def get_trace(artifact_id: str, repository: Repository = Depends(get_repository)):
        return repository.get_trace(artifact_id)

    @app.post("/exports/codebeamer")
    def export_requirement_to_codebeamer(
        request: CodebeamerExportRequest,
        repository: Repository = Depends(get_repository),
    ):
        return repository.export_requirement(request)

    return app


app = create_app(default_repository)

__all__ = ["app", "create_app", "InMemoryRepository"]
