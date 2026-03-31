from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

from fastapi import HTTPException, status

from .models import (
    AuditRationale,
    CodebeamerExportRequest,
    ExportJobResponse,
    LockRequest,
    Note,
    Requirement,
    ReviewDecisionResponse,
    ReviewRecord,
    SectionLock,
    SpecSection,
    TestRequirement,
    TraceMapEntry,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def next_id(prefix: str) -> str:
    return f"{prefix}-{uuid4()}"


class Repository(Protocol):
    def upsert_spec_section(self, section: SpecSection) -> SpecSection: ...
    def list_spec_sections(self, status_filter: str | None, section_key: str | None) -> list[SpecSection]: ...
    def get_spec_section(self, spec_section_id: str) -> SpecSection: ...
    def create_note(self, note: Note) -> Note: ...
    def list_notes(self, status_filter: str | None, source_spec_id: str | None) -> list[Note]: ...
    def get_note(self, note_id: str) -> Note: ...
    def create_requirement(self, requirement: Requirement) -> Requirement: ...
    def list_requirements(self, status_filter: str | None, source_spec_id: str | None) -> list[Requirement]: ...
    def get_requirement(self, requirement_id: str) -> Requirement: ...
    def patch_requirement(self, requirement_id: str, title: str | None, statement: str | None, compliance, audit_rationale_id: str | None = None) -> Requirement: ...
    def submit_requirement_review(self, requirement_id: str) -> Requirement: ...
    def create_test_requirement(self, test_requirement: TestRequirement) -> TestRequirement: ...
    def list_test_requirements(self, status_filter: str | None, source_requirement_id: str | None) -> list[TestRequirement]: ...
    def get_test_requirement(self, test_requirement_id: str) -> TestRequirement: ...
    def patch_test_requirement(self, test_requirement_id: str, statement: str | None, acceptance_criteria: list[str] | None, audit_rationale_id: str | None = None) -> TestRequirement: ...
    def submit_test_requirement_review(self, test_requirement_id: str) -> TestRequirement: ...
    def create_audit_rationale(self, audit_rationale: AuditRationale) -> AuditRationale: ...
    def get_audit_rationale(self, audit_rationale_id: str) -> AuditRationale: ...
    def create_review(self, review: ReviewRecord) -> ReviewDecisionResponse: ...
    def get_review(self, review_id: str) -> ReviewRecord: ...
    def acquire_or_renew_lock(self, section_key: str, request: LockRequest) -> SectionLock: ...
    def release_lock(self, section_key: str, owner_id: str) -> None: ...
    def get_trace(self, artifact_id: str) -> TraceMapEntry: ...
    def export_requirement(self, request: CodebeamerExportRequest) -> ExportJobResponse: ...


class InMemoryRepository:
    def __init__(self) -> None:
        self.spec_sections: dict[str, SpecSection] = {}
        self.notes: dict[str, Note] = {}
        self.requirements: dict[str, Requirement] = {}
        self.test_requirements: dict[str, TestRequirement] = {}
        self.audit_rationales: dict[str, AuditRationale] = {}
        self.reviews: dict[str, ReviewRecord] = {}
        self.locks: dict[str, SectionLock] = {}
        self.trace_entries: dict[str, TraceMapEntry] = {}

    def upsert_spec_section(self, section: SpecSection) -> SpecSection:
        section.updated_at = utc_now()
        self.spec_sections[section.id] = section
        self.trace_entries[section.id] = TraceMapEntry(
            artifact_id=section.id,
            artifact_type=section.artifact_type,
            upstream_ids=[],
            downstream_ids=[],
            status=section.status,
            version=section.version,
            schema_version=section.schema_version,
        )
        return section

    def list_spec_sections(self, status_filter: str | None, section_key: str | None) -> list[SpecSection]:
        items = list(self.spec_sections.values())
        if status_filter:
            items = [item for item in items if item.status == status_filter]
        if section_key:
            items = [item for item in items if item.section_key == section_key]
        return items

    def get_spec_section(self, spec_section_id: str) -> SpecSection:
        item = self.spec_sections.get(spec_section_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spec section not found")
        return item

    def create_note(self, note: Note) -> Note:
        for source_spec_id in note.source_spec_ids:
            if source_spec_id not in self.spec_sections:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source spec section not found")
        self.notes[note.id] = note
        self.trace_entries[note.id] = TraceMapEntry(
            artifact_id=note.id,
            artifact_type=note.artifact_type,
            upstream_ids=note.source_spec_ids,
            downstream_ids=[],
            status=note.status,
            version=note.version,
            schema_version=note.schema_version,
        )
        return note

    def list_notes(self, status_filter: str | None, source_spec_id: str | None) -> list[Note]:
        items = list(self.notes.values())
        if status_filter:
            items = [item for item in items if item.status == status_filter]
        if source_spec_id:
            items = [item for item in items if source_spec_id in item.source_spec_ids]
        return items

    def get_note(self, note_id: str) -> Note:
        item = self.notes.get(note_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
        return item

    def create_requirement(self, requirement: Requirement) -> Requirement:
        for source_note_id in requirement.source_note_ids:
            if source_note_id not in self.notes:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source note not found")
        self.requirements[requirement.id] = requirement
        self.trace_entries[requirement.id] = TraceMapEntry(
            artifact_id=requirement.id,
            artifact_type=requirement.artifact_type,
            upstream_ids=requirement.source_spec_ids + requirement.source_note_ids,
            downstream_ids=requirement.trace.downstream_test_requirement_ids,
            status=requirement.status,
            version=requirement.version,
            schema_version=requirement.schema_version,
            audit_rationale_id=requirement.audit_rationale_id,
        )
        return requirement

    def list_requirements(self, status_filter: str | None, source_spec_id: str | None) -> list[Requirement]:
        items = list(self.requirements.values())
        if status_filter:
            items = [item for item in items if item.status == status_filter]
        if source_spec_id:
            items = [item for item in items if source_spec_id in item.source_spec_ids]
        return items

    def get_requirement(self, requirement_id: str) -> Requirement:
        item = self.requirements.get(requirement_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found")
        return item

    def patch_requirement(
        self,
        requirement_id: str,
        title: str | None,
        statement: str | None,
        compliance,
        audit_rationale_id: str | None = None,
    ) -> Requirement:
        item = self.get_requirement(requirement_id)
        if item.status == "APPROVED":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="APPROVED requirement cannot be patched")
        if title is not None:
            item.title = title
        if statement is not None:
            item.statement = statement
        if compliance is not None:
            item.compliance = compliance
        if audit_rationale_id is not None:
            if audit_rationale_id not in self.audit_rationales:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit rationale not found")
            item.audit_rationale_id = audit_rationale_id
        item.updated_at = utc_now()
        trace_entry = self.trace_entries[requirement_id]
        trace_entry.status = item.status
        trace_entry.audit_rationale_id = item.audit_rationale_id
        self.trace_entries[requirement_id] = trace_entry
        return item

    def submit_requirement_review(self, requirement_id: str) -> Requirement:
        item = self.get_requirement(requirement_id)
        if item.status != "DRAFT":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only DRAFT requirement can enter review")
        item.status = "IN_REVIEW"
        item.updated_at = utc_now()
        self.trace_entries[requirement_id].status = item.status
        return item

    def create_test_requirement(self, test_requirement: TestRequirement) -> TestRequirement:
        for source_requirement_id in test_requirement.source_requirement_ids:
            requirement = self.requirements.get(source_requirement_id)
            if not requirement:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source requirement not found")
        if test_requirement.audit_rationale_id is not None and test_requirement.audit_rationale_id not in self.audit_rationales:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit rationale not found")
        self.test_requirements[test_requirement.id] = test_requirement
        self.trace_entries[test_requirement.id] = TraceMapEntry(
            artifact_id=test_requirement.id,
            artifact_type=test_requirement.artifact_type,
            upstream_ids=test_requirement.source_requirement_ids,
            downstream_ids=[],
            status=test_requirement.status,
            version=test_requirement.version,
            schema_version=test_requirement.schema_version,
            audit_rationale_id=test_requirement.audit_rationale_id,
        )
        for source_requirement_id in test_requirement.source_requirement_ids:
            requirement = self.requirements[source_requirement_id]
            if test_requirement.id not in requirement.trace.downstream_test_requirement_ids:
                requirement.trace.downstream_test_requirement_ids.append(test_requirement.id)
                self.trace_entries[source_requirement_id].downstream_ids = requirement.trace.downstream_test_requirement_ids
        return test_requirement

    def list_test_requirements(self, status_filter: str | None, source_requirement_id: str | None) -> list[TestRequirement]:
        items = list(self.test_requirements.values())
        if status_filter:
            items = [item for item in items if item.status == status_filter]
        if source_requirement_id:
            items = [item for item in items if source_requirement_id in item.source_requirement_ids]
        return items

    def get_test_requirement(self, test_requirement_id: str) -> TestRequirement:
        item = self.test_requirements.get(test_requirement_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test requirement not found")
        return item

    def patch_test_requirement(
        self,
        test_requirement_id: str,
        statement: str | None,
        acceptance_criteria: list[str] | None,
        audit_rationale_id: str | None = None,
    ) -> TestRequirement:
        item = self.get_test_requirement(test_requirement_id)
        if item.status == "APPROVED":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="APPROVED test requirement cannot be patched")
        if statement is not None:
            item.statement = statement
        if acceptance_criteria is not None:
            item.acceptance_criteria = acceptance_criteria
        if audit_rationale_id is not None:
            if audit_rationale_id not in self.audit_rationales:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit rationale not found")
            item.audit_rationale_id = audit_rationale_id
        item.updated_at = utc_now()
        trace_entry = self.trace_entries[test_requirement_id]
        trace_entry.status = item.status
        trace_entry.audit_rationale_id = item.audit_rationale_id
        self.trace_entries[test_requirement_id] = trace_entry
        return item

    def submit_test_requirement_review(self, test_requirement_id: str) -> TestRequirement:
        item = self.get_test_requirement(test_requirement_id)
        if item.status != "DRAFT":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only DRAFT test requirement can enter review")
        item.status = "IN_REVIEW"
        item.updated_at = utc_now()
        self.trace_entries[test_requirement_id].status = item.status
        return item

    def create_audit_rationale(self, audit_rationale: AuditRationale) -> AuditRationale:
        if audit_rationale.artifact_id not in self.requirements and audit_rationale.artifact_id not in self.test_requirements:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found for audit rationale")
        self.audit_rationales[audit_rationale.id] = audit_rationale
        return audit_rationale

    def get_audit_rationale(self, audit_rationale_id: str) -> AuditRationale:
        item = self.audit_rationales.get(audit_rationale_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit rationale not found")
        return item

    def create_review(self, review: ReviewRecord) -> ReviewDecisionResponse:
        requirement = self.requirements.get(review.artifact_id)
        if requirement:
            if requirement.status != "IN_REVIEW":
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Requirement must be IN_REVIEW")
            if review.decision == "APPROVED" and not requirement.audit_rationale_id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="APPROVED requirement requires audit_rationale_id")
            requirement.status = review.decision
            requirement.updated_at = utc_now()
            artifact: Requirement | TestRequirement = requirement
        else:
            test_requirement = self.test_requirements.get(review.artifact_id)
            if not test_requirement:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review target not found")
            if test_requirement.status != "IN_REVIEW":
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Test requirement must be IN_REVIEW")
            if review.decision == "APPROVED" and not test_requirement.audit_rationale_id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="APPROVED test requirement requires audit_rationale_id")
            test_requirement.status = review.decision
            test_requirement.updated_at = utc_now()
            artifact = test_requirement

        self.reviews[review.id] = review
        trace = self.trace_entries[review.artifact_id]
        trace.status = artifact.status
        trace.last_review_id = review.id
        trace.audit_rationale_id = artifact.audit_rationale_id
        return ReviewDecisionResponse(review=review, artifact=artifact)

    def get_review(self, review_id: str) -> ReviewRecord:
        item = self.reviews.get(review_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
        return item

    def acquire_or_renew_lock(self, section_key: str, request: LockRequest) -> SectionLock:
        current = self.locks.get(section_key)
        now = utc_now()
        if current and current.expires_at > now and current.owner_id != request.owner_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "Lock conflict", "current_lock": current.model_dump(mode="json")},
            )
        lock = SectionLock(section_key=section_key, owner_id=request.owner_id, expires_at=request.expires_at())
        self.locks[section_key] = lock
        return lock

    def release_lock(self, section_key: str, owner_id: str) -> None:
        current = self.locks.get(section_key)
        if not current:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lock not found")
        if current.owner_id != owner_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only lock owner can release lock")
        del self.locks[section_key]

    def get_trace(self, artifact_id: str) -> TraceMapEntry:
        item = self.trace_entries.get(artifact_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trace entry not found")
        return item

    def export_requirement(self, request: CodebeamerExportRequest) -> ExportJobResponse:
        requirement = self.get_requirement(request.requirement_id)
        if requirement.status != "APPROVED":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only APPROVED requirements can be exported")
        return ExportJobResponse(job_id=f"export-{uuid4()}", status="QUEUED", integration_log_id=f"log-{uuid4()}")


class SQLiteRepository:
    def __init__(self, db_path: str | Path = "specops.db") -> None:
        self.db_path = Path(db_path)
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        cursor = self.connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS spec_sections (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS notes (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS requirements (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS test_requirements (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS audit_rationales (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS reviews (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS locks (section_key TEXT PRIMARY KEY, payload TEXT NOT NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS trace_entries (artifact_id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
        self.connection.commit()

    def _save_model(self, table: str, key_field: str, key: str, model) -> None:
        payload = model.model_dump_json()
        self.connection.execute(
            f"INSERT OR REPLACE INTO {table} ({key_field}, payload) VALUES (?, ?)",
            (key, payload),
        )
        self.connection.commit()

    def _load_model(self, table: str, key_field: str, key: str, model_cls):
        row = self.connection.execute(
            f"SELECT payload FROM {table} WHERE {key_field} = ?",
            (key,),
        ).fetchone()
        if not row:
            return None
        return model_cls.model_validate_json(row["payload"])

    def _load_all(self, table: str, model_cls) -> list[Any]:
        rows = self.connection.execute(f"SELECT payload FROM {table}").fetchall()
        return [model_cls.model_validate_json(row["payload"]) for row in rows]

    def upsert_spec_section(self, section: SpecSection) -> SpecSection:
        section.updated_at = utc_now()
        self._save_model("spec_sections", "id", section.id, section)
        trace_entry = TraceMapEntry(
            artifact_id=section.id,
            artifact_type=section.artifact_type,
            upstream_ids=[],
            downstream_ids=[],
            status=section.status,
            version=section.version,
            schema_version=section.schema_version,
        )
        self._save_model("trace_entries", "artifact_id", section.id, trace_entry)
        return section

    def list_spec_sections(self, status_filter: str | None, section_key: str | None) -> list[SpecSection]:
        items = self._load_all("spec_sections", SpecSection)
        if status_filter:
            items = [item for item in items if item.status == status_filter]
        if section_key:
            items = [item for item in items if item.section_key == section_key]
        return items

    def get_spec_section(self, spec_section_id: str) -> SpecSection:
        item = self._load_model("spec_sections", "id", spec_section_id, SpecSection)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spec section not found")
        return item

    def create_note(self, note: Note) -> Note:
        for source_spec_id in note.source_spec_ids:
            self.get_spec_section(source_spec_id)
        self._save_model("notes", "id", note.id, note)
        trace_entry = TraceMapEntry(
            artifact_id=note.id,
            artifact_type=note.artifact_type,
            upstream_ids=note.source_spec_ids,
            downstream_ids=[],
            status=note.status,
            version=note.version,
            schema_version=note.schema_version,
        )
        self._save_model("trace_entries", "artifact_id", note.id, trace_entry)
        return note

    def list_notes(self, status_filter: str | None, source_spec_id: str | None) -> list[Note]:
        items = self._load_all("notes", Note)
        if status_filter:
            items = [item for item in items if item.status == status_filter]
        if source_spec_id:
            items = [item for item in items if source_spec_id in item.source_spec_ids]
        return items

    def get_note(self, note_id: str) -> Note:
        item = self._load_model("notes", "id", note_id, Note)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
        return item

    def create_requirement(self, requirement: Requirement) -> Requirement:
        for source_note_id in requirement.source_note_ids:
            self.get_note(source_note_id)
        self._save_model("requirements", "id", requirement.id, requirement)
        trace_entry = TraceMapEntry(
            artifact_id=requirement.id,
            artifact_type=requirement.artifact_type,
            upstream_ids=requirement.source_spec_ids + requirement.source_note_ids,
            downstream_ids=requirement.trace.downstream_test_requirement_ids,
            status=requirement.status,
            version=requirement.version,
            schema_version=requirement.schema_version,
            audit_rationale_id=requirement.audit_rationale_id,
        )
        self._save_model("trace_entries", "artifact_id", requirement.id, trace_entry)
        return requirement

    def list_requirements(self, status_filter: str | None, source_spec_id: str | None) -> list[Requirement]:
        items = self._load_all("requirements", Requirement)
        if status_filter:
            items = [item for item in items if item.status == status_filter]
        if source_spec_id:
            items = [item for item in items if source_spec_id in item.source_spec_ids]
        return items

    def get_requirement(self, requirement_id: str) -> Requirement:
        item = self._load_model("requirements", "id", requirement_id, Requirement)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found")
        return item

    def patch_requirement(
        self,
        requirement_id: str,
        title: str | None,
        statement: str | None,
        compliance,
        audit_rationale_id: str | None = None,
    ) -> Requirement:
        item = self.get_requirement(requirement_id)
        if item.status == "APPROVED":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="APPROVED requirement cannot be patched")
        if title is not None:
            item.title = title
        if statement is not None:
            item.statement = statement
        if compliance is not None:
            item.compliance = compliance
        if audit_rationale_id is not None:
            if not self._load_model("audit_rationales", "id", audit_rationale_id, AuditRationale):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit rationale not found")
            item.audit_rationale_id = audit_rationale_id
        item.updated_at = utc_now()
        self._save_model("requirements", "id", requirement_id, item)
        trace = self.get_trace(requirement_id)
        trace.status = item.status
        trace.audit_rationale_id = item.audit_rationale_id
        self._save_model("trace_entries", "artifact_id", requirement_id, trace)
        return item

    def submit_requirement_review(self, requirement_id: str) -> Requirement:
        item = self.get_requirement(requirement_id)
        if item.status != "DRAFT":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only DRAFT requirement can enter review")
        item.status = "IN_REVIEW"
        item.updated_at = utc_now()
        self._save_model("requirements", "id", requirement_id, item)
        trace = self.get_trace(requirement_id)
        trace.status = item.status
        self._save_model("trace_entries", "artifact_id", requirement_id, trace)
        return item

    def create_test_requirement(self, test_requirement: TestRequirement) -> TestRequirement:
        for source_requirement_id in test_requirement.source_requirement_ids:
            requirement = self.get_requirement(source_requirement_id)
            if test_requirement.id not in requirement.trace.downstream_test_requirement_ids:
                requirement.trace.downstream_test_requirement_ids.append(test_requirement.id)
                self._save_model("requirements", "id", requirement.id, requirement)
                trace = self.get_trace(requirement.id)
                trace.downstream_ids = requirement.trace.downstream_test_requirement_ids
                self._save_model("trace_entries", "artifact_id", requirement.id, trace)
        if test_requirement.audit_rationale_id is not None and not self._load_model("audit_rationales", "id", test_requirement.audit_rationale_id, AuditRationale):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit rationale not found")
        self._save_model("test_requirements", "id", test_requirement.id, test_requirement)
        trace_entry = TraceMapEntry(
            artifact_id=test_requirement.id,
            artifact_type=test_requirement.artifact_type,
            upstream_ids=test_requirement.source_requirement_ids,
            downstream_ids=[],
            status=test_requirement.status,
            version=test_requirement.version,
            schema_version=test_requirement.schema_version,
            audit_rationale_id=test_requirement.audit_rationale_id,
        )
        self._save_model("trace_entries", "artifact_id", test_requirement.id, trace_entry)
        return test_requirement

    def list_test_requirements(self, status_filter: str | None, source_requirement_id: str | None) -> list[TestRequirement]:
        items = self._load_all("test_requirements", TestRequirement)
        if status_filter:
            items = [item for item in items if item.status == status_filter]
        if source_requirement_id:
            items = [item for item in items if source_requirement_id in item.source_requirement_ids]
        return items

    def get_test_requirement(self, test_requirement_id: str) -> TestRequirement:
        item = self._load_model("test_requirements", "id", test_requirement_id, TestRequirement)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test requirement not found")
        return item

    def patch_test_requirement(
        self,
        test_requirement_id: str,
        statement: str | None,
        acceptance_criteria: list[str] | None,
        audit_rationale_id: str | None = None,
    ) -> TestRequirement:
        item = self.get_test_requirement(test_requirement_id)
        if item.status == "APPROVED":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="APPROVED test requirement cannot be patched")
        if statement is not None:
            item.statement = statement
        if acceptance_criteria is not None:
            item.acceptance_criteria = acceptance_criteria
        if audit_rationale_id is not None:
            if not self._load_model("audit_rationales", "id", audit_rationale_id, AuditRationale):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit rationale not found")
            item.audit_rationale_id = audit_rationale_id
        item.updated_at = utc_now()
        self._save_model("test_requirements", "id", test_requirement_id, item)
        trace = self.get_trace(test_requirement_id)
        trace.status = item.status
        trace.audit_rationale_id = item.audit_rationale_id
        self._save_model("trace_entries", "artifact_id", test_requirement_id, trace)
        return item

    def submit_test_requirement_review(self, test_requirement_id: str) -> TestRequirement:
        item = self.get_test_requirement(test_requirement_id)
        if item.status != "DRAFT":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only DRAFT test requirement can enter review")
        item.status = "IN_REVIEW"
        item.updated_at = utc_now()
        self._save_model("test_requirements", "id", test_requirement_id, item)
        trace = self.get_trace(test_requirement_id)
        trace.status = item.status
        self._save_model("trace_entries", "artifact_id", test_requirement_id, trace)
        return item

    def create_audit_rationale(self, audit_rationale: AuditRationale) -> AuditRationale:
        if (
            not self._load_model("requirements", "id", audit_rationale.artifact_id, Requirement)
            and not self._load_model("test_requirements", "id", audit_rationale.artifact_id, TestRequirement)
        ):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found for audit rationale")
        self._save_model("audit_rationales", "id", audit_rationale.id, audit_rationale)
        return audit_rationale

    def get_audit_rationale(self, audit_rationale_id: str) -> AuditRationale:
        item = self._load_model("audit_rationales", "id", audit_rationale_id, AuditRationale)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit rationale not found")
        return item

    def create_review(self, review: ReviewRecord) -> ReviewDecisionResponse:
        requirement = self._load_model("requirements", "id", review.artifact_id, Requirement)
        if requirement:
            if requirement.status != "IN_REVIEW":
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Requirement must be IN_REVIEW")
            if review.decision == "APPROVED" and not requirement.audit_rationale_id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="APPROVED requirement requires audit_rationale_id")
            requirement.status = review.decision
            requirement.updated_at = utc_now()
            self._save_model("requirements", "id", requirement.id, requirement)
            artifact: Requirement | TestRequirement = requirement
        else:
            test_requirement = self._load_model("test_requirements", "id", review.artifact_id, TestRequirement)
            if not test_requirement:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review target not found")
            if test_requirement.status != "IN_REVIEW":
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Test requirement must be IN_REVIEW")
            if review.decision == "APPROVED" and not test_requirement.audit_rationale_id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="APPROVED test requirement requires audit_rationale_id")
            test_requirement.status = review.decision
            test_requirement.updated_at = utc_now()
            self._save_model("test_requirements", "id", test_requirement.id, test_requirement)
            artifact = test_requirement

        self._save_model("reviews", "id", review.id, review)
        trace = self.get_trace(review.artifact_id)
        trace.status = artifact.status
        trace.last_review_id = review.id
        trace.audit_rationale_id = artifact.audit_rationale_id
        self._save_model("trace_entries", "artifact_id", review.artifact_id, trace)
        return ReviewDecisionResponse(review=review, artifact=artifact)

    def get_review(self, review_id: str) -> ReviewRecord:
        item = self._load_model("reviews", "id", review_id, ReviewRecord)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
        return item

    def acquire_or_renew_lock(self, section_key: str, request: LockRequest) -> SectionLock:
        current = self._load_model("locks", "section_key", section_key, SectionLock)
        now = utc_now()
        if current and current.expires_at > now and current.owner_id != request.owner_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "Lock conflict", "current_lock": current.model_dump(mode="json")},
            )
        lock = SectionLock(section_key=section_key, owner_id=request.owner_id, expires_at=request.expires_at())
        self._save_model("locks", "section_key", section_key, lock)
        return lock

    def release_lock(self, section_key: str, owner_id: str) -> None:
        current = self._load_model("locks", "section_key", section_key, SectionLock)
        if not current:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lock not found")
        if current.owner_id != owner_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only lock owner can release lock")
        self.connection.execute("DELETE FROM locks WHERE section_key = ?", (section_key,))
        self.connection.commit()

    def get_trace(self, artifact_id: str) -> TraceMapEntry:
        item = self._load_model("trace_entries", "artifact_id", artifact_id, TraceMapEntry)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trace entry not found")
        return item

    def export_requirement(self, request: CodebeamerExportRequest) -> ExportJobResponse:
        requirement = self.get_requirement(request.requirement_id)
        if requirement.status != "APPROVED":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only APPROVED requirements can be exported")
        return ExportJobResponse(job_id=f"export-{uuid4()}", status="QUEUED", integration_log_id=f"log-{uuid4()}")

from .sqlite_repository_relational import SQLiteRepository as SQLiteRepository


repository = SQLiteRepository()
