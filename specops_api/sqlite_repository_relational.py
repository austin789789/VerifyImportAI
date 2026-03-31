from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status

from .models import (
    AuditRationale,
    CodebeamerExportRequest,
    ExportJobResponse,
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


class SQLiteRepository:
    def __init__(self, db_path: str | Path = "specops.db") -> None:
        self.db_path = Path(db_path)
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        legacy_payloads = self._load_legacy_payload_data() if self._uses_legacy_payload_schema() else None
        if legacy_payloads is not None:
            self._drop_all_tables()
        self._create_tables()
        if legacy_payloads is not None:
            self._restore_legacy_payload_data(legacy_payloads)

    def _table_columns(self, table: str) -> set[str]:
        rows = self.connection.execute(f"PRAGMA table_info({table})").fetchall()
        return {row["name"] for row in rows}

    def _uses_legacy_payload_schema(self) -> bool:
        return self._table_columns("requirements") == {"id", "payload"}

    def _create_tables(self) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS spec_sections (
                id TEXT PRIMARY KEY,
                artifact_type TEXT NOT NULL,
                schema_version TEXT NOT NULL,
                status TEXT NOT NULL,
                version TEXT NOT NULL,
                section_key TEXT NOT NULL,
                title TEXT NOT NULL,
                text TEXT NOT NULL,
                normalized_text TEXT,
                parser_warnings_json TEXT NOT NULL,
                source_refs_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id TEXT PRIMARY KEY,
                artifact_type TEXT NOT NULL,
                schema_version TEXT NOT NULL,
                status TEXT NOT NULL,
                version TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS note_source_specs (
                note_id TEXT NOT NULL,
                spec_id TEXT NOT NULL,
                position INTEGER NOT NULL,
                PRIMARY KEY (note_id, spec_id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS requirements (
                id TEXT PRIMARY KEY,
                artifact_type TEXT NOT NULL,
                schema_version TEXT NOT NULL,
                status TEXT NOT NULL,
                version TEXT NOT NULL,
                title TEXT NOT NULL,
                statement TEXT NOT NULL,
                classes_json TEXT NOT NULL,
                asil TEXT,
                cal TEXT,
                graph_node_id TEXT NOT NULL,
                variant_scope TEXT NOT NULL,
                audit_rationale_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS requirement_source_specs (
                requirement_id TEXT NOT NULL,
                spec_id TEXT NOT NULL,
                position INTEGER NOT NULL,
                PRIMARY KEY (requirement_id, spec_id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS requirement_source_notes (
                requirement_id TEXT NOT NULL,
                note_id TEXT NOT NULL,
                position INTEGER NOT NULL,
                PRIMARY KEY (requirement_id, note_id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS test_requirements (
                id TEXT PRIMARY KEY,
                artifact_type TEXT NOT NULL,
                schema_version TEXT NOT NULL,
                status TEXT NOT NULL,
                version TEXT NOT NULL,
                statement TEXT NOT NULL,
                acceptance_criteria_json TEXT NOT NULL,
                audit_rationale_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS test_requirement_sources (
                test_requirement_id TEXT NOT NULL,
                requirement_id TEXT NOT NULL,
                position INTEGER NOT NULL,
                PRIMARY KEY (test_requirement_id, requirement_id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_rationales (
                id TEXT PRIMARY KEY,
                artifact_id TEXT NOT NULL,
                source_refs_json TEXT NOT NULL,
                prompt_version TEXT NOT NULL,
                model_version TEXT NOT NULL,
                silver_refs_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS reviews (
                id TEXT PRIMARY KEY,
                artifact_id TEXT NOT NULL,
                decision TEXT NOT NULL,
                reviewer_id TEXT NOT NULL,
                rejection_tags_json TEXT NOT NULL,
                review_note TEXT,
                reviewed_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS locks (
                section_key TEXT PRIMARY KEY,
                owner_id TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                status TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS trace_entries (
                artifact_id TEXT PRIMARY KEY,
                artifact_type TEXT NOT NULL,
                status TEXT NOT NULL,
                version TEXT NOT NULL,
                schema_version TEXT NOT NULL,
                last_review_id TEXT,
                audit_rationale_id TEXT
            )
            """
        )
        self.connection.commit()

    def _drop_all_tables(self) -> None:
        tables = [
            "trace_entries",
            "locks",
            "reviews",
            "audit_rationales",
            "test_requirement_sources",
            "test_requirements",
            "requirement_source_notes",
            "requirement_source_specs",
            "requirements",
            "note_source_specs",
            "notes",
            "spec_sections",
        ]
        for table in tables:
            self.connection.execute(f"DROP TABLE IF EXISTS {table}")
        self.connection.commit()

    def _load_legacy_payload_data(self) -> dict[str, list[Any]]:
        def load(table: str, model_cls) -> list[Any]:
            rows = self.connection.execute(f"SELECT payload FROM {table}").fetchall()
            return [model_cls.model_validate_json(row["payload"]) for row in rows]

        return {
            "spec_sections": load("spec_sections", SpecSection),
            "notes": load("notes", Note),
            "requirements": load("requirements", Requirement),
            "test_requirements": load("test_requirements", TestRequirement),
            "audit_rationales": load("audit_rationales", AuditRationale),
            "reviews": load("reviews", ReviewRecord),
            "locks": load("locks", SectionLock),
            "trace_entries": load("trace_entries", TraceMapEntry),
        }

    def _restore_legacy_payload_data(self, legacy_payloads: dict[str, list[Any]]) -> None:
        for section in legacy_payloads["spec_sections"]:
            self._persist_spec_section(section)
        for note in legacy_payloads["notes"]:
            self._persist_note(note)
        for requirement in legacy_payloads["requirements"]:
            self._persist_requirement(requirement)
        for test_requirement in legacy_payloads["test_requirements"]:
            self._persist_test_requirement(test_requirement)
        for audit_rationale in legacy_payloads["audit_rationales"]:
            self._persist_audit_rationale(audit_rationale)
        for review in legacy_payloads["reviews"]:
            self._persist_review(review)
        for lock in legacy_payloads["locks"]:
            self._persist_lock(lock)
        for trace_entry in legacy_payloads["trace_entries"]:
            self._persist_trace_entry(trace_entry)
        self.connection.commit()

    def _json_dump(self, value: Any) -> str:
        return json.dumps(value, separators=(",", ":"))

    def _json_load(self, value: str) -> Any:
        return json.loads(value)

    def _row_or_none(self, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
        return self.connection.execute(sql, params).fetchone()

    def _rows(self, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        return list(self.connection.execute(sql, params).fetchall())

    def _replace_links(self, table: str, left_column: str, right_column: str, left_id: str, values: list[str]) -> None:
        self.connection.execute(f"DELETE FROM {table} WHERE {left_column} = ?", (left_id,))
        for position, value in enumerate(values):
            self.connection.execute(
                f"INSERT INTO {table} ({left_column}, {right_column}, position) VALUES (?, ?, ?)",
                (left_id, value, position),
            )

    def _linked_ids(self, table: str, left_column: str, right_column: str, left_id: str) -> list[str]:
        rows = self._rows(
            f"SELECT {right_column} FROM {table} WHERE {left_column} = ? ORDER BY position",
            (left_id,),
        )
        return [row[right_column] for row in rows]

    def _persist_spec_section(self, section: SpecSection) -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO spec_sections (
                id, artifact_type, schema_version, status, version, section_key, title, text,
                normalized_text, parser_warnings_json, source_refs_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                section.id,
                section.artifact_type,
                section.schema_version,
                section.status,
                section.version,
                section.section_key,
                section.title,
                section.text,
                section.normalized_text,
                self._json_dump(section.parser_warnings),
                self._json_dump([ref.model_dump(mode="json") for ref in section.source_refs]),
                section.created_at.isoformat(),
                section.updated_at.isoformat(),
            ),
        )

    def _persist_note(self, note: Note) -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO notes (
                id, artifact_type, schema_version, status, version, title, summary, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                note.id,
                note.artifact_type,
                note.schema_version,
                note.status,
                note.version,
                note.title,
                note.summary,
                note.created_at.isoformat(),
                note.updated_at.isoformat(),
            ),
        )
        self._replace_links("note_source_specs", "note_id", "spec_id", note.id, note.source_spec_ids)

    def _persist_requirement(self, requirement: Requirement) -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO requirements (
                id, artifact_type, schema_version, status, version, title, statement, classes_json,
                asil, cal, graph_node_id, variant_scope, audit_rationale_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                requirement.id,
                requirement.artifact_type,
                requirement.schema_version,
                requirement.status,
                requirement.version,
                requirement.title,
                requirement.statement,
                self._json_dump(requirement.compliance.classes),
                requirement.compliance.asil,
                requirement.compliance.cal,
                requirement.trace.graph_node_id,
                requirement.variant_scope,
                requirement.audit_rationale_id,
                requirement.created_at.isoformat(),
                requirement.updated_at.isoformat(),
            ),
        )
        self._replace_links("requirement_source_specs", "requirement_id", "spec_id", requirement.id, requirement.source_spec_ids)
        self._replace_links("requirement_source_notes", "requirement_id", "note_id", requirement.id, requirement.source_note_ids)

    def _persist_test_requirement(self, test_requirement: TestRequirement) -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO test_requirements (
                id, artifact_type, schema_version, status, version, statement, acceptance_criteria_json,
                audit_rationale_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                test_requirement.id,
                test_requirement.artifact_type,
                test_requirement.schema_version,
                test_requirement.status,
                test_requirement.version,
                test_requirement.statement,
                self._json_dump(test_requirement.acceptance_criteria),
                test_requirement.audit_rationale_id,
                test_requirement.created_at.isoformat(),
                test_requirement.updated_at.isoformat(),
            ),
        )
        self._replace_links(
            "test_requirement_sources",
            "test_requirement_id",
            "requirement_id",
            test_requirement.id,
            test_requirement.source_requirement_ids,
        )

    def _persist_audit_rationale(self, audit_rationale: AuditRationale) -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO audit_rationales (
                id, artifact_id, source_refs_json, prompt_version, model_version, silver_refs_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                audit_rationale.id,
                audit_rationale.artifact_id,
                self._json_dump([ref.model_dump(mode="json") for ref in audit_rationale.source_refs]),
                audit_rationale.prompt_version,
                audit_rationale.model_version,
                self._json_dump(audit_rationale.silver_refs),
                audit_rationale.created_at.isoformat(),
            ),
        )

    def _persist_review(self, review: ReviewRecord) -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO reviews (
                id, artifact_id, decision, reviewer_id, rejection_tags_json, review_note, reviewed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                review.id,
                review.artifact_id,
                review.decision,
                review.reviewer_id,
                self._json_dump(review.rejection_tags),
                review.review_note,
                review.reviewed_at.isoformat(),
            ),
        )

    def _persist_lock(self, lock: SectionLock) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO locks (section_key, owner_id, expires_at, status) VALUES (?, ?, ?, ?)",
            (lock.section_key, lock.owner_id, lock.expires_at.isoformat(), lock.status),
        )

    def _persist_trace_entry(self, trace_entry: TraceMapEntry) -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO trace_entries (
                artifact_id, artifact_type, status, version, schema_version, last_review_id, audit_rationale_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trace_entry.artifact_id,
                trace_entry.artifact_type,
                trace_entry.status,
                trace_entry.version,
                trace_entry.schema_version,
                trace_entry.last_review_id,
                trace_entry.audit_rationale_id,
            ),
        )

    def _build_spec_section(self, row: sqlite3.Row) -> SpecSection:
        return SpecSection.model_validate(
            {
                "id": row["id"],
                "artifact_type": row["artifact_type"],
                "schema_version": row["schema_version"],
                "status": row["status"],
                "version": row["version"],
                "section_key": row["section_key"],
                "title": row["title"],
                "text": row["text"],
                "normalized_text": row["normalized_text"],
                "parser_warnings": self._json_load(row["parser_warnings_json"]),
                "source_refs": self._json_load(row["source_refs_json"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        )

    def _build_note(self, row: sqlite3.Row) -> Note:
        return Note.model_validate(
            {
                "id": row["id"],
                "artifact_type": row["artifact_type"],
                "schema_version": row["schema_version"],
                "status": row["status"],
                "version": row["version"],
                "title": row["title"],
                "summary": row["summary"],
                "source_spec_ids": self._linked_ids("note_source_specs", "note_id", "spec_id", row["id"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        )

    def _build_requirement(self, row: sqlite3.Row) -> Requirement:
        requirement_id = row["id"]
        return Requirement.model_validate(
            {
                "id": requirement_id,
                "artifact_type": row["artifact_type"],
                "schema_version": row["schema_version"],
                "status": row["status"],
                "version": row["version"],
                "title": row["title"],
                "statement": row["statement"],
                "source_spec_ids": self._linked_ids("requirement_source_specs", "requirement_id", "spec_id", requirement_id),
                "source_note_ids": self._linked_ids("requirement_source_notes", "requirement_id", "note_id", requirement_id),
                "compliance": {
                    "classes": self._json_load(row["classes_json"]),
                    "asil": row["asil"],
                    "cal": row["cal"],
                },
                "trace": {
                    "graph_node_id": row["graph_node_id"],
                    "downstream_test_requirement_ids": self._linked_ids(
                        "test_requirement_sources",
                        "requirement_id",
                        "test_requirement_id",
                        requirement_id,
                    ),
                },
                "audit_rationale_id": row["audit_rationale_id"],
                "variant_scope": row["variant_scope"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        )

    def _build_test_requirement(self, row: sqlite3.Row) -> TestRequirement:
        return TestRequirement.model_validate(
            {
                "id": row["id"],
                "artifact_type": row["artifact_type"],
                "schema_version": row["schema_version"],
                "status": row["status"],
                "version": row["version"],
                "statement": row["statement"],
                "source_requirement_ids": self._linked_ids(
                    "test_requirement_sources",
                    "test_requirement_id",
                    "requirement_id",
                    row["id"],
                ),
                "acceptance_criteria": self._json_load(row["acceptance_criteria_json"]),
                "audit_rationale_id": row["audit_rationale_id"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        )

    def _build_audit_rationale(self, row: sqlite3.Row) -> AuditRationale:
        return AuditRationale.model_validate(
            {
                "id": row["id"],
                "artifact_id": row["artifact_id"],
                "source_refs": self._json_load(row["source_refs_json"]),
                "prompt_version": row["prompt_version"],
                "model_version": row["model_version"],
                "silver_refs": self._json_load(row["silver_refs_json"]),
                "created_at": row["created_at"],
            }
        )

    def _build_review(self, row: sqlite3.Row) -> ReviewRecord:
        return ReviewRecord.model_validate(
            {
                "id": row["id"],
                "artifact_id": row["artifact_id"],
                "decision": row["decision"],
                "reviewer_id": row["reviewer_id"],
                "rejection_tags": self._json_load(row["rejection_tags_json"]),
                "review_note": row["review_note"],
                "reviewed_at": row["reviewed_at"],
            }
        )

    def _build_lock(self, row: sqlite3.Row) -> SectionLock:
        return SectionLock.model_validate(
            {
                "section_key": row["section_key"],
                "owner_id": row["owner_id"],
                "expires_at": row["expires_at"],
                "status": row["status"],
            }
        )

    def _trace_links(self, artifact_id: str, artifact_type: str) -> tuple[list[str], list[str]]:
        if artifact_type == "spec_section":
            downstream = self._linked_ids("note_source_specs", "spec_id", "note_id", artifact_id)
            downstream.extend(self._linked_ids("requirement_source_specs", "spec_id", "requirement_id", artifact_id))
            return [], downstream
        if artifact_type == "note":
            upstream = self._linked_ids("note_source_specs", "note_id", "spec_id", artifact_id)
            downstream = self._linked_ids("requirement_source_notes", "note_id", "requirement_id", artifact_id)
            return upstream, downstream
        if artifact_type == "requirement":
            upstream = self._linked_ids("requirement_source_specs", "requirement_id", "spec_id", artifact_id)
            upstream.extend(self._linked_ids("requirement_source_notes", "requirement_id", "note_id", artifact_id))
            downstream = self._linked_ids("test_requirement_sources", "requirement_id", "test_requirement_id", artifact_id)
            return upstream, downstream
        if artifact_type == "test_requirement":
            upstream = self._linked_ids("test_requirement_sources", "test_requirement_id", "requirement_id", artifact_id)
            return upstream, []
        return [], []

    def upsert_spec_section(self, section: SpecSection) -> SpecSection:
        section.updated_at = utc_now()
        self._persist_spec_section(section)
        self._persist_trace_entry(
            TraceMapEntry(
                artifact_id=section.id,
                artifact_type=section.artifact_type,
                upstream_ids=[],
                downstream_ids=[],
                status=section.status,
                version=section.version,
                schema_version=section.schema_version,
            )
        )
        self.connection.commit()
        return section

    def list_spec_sections(self, status_filter: str | None, section_key: str | None) -> list[SpecSection]:
        sql = "SELECT * FROM spec_sections WHERE 1 = 1"
        params: list[Any] = []
        if status_filter:
            sql += " AND status = ?"
            params.append(status_filter)
        if section_key:
            sql += " AND section_key = ?"
            params.append(section_key)
        rows = self._rows(sql + " ORDER BY id", tuple(params))
        return [self._build_spec_section(row) for row in rows]

    def get_spec_section(self, spec_section_id: str) -> SpecSection:
        row = self._row_or_none("SELECT * FROM spec_sections WHERE id = ?", (spec_section_id,))
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spec section not found")
        return self._build_spec_section(row)

    def create_note(self, note: Note) -> Note:
        for source_spec_id in note.source_spec_ids:
            self.get_spec_section(source_spec_id)
        self._persist_note(note)
        self._persist_trace_entry(
            TraceMapEntry(
                artifact_id=note.id,
                artifact_type=note.artifact_type,
                upstream_ids=note.source_spec_ids,
                downstream_ids=[],
                status=note.status,
                version=note.version,
                schema_version=note.schema_version,
            )
        )
        self.connection.commit()
        return note

    def list_notes(self, status_filter: str | None, source_spec_id: str | None) -> list[Note]:
        sql = "SELECT DISTINCT notes.* FROM notes"
        params: list[Any] = []
        if source_spec_id:
            sql += " JOIN note_source_specs ON note_source_specs.note_id = notes.id"
        sql += " WHERE 1 = 1"
        if status_filter:
            sql += " AND notes.status = ?"
            params.append(status_filter)
        if source_spec_id:
            sql += " AND note_source_specs.spec_id = ?"
            params.append(source_spec_id)
        rows = self._rows(sql + " ORDER BY notes.id", tuple(params))
        return [self._build_note(row) for row in rows]

    def get_note(self, note_id: str) -> Note:
        row = self._row_or_none("SELECT * FROM notes WHERE id = ?", (note_id,))
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
        return self._build_note(row)

    def create_requirement(self, requirement: Requirement) -> Requirement:
        for source_note_id in requirement.source_note_ids:
            self.get_note(source_note_id)
        self._persist_requirement(requirement)
        self._persist_trace_entry(
            TraceMapEntry(
                artifact_id=requirement.id,
                artifact_type=requirement.artifact_type,
                upstream_ids=requirement.source_spec_ids + requirement.source_note_ids,
                downstream_ids=requirement.trace.downstream_test_requirement_ids,
                status=requirement.status,
                version=requirement.version,
                schema_version=requirement.schema_version,
                audit_rationale_id=requirement.audit_rationale_id,
            )
        )
        self.connection.commit()
        return requirement

    def list_requirements(self, status_filter: str | None, source_spec_id: str | None) -> list[Requirement]:
        sql = "SELECT DISTINCT requirements.* FROM requirements"
        params: list[Any] = []
        if source_spec_id:
            sql += " JOIN requirement_source_specs ON requirement_source_specs.requirement_id = requirements.id"
        sql += " WHERE 1 = 1"
        if status_filter:
            sql += " AND requirements.status = ?"
            params.append(status_filter)
        if source_spec_id:
            sql += " AND requirement_source_specs.spec_id = ?"
            params.append(source_spec_id)
        rows = self._rows(sql + " ORDER BY requirements.id", tuple(params))
        return [self._build_requirement(row) for row in rows]

    def get_requirement(self, requirement_id: str) -> Requirement:
        row = self._row_or_none("SELECT * FROM requirements WHERE id = ?", (requirement_id,))
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found")
        return self._build_requirement(row)

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
            if not self._row_or_none("SELECT id FROM audit_rationales WHERE id = ?", (audit_rationale_id,)):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit rationale not found")
            item.audit_rationale_id = audit_rationale_id
        item.updated_at = utc_now()
        self._persist_requirement(item)
        trace = self.get_trace(requirement_id)
        trace.status = item.status
        trace.audit_rationale_id = item.audit_rationale_id
        self._persist_trace_entry(trace)
        self.connection.commit()
        return item

    def submit_requirement_review(self, requirement_id: str) -> Requirement:
        item = self.get_requirement(requirement_id)
        if item.status != "DRAFT":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only DRAFT requirement can enter review")
        item.status = "IN_REVIEW"
        item.updated_at = utc_now()
        self._persist_requirement(item)
        trace = self.get_trace(requirement_id)
        trace.status = item.status
        self._persist_trace_entry(trace)
        self.connection.commit()
        return item

    def create_test_requirement(self, test_requirement: TestRequirement) -> TestRequirement:
        for source_requirement_id in test_requirement.source_requirement_ids:
            self.get_requirement(source_requirement_id)
        if test_requirement.audit_rationale_id is not None and not self._row_or_none(
            "SELECT id FROM audit_rationales WHERE id = ?",
            (test_requirement.audit_rationale_id,),
        ):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit rationale not found")
        self._persist_test_requirement(test_requirement)
        self._persist_trace_entry(
            TraceMapEntry(
                artifact_id=test_requirement.id,
                artifact_type=test_requirement.artifact_type,
                upstream_ids=test_requirement.source_requirement_ids,
                downstream_ids=[],
                status=test_requirement.status,
                version=test_requirement.version,
                schema_version=test_requirement.schema_version,
                audit_rationale_id=test_requirement.audit_rationale_id,
            )
        )
        self.connection.commit()
        return test_requirement

    def list_test_requirements(self, status_filter: str | None, source_requirement_id: str | None) -> list[TestRequirement]:
        sql = "SELECT DISTINCT test_requirements.* FROM test_requirements"
        params: list[Any] = []
        if source_requirement_id:
            sql += " JOIN test_requirement_sources ON test_requirement_sources.test_requirement_id = test_requirements.id"
        sql += " WHERE 1 = 1"
        if status_filter:
            sql += " AND test_requirements.status = ?"
            params.append(status_filter)
        if source_requirement_id:
            sql += " AND test_requirement_sources.requirement_id = ?"
            params.append(source_requirement_id)
        rows = self._rows(sql + " ORDER BY test_requirements.id", tuple(params))
        return [self._build_test_requirement(row) for row in rows]

    def get_test_requirement(self, test_requirement_id: str) -> TestRequirement:
        row = self._row_or_none("SELECT * FROM test_requirements WHERE id = ?", (test_requirement_id,))
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test requirement not found")
        return self._build_test_requirement(row)

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
            if not self._row_or_none("SELECT id FROM audit_rationales WHERE id = ?", (audit_rationale_id,)):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit rationale not found")
            item.audit_rationale_id = audit_rationale_id
        item.updated_at = utc_now()
        self._persist_test_requirement(item)
        trace = self.get_trace(test_requirement_id)
        trace.status = item.status
        trace.audit_rationale_id = item.audit_rationale_id
        self._persist_trace_entry(trace)
        self.connection.commit()
        return item

    def submit_test_requirement_review(self, test_requirement_id: str) -> TestRequirement:
        item = self.get_test_requirement(test_requirement_id)
        if item.status != "DRAFT":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only DRAFT test requirement can enter review")
        item.status = "IN_REVIEW"
        item.updated_at = utc_now()
        self._persist_test_requirement(item)
        trace = self.get_trace(test_requirement_id)
        trace.status = item.status
        self._persist_trace_entry(trace)
        self.connection.commit()
        return item

    def create_audit_rationale(self, audit_rationale: AuditRationale) -> AuditRationale:
        if (
            not self._row_or_none("SELECT id FROM requirements WHERE id = ?", (audit_rationale.artifact_id,))
            and not self._row_or_none("SELECT id FROM test_requirements WHERE id = ?", (audit_rationale.artifact_id,))
        ):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found for audit rationale")
        self._persist_audit_rationale(audit_rationale)
        self.connection.commit()
        return audit_rationale

    def get_audit_rationale(self, audit_rationale_id: str) -> AuditRationale:
        row = self._row_or_none("SELECT * FROM audit_rationales WHERE id = ?", (audit_rationale_id,))
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit rationale not found")
        return self._build_audit_rationale(row)

    def create_review(self, review: ReviewRecord) -> ReviewDecisionResponse:
        requirement_row = self._row_or_none("SELECT * FROM requirements WHERE id = ?", (review.artifact_id,))
        requirement = self._build_requirement(requirement_row) if requirement_row else None
        if requirement:
            if requirement.status != "IN_REVIEW":
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Requirement must be IN_REVIEW")
            if review.decision == "APPROVED" and not requirement.audit_rationale_id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="APPROVED requirement requires audit_rationale_id")
            requirement.status = review.decision
            requirement.updated_at = utc_now()
            self._persist_requirement(requirement)
            artifact: Requirement | TestRequirement = requirement
        else:
            test_requirement_row = self._row_or_none("SELECT * FROM test_requirements WHERE id = ?", (review.artifact_id,))
            test_requirement = self._build_test_requirement(test_requirement_row) if test_requirement_row else None
            if not test_requirement:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review target not found")
            if test_requirement.status != "IN_REVIEW":
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Test requirement must be IN_REVIEW")
            if review.decision == "APPROVED" and not test_requirement.audit_rationale_id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="APPROVED test requirement requires audit_rationale_id")
            test_requirement.status = review.decision
            test_requirement.updated_at = utc_now()
            self._persist_test_requirement(test_requirement)
            artifact = test_requirement

        self._persist_review(review)
        trace = self.get_trace(review.artifact_id)
        trace.status = artifact.status
        trace.last_review_id = review.id
        trace.audit_rationale_id = artifact.audit_rationale_id
        self._persist_trace_entry(trace)
        self.connection.commit()
        return ReviewDecisionResponse(review=review, artifact=artifact)

    def get_review(self, review_id: str) -> ReviewRecord:
        row = self._row_or_none("SELECT * FROM reviews WHERE id = ?", (review_id,))
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
        return self._build_review(row)

    def acquire_or_renew_lock(self, section_key: str, request) -> SectionLock:
        current_row = self._row_or_none("SELECT * FROM locks WHERE section_key = ?", (section_key,))
        current = self._build_lock(current_row) if current_row else None
        now = utc_now()
        if current and current.expires_at > now and current.owner_id != request.owner_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "Lock conflict", "current_lock": current.model_dump(mode="json")},
            )
        lock = SectionLock(section_key=section_key, owner_id=request.owner_id, expires_at=request.expires_at())
        self._persist_lock(lock)
        self.connection.commit()
        return lock

    def release_lock(self, section_key: str, owner_id: str) -> None:
        current_row = self._row_or_none("SELECT * FROM locks WHERE section_key = ?", (section_key,))
        current = self._build_lock(current_row) if current_row else None
        if not current:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lock not found")
        if current.owner_id != owner_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only lock owner can release lock")
        self.connection.execute("DELETE FROM locks WHERE section_key = ?", (section_key,))
        self.connection.commit()

    def get_trace(self, artifact_id: str) -> TraceMapEntry:
        row = self._row_or_none("SELECT * FROM trace_entries WHERE artifact_id = ?", (artifact_id,))
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trace entry not found")
        upstream_ids, downstream_ids = self._trace_links(row["artifact_id"], row["artifact_type"])
        return TraceMapEntry.model_validate(
            {
                "artifact_id": row["artifact_id"],
                "artifact_type": row["artifact_type"],
                "upstream_ids": upstream_ids,
                "downstream_ids": downstream_ids,
                "status": row["status"],
                "version": row["version"],
                "schema_version": row["schema_version"],
                "last_review_id": row["last_review_id"],
                "audit_rationale_id": row["audit_rationale_id"],
            }
        )

    def export_requirement(self, request: CodebeamerExportRequest) -> ExportJobResponse:
        requirement = self.get_requirement(request.requirement_id)
        if requirement.status != "APPROVED":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only APPROVED requirements can be exported")
        return ExportJobResponse(job_id=f"export-{uuid4()}", status="QUEUED", integration_log_id=f"log-{uuid4()}")
