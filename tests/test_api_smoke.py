from pathlib import Path
import sqlite3
import json

from fastapi.testclient import TestClient

from specops_api.app import create_app
from specops_api.repository import InMemoryRepository, SQLiteRepository


def make_memory_client() -> TestClient:
    return TestClient(create_app(InMemoryRepository()))


def make_sqlite_client(db_path: Path) -> TestClient:
    return TestClient(create_app(SQLiteRepository(db_path)))


def create_spec_section(client: TestClient) -> str:
    spec_section_payload = {
        "id": "S-oemx-cluster-v1_0-sec_001",
        "artifact_type": "spec_section",
        "schema_version": "1.0.0",
        "status": "DRAFT",
        "version": "v1.0",
        "section_key": "sec_001",
        "title": "Vehicle Speed Display",
        "text": "The system shall display vehicle speed in km/h when market profile is metric.",
        "normalized_text": "The system shall display vehicle speed in km/h when market profile is metric.",
        "parser_warnings": [],
        "source_refs": [{"page": 12, "bbox": [100, 200, 400, 260], "table_ref": None}],
        "created_at": "2026-03-31T00:00:00Z",
        "updated_at": "2026-03-31T00:00:00Z",
    }
    spec_response = client.post("/spec-sections", json=spec_section_payload)
    assert spec_response.status_code == 201
    return spec_response.json()["id"]


def test_registered_real_spec_listing_smoke() -> None:
    client = make_memory_client()

    response = client.get("/pipelines/markdown-specs/registered")

    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["document_id"] for item in items] == [
        "triumph-s6867-07",
        "kawasaki-global-req",
    ]


def test_registered_real_spec_section_listing_smoke() -> None:
    client = make_memory_client()

    response = client.get("/pipelines/markdown-specs/triumph-s6867-07/sections")

    assert response.status_code == 200
    items = response.json()["items"]
    assert items[0]["id"] == "S-triumph-s6867-07-sec_001"
    assert any(item["section_key"] == "sec_007" for item in items)


def test_registered_real_spec_section_detail_smoke() -> None:
    client = make_memory_client()

    response = client.get("/pipelines/markdown-specs/triumph-s6867-07/sections/sec_007")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "S-triumph-s6867-07-sec_007"
    assert payload["title"] == "Operation"


def test_registered_real_spec_direct_bundle_generation_smoke() -> None:
    client = make_memory_client()

    response = client.post(
        "/pipelines/markdown-specs/triumph-s6867-07/sections/sec_007/generate-requirement-bundle",
        json={
            "prompt_version": "deterministic-note-v1",
            "model_version": "rule-based-generator-v1",
            "variant_scope": "base",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["requirement"]["artifact_type"] == "requirement"
    assert payload["audit_rationale"]["artifact_id"] == payload["requirement"]["id"]


def create_note(client: TestClient, source_spec_id: str) -> str:
    note_response = client.post(
        "/notes",
        json={
            "title": "Vehicle speed display note",
            "summary": "Metric market profile requires km/h display.",
            "source_spec_ids": [source_spec_id],
        },
    )
    assert note_response.status_code == 201
    return note_response.json()["id"]


def create_requirement(client: TestClient, source_spec_id: str, note_id: str) -> str:
    requirement_response = client.post(
        "/requirements",
        json={
            "title": "Display vehicle speed in metric mode",
            "statement": "The system shall display vehicle speed in km/h when market profile is metric.",
            "source_spec_ids": [source_spec_id],
            "source_note_ids": [note_id],
            "compliance": {"classes": ["FSR"], "asil": "B", "cal": None},
            "variant_scope": "base",
        },
    )
    assert requirement_response.status_code == 201
    return requirement_response.json()["id"]


def create_test_requirement(client: TestClient, requirement_id: str) -> str:
    response = client.post(
        "/test-requirements",
        json={
            "statement": "Verify speed is shown in km/h under metric market profile.",
            "source_requirement_ids": [requirement_id],
            "acceptance_criteria": [
                "Display unit is km/h",
                "Displayed value matches input signal tolerance",
            ],
            "audit_rationale_id": None,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def attach_audit_rationale(client: TestClient, artifact_id: str, source_spec_id: str) -> str:
    audit_response = client.post(
        "/audit-rationales",
        json={
            "artifact_id": artifact_id,
            "source_refs": [
                {
                    "spec_id": source_spec_id,
                    "page": 12,
                    "bbox": [100, 200, 400, 260],
                }
            ],
            "prompt_version": "prompt-v1",
            "model_version": "model-v1",
            "silver_refs": [],
        },
    )
    assert audit_response.status_code == 201
    audit_id = audit_response.json()["id"]

    if artifact_id.startswith("R-"):
        patch_response = client.patch(
            f"/requirements/{artifact_id}",
            json={"audit_rationale_id": audit_id},
        )
        assert patch_response.status_code == 200
        assert patch_response.json()["audit_rationale_id"] == audit_id
    elif artifact_id.startswith("T-"):
        patch_response = client.patch(
            f"/test-requirements/{artifact_id}",
            json={"audit_rationale_id": audit_id},
        )
        assert patch_response.status_code == 200
        assert patch_response.json()["audit_rationale_id"] == audit_id
    return audit_id


def create_legacy_payload_db(db_path: Path) -> None:
    connection = sqlite3.connect(db_path)
    try:
        for ddl in [
            "CREATE TABLE spec_sections (id TEXT PRIMARY KEY, payload TEXT NOT NULL)",
            "CREATE TABLE notes (id TEXT PRIMARY KEY, payload TEXT NOT NULL)",
            "CREATE TABLE requirements (id TEXT PRIMARY KEY, payload TEXT NOT NULL)",
            "CREATE TABLE test_requirements (id TEXT PRIMARY KEY, payload TEXT NOT NULL)",
            "CREATE TABLE audit_rationales (id TEXT PRIMARY KEY, payload TEXT NOT NULL)",
            "CREATE TABLE reviews (id TEXT PRIMARY KEY, payload TEXT NOT NULL)",
            "CREATE TABLE locks (section_key TEXT PRIMARY KEY, payload TEXT NOT NULL)",
            "CREATE TABLE trace_entries (artifact_id TEXT PRIMARY KEY, payload TEXT NOT NULL)",
        ]:
            connection.execute(ddl)

        spec_id = "S-legacy"
        note_id = "N-legacy"
        requirement_id = "R-legacy"
        test_requirement_id = "T-legacy"
        audit_id = "AR-legacy"
        review_id = "RV-legacy"

        records = {
            "spec_sections": [
                (
                    spec_id,
                    {
                        "id": spec_id,
                        "artifact_type": "spec_section",
                        "schema_version": "1.0.0",
                        "status": "DRAFT",
                        "version": "v1.0",
                        "section_key": "sec_legacy",
                        "title": "Legacy Section",
                        "text": "Legacy spec text.",
                        "normalized_text": "Legacy spec text.",
                        "parser_warnings": [],
                        "source_refs": [{"page": 3, "bbox": [1, 2, 3, 4], "table_ref": None}],
                        "created_at": "2026-03-31T00:00:00Z",
                        "updated_at": "2026-03-31T00:00:00Z",
                    },
                )
            ],
            "notes": [
                (
                    note_id,
                    {
                        "id": note_id,
                        "artifact_type": "note",
                        "schema_version": "1.0.0",
                        "status": "DRAFT",
                        "version": "v1.0",
                        "title": "Legacy Note",
                        "summary": "Legacy note summary.",
                        "source_spec_ids": [spec_id],
                        "created_at": "2026-03-31T00:00:00Z",
                        "updated_at": "2026-03-31T00:00:00Z",
                    },
                )
            ],
            "requirements": [
                (
                    requirement_id,
                    {
                        "id": requirement_id,
                        "artifact_type": "requirement",
                        "schema_version": "1.0.0",
                        "status": "APPROVED",
                        "version": "v1.0",
                        "title": "Legacy Requirement",
                        "statement": "Legacy requirement statement.",
                        "source_spec_ids": [spec_id],
                        "source_note_ids": [note_id],
                        "compliance": {"classes": ["FSR"], "asil": "B", "cal": None},
                        "trace": {
                            "graph_node_id": "GN-legacy",
                            "downstream_test_requirement_ids": [test_requirement_id],
                        },
                        "audit_rationale_id": audit_id,
                        "variant_scope": "base",
                        "created_at": "2026-03-31T00:00:00Z",
                        "updated_at": "2026-03-31T00:00:00Z",
                    },
                )
            ],
            "test_requirements": [
                (
                    test_requirement_id,
                    {
                        "id": test_requirement_id,
                        "artifact_type": "test_requirement",
                        "schema_version": "1.0.0",
                        "status": "APPROVED",
                        "version": "v1.0",
                        "statement": "Legacy test requirement statement.",
                        "source_requirement_ids": [requirement_id],
                        "acceptance_criteria": ["Criterion A"],
                        "audit_rationale_id": audit_id,
                        "created_at": "2026-03-31T00:00:00Z",
                        "updated_at": "2026-03-31T00:00:00Z",
                    },
                )
            ],
            "audit_rationales": [
                (
                    audit_id,
                    {
                        "id": audit_id,
                        "artifact_id": requirement_id,
                        "source_refs": [{"spec_id": spec_id, "page": 3, "bbox": [1, 2, 3, 4]}],
                        "prompt_version": "legacy-prompt",
                        "model_version": "legacy-model",
                        "silver_refs": [],
                        "created_at": "2026-03-31T00:00:00Z",
                    },
                )
            ],
            "reviews": [
                (
                    review_id,
                    {
                        "id": review_id,
                        "artifact_id": requirement_id,
                        "decision": "APPROVED",
                        "reviewer_id": "legacy-reviewer",
                        "rejection_tags": [],
                        "review_note": "Legacy approval.",
                        "reviewed_at": "2026-03-31T00:00:00Z",
                    },
                )
            ],
            "locks": [
                (
                    "sec_legacy",
                    {
                        "section_key": "sec_legacy",
                        "owner_id": "legacy-user",
                        "expires_at": "2099-03-31T00:00:00Z",
                        "status": "LOCKED",
                    },
                )
            ],
            "trace_entries": [
                (
                    requirement_id,
                    {
                        "artifact_id": requirement_id,
                        "artifact_type": "requirement",
                        "upstream_ids": [spec_id, note_id],
                        "downstream_ids": [test_requirement_id],
                        "status": "APPROVED",
                        "version": "v1.0",
                        "schema_version": "1.0.0",
                        "last_review_id": review_id,
                        "audit_rationale_id": audit_id,
                    },
                )
            ],
        }

        for table, rows in records.items():
            key = "section_key" if table == "locks" else "artifact_id" if table == "trace_entries" else "id"
            for record_id, payload in rows:
                connection.execute(
                    f"INSERT INTO {table} ({key}, payload) VALUES (?, ?)",
                    (record_id, json.dumps(payload)),
                )
        connection.commit()
    finally:
        connection.close()


def test_healthcheck() -> None:
    client = make_memory_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_spec_note_requirement_review_trace_flow() -> None:
    client = make_memory_client()
    spec_section_id = create_spec_section(client)
    note_id = create_note(client, spec_section_id)
    requirement_id = create_requirement(client, spec_section_id, note_id)

    note_response = client.get(f"/notes/{note_id}")
    assert note_response.status_code == 200
    assert note_response.json()["id"] == note_id

    submit_response = client.post(
        f"/requirements/{requirement_id}/submit-review",
        json={"reviewer_id": "reviewer-a", "review_note": "ready"},
    )
    assert submit_response.status_code == 200
    assert submit_response.json()["status"] == "IN_REVIEW"

    reject_response = client.post(
        "/reviews",
        json={
            "artifact_id": requirement_id,
            "decision": "REJECTED",
            "reviewer_id": "reviewer-a",
            "rejection_tags": ["missing_trace"],
            "review_note": "Need audit rationale before approval.",
        },
    )
    assert reject_response.status_code == 201
    assert reject_response.json()["artifact"]["status"] == "REJECTED"

    trace_response = client.get(f"/trace/{requirement_id}")
    assert trace_response.status_code == 200
    trace = trace_response.json()
    assert spec_section_id in trace["upstream_ids"]
    assert note_id in trace["upstream_ids"]


def test_requirement_to_test_requirement_trace_flow() -> None:
    client = make_memory_client()
    spec_section_id = create_spec_section(client)
    note_id = create_note(client, spec_section_id)
    requirement_id = create_requirement(client, spec_section_id, note_id)
    test_requirement_id = create_test_requirement(client, requirement_id)

    test_requirement_response = client.get(f"/test-requirements/{test_requirement_id}")
    assert test_requirement_response.status_code == 200
    assert test_requirement_response.json()["id"] == test_requirement_id

    requirement_trace_response = client.get(f"/trace/{requirement_id}")
    assert requirement_trace_response.status_code == 200
    assert test_requirement_id in requirement_trace_response.json()["downstream_ids"]

    test_requirement_trace_response = client.get(f"/trace/{test_requirement_id}")
    assert test_requirement_trace_response.status_code == 200
    assert requirement_id in test_requirement_trace_response.json()["upstream_ids"]


def test_test_requirement_review_and_approval_flow() -> None:
    client = make_memory_client()
    spec_section_id = create_spec_section(client)
    note_id = create_note(client, spec_section_id)
    requirement_id = create_requirement(client, spec_section_id, note_id)
    test_requirement_id = create_test_requirement(client, requirement_id)
    audit_id = attach_audit_rationale(client, test_requirement_id, spec_section_id)

    submit_response = client.post(
        f"/test-requirements/{test_requirement_id}/submit-review",
        json={"reviewer_id": "reviewer-a"},
    )
    assert submit_response.status_code == 200
    assert submit_response.json()["status"] == "IN_REVIEW"

    approve_response = client.post(
        "/reviews",
        json={
            "artifact_id": test_requirement_id,
            "decision": "APPROVED",
            "reviewer_id": "reviewer-a",
            "review_note": "Approved test requirement.",
        },
    )
    assert approve_response.status_code == 201
    assert approve_response.json()["artifact"]["status"] == "APPROVED"
    assert approve_response.json()["artifact"]["audit_rationale_id"] == audit_id
    assert approve_response.json()["artifact"]["artifact_type"] == "test_requirement"


def test_approve_and_export_flow() -> None:
    client = make_memory_client()
    spec_section_id = create_spec_section(client)
    note_id = create_note(client, spec_section_id)
    requirement_id = create_requirement(client, spec_section_id, note_id)
    audit_id = attach_audit_rationale(client, requirement_id, spec_section_id)

    submit_response = client.post(
        f"/requirements/{requirement_id}/submit-review",
        json={"reviewer_id": "reviewer-a"},
    )
    assert submit_response.status_code == 200

    approve_response = client.post(
        "/reviews",
        json={
            "artifact_id": requirement_id,
            "decision": "APPROVED",
            "reviewer_id": "reviewer-a",
            "review_note": "Approved for export.",
        },
    )
    assert approve_response.status_code == 201
    assert approve_response.json()["artifact"]["status"] == "APPROVED"
    assert approve_response.json()["artifact"]["audit_rationale_id"] == audit_id

    export_response = client.post(
        "/exports/codebeamer",
        json={"requirement_id": requirement_id, "requested_by": "user-a"},
    )
    assert export_response.status_code == 200
    assert export_response.json()["status"] == "QUEUED"



def test_generate_test_requirement_from_approved_requirement_flow() -> None:
    client = make_memory_client()
    spec_section_id = create_spec_section(client)
    note_id = create_note(client, spec_section_id)
    requirement_id = create_requirement(client, spec_section_id, note_id)
    attach_audit_rationale(client, requirement_id, spec_section_id)

    submit_response = client.post(
        f"/requirements/{requirement_id}/submit-review",
        json={"reviewer_id": "reviewer-a"},
    )
    assert submit_response.status_code == 200

    approve_response = client.post(
        "/reviews",
        json={
            "artifact_id": requirement_id,
            "decision": "APPROVED",
            "reviewer_id": "reviewer-a",
            "review_note": "Approved for downstream test generation.",
        },
    )
    assert approve_response.status_code == 201

    generate_response = client.post(f"/requirements/{requirement_id}/generate-test-requirement")
    assert generate_response.status_code == 201
    generated = generate_response.json()

    assert generated["artifact_type"] == "test_requirement"
    assert generated["status"] == "DRAFT"
    assert generated["source_requirement_ids"] == [requirement_id]
    assert generated["statement"].startswith("Verify:")
    assert len(generated["acceptance_criteria"]) == 2

    trace_response = client.get(f"/trace/{requirement_id}")
    assert trace_response.status_code == 200
    assert generated["id"] in trace_response.json()["downstream_ids"]


def test_generate_test_requirement_requires_approved_requirement() -> None:
    client = make_memory_client()
    spec_section_id = create_spec_section(client)
    note_id = create_note(client, spec_section_id)
    requirement_id = create_requirement(client, spec_section_id, note_id)

    generate_response = client.post(f"/requirements/{requirement_id}/generate-test-requirement")
    assert generate_response.status_code == 409
    assert generate_response.json() == {
        "error": "Only APPROVED requirements can generate test requirements",
        "detail": None,
    }


def test_generate_test_requirement_prevents_duplicate_active_downstream() -> None:
    client = make_memory_client()
    spec_section_id = create_spec_section(client)
    note_id = create_note(client, spec_section_id)
    requirement_id = create_requirement(client, spec_section_id, note_id)
    attach_audit_rationale(client, requirement_id, spec_section_id)

    submit_response = client.post(
        f"/requirements/{requirement_id}/submit-review",
        json={"reviewer_id": "reviewer-a"},
    )
    assert submit_response.status_code == 200

    approve_response = client.post(
        "/reviews",
        json={
            "artifact_id": requirement_id,
            "decision": "APPROVED",
            "reviewer_id": "reviewer-a",
            "review_note": "Approved for downstream test generation.",
        },
    )
    assert approve_response.status_code == 201

    first_generate_response = client.post(f"/requirements/{requirement_id}/generate-test-requirement")
    assert first_generate_response.status_code == 201

    second_generate_response = client.post(f"/requirements/{requirement_id}/generate-test-requirement")
    assert second_generate_response.status_code == 409
    assert second_generate_response.json() == {
        "error": "Active downstream test requirement already exists",
        "detail": None,
    }
def test_invalid_approve_without_audit_returns_error_response() -> None:
    client = make_memory_client()
    spec_section_id = create_spec_section(client)
    note_id = create_note(client, spec_section_id)
    requirement_id = create_requirement(client, spec_section_id, note_id)

    submit_response = client.post(
        f"/requirements/{requirement_id}/submit-review",
        json={"reviewer_id": "reviewer-a"},
    )
    assert submit_response.status_code == 200

    approve_response = client.post(
        "/reviews",
        json={
            "artifact_id": requirement_id,
            "decision": "APPROVED",
            "reviewer_id": "reviewer-a",
            "review_note": "Should fail without audit rationale.",
        },
    )
    assert approve_response.status_code == 409
    assert approve_response.json() == {
        "error": "APPROVED requirement requires audit_rationale_id",
        "detail": None,
    }


def test_invalid_test_requirement_approve_without_audit_returns_error_response() -> None:
    client = make_memory_client()
    spec_section_id = create_spec_section(client)
    note_id = create_note(client, spec_section_id)
    requirement_id = create_requirement(client, spec_section_id, note_id)
    test_requirement_id = create_test_requirement(client, requirement_id)

    submit_response = client.post(
        f"/test-requirements/{test_requirement_id}/submit-review",
        json={"reviewer_id": "reviewer-a"},
    )
    assert submit_response.status_code == 200

    approve_response = client.post(
        "/reviews",
        json={
            "artifact_id": test_requirement_id,
            "decision": "APPROVED",
            "reviewer_id": "reviewer-a",
            "review_note": "Should fail without audit rationale.",
        },
    )
    assert approve_response.status_code == 409
    assert approve_response.json() == {
        "error": "APPROVED test requirement requires audit_rationale_id",
        "detail": None,
    }


def test_invalid_requirement_creation_without_note_returns_error_response() -> None:
    client = make_memory_client()
    spec_section_id = create_spec_section(client)

    response = client.post(
        "/requirements",
        json={
            "title": "Invalid requirement",
            "statement": "This should fail because note is missing.",
            "source_spec_ids": [spec_section_id],
            "source_note_ids": ["N-missing"],
            "compliance": {"classes": [], "asil": None, "cal": None},
            "variant_scope": "base",
        },
    )
    assert response.status_code == 404
    assert response.json() == {"error": "Source note not found", "detail": None}


def test_review_queue_and_note_filter_listing() -> None:
    client = make_memory_client()
    spec_section_id = create_spec_section(client)
    note_id = create_note(client, spec_section_id)
    requirement_id = create_requirement(client, spec_section_id, note_id)

    note_list_response = client.get(f"/notes?source_spec_id={spec_section_id}")
    assert note_list_response.status_code == 200
    assert note_list_response.json()["items"][0]["id"] == note_id

    submit_response = client.post(
        f"/requirements/{requirement_id}/submit-review",
        json={"reviewer_id": "reviewer-a"},
    )
    assert submit_response.status_code == 200

    pending_review_response = client.get("/requirements?review_queue=pending_review")
    assert pending_review_response.status_code == 200
    ids = [item["id"] for item in pending_review_response.json()["items"]]
    assert requirement_id in ids


def test_lock_conflict_flow() -> None:
    client = make_memory_client()

    first = client.post("/locks/sec_001", json={"owner_id": "user-a", "ttl_minutes": 30})
    assert first.status_code == 200

    second = client.post("/locks/sec_001", json={"owner_id": "user-b", "ttl_minutes": 30})
    assert second.status_code == 409
    assert second.json()["error"] == "Lock conflict"
    assert second.json()["current_lock"]["owner_id"] == "user-a"


def test_missing_trace_returns_error_response() -> None:
    client = make_memory_client()
    response = client.get("/trace/does-not-exist")
    assert response.status_code == 404
    assert response.json() == {"error": "Trace entry not found", "detail": None}


def test_sqlite_repository_persists_across_app_instances(tmp_path: Path) -> None:
    db_path = tmp_path / "specops-test.db"
    client_a = make_sqlite_client(db_path)
    spec_section_id = create_spec_section(client_a)
    note_id = create_note(client_a, spec_section_id)
    requirement_id = create_requirement(client_a, spec_section_id, note_id)
    test_requirement_id = create_test_requirement(client_a, requirement_id)
    attach_audit_rationale(client_a, requirement_id, spec_section_id)
    attach_audit_rationale(client_a, test_requirement_id, spec_section_id)

    client_b = make_sqlite_client(db_path)
    note_response = client_b.get(f"/notes/{note_id}")
    assert note_response.status_code == 200
    assert note_response.json()["id"] == note_id

    requirement_response = client_b.get(f"/requirements/{requirement_id}")
    assert requirement_response.status_code == 200
    assert requirement_response.json()["id"] == requirement_id

    test_requirement_response = client_b.get(f"/test-requirements/{test_requirement_id}")
    assert test_requirement_response.status_code == 200
    assert test_requirement_response.json()["id"] == test_requirement_id

    trace_response = client_b.get(f"/trace/{requirement_id}")
    assert trace_response.status_code == 200
    assert test_requirement_id in trace_response.json()["downstream_ids"]


def test_sqlite_repository_uses_relational_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "specops-schema.db"
    client = make_sqlite_client(db_path)
    spec_section_id = create_spec_section(client)
    note_id = create_note(client, spec_section_id)
    requirement_id = create_requirement(client, spec_section_id, note_id)
    create_test_requirement(client, requirement_id)

    connection = sqlite3.connect(db_path)
    try:
        requirement_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(requirements)").fetchall()
        }
        assert {"id", "status", "title", "statement", "variant_scope", "audit_rationale_id"} <= requirement_columns
        assert "payload" not in requirement_columns

        source_note_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(requirement_source_notes)").fetchall()
        }
        assert {"requirement_id", "note_id", "position"} <= source_note_columns

        review_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(reviews)").fetchall()
        }
        assert {"id", "artifact_id", "decision", "reviewer_id", "reviewed_at"} <= review_columns
        assert "payload" not in review_columns
    finally:
        connection.close()


def test_sqlite_repository_migrates_legacy_payload_schema(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy-specops.db"
    create_legacy_payload_db(db_path)

    repo = SQLiteRepository(db_path)
    requirement = repo.get_requirement("R-legacy")
    test_requirement = repo.get_test_requirement("T-legacy")
    trace_entry = repo.get_trace("R-legacy")

    assert requirement.title == "Legacy Requirement"
    assert requirement.audit_rationale_id == "AR-legacy"
    assert test_requirement.source_requirement_ids == ["R-legacy"]
    assert trace_entry.downstream_ids == ["T-legacy"]

    connection = sqlite3.connect(db_path)
    try:
        requirement_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(requirements)").fetchall()
        }
        assert "payload" not in requirement_columns

        migrated_requirement = connection.execute(
            "SELECT title, status, audit_rationale_id FROM requirements WHERE id = ?",
            ("R-legacy",),
        ).fetchone()
        assert migrated_requirement == ("Legacy Requirement", "APPROVED", "AR-legacy")
    finally:
        connection.close()


def test_sqlite_repository_passes_integrity_check_and_link_counts(tmp_path: Path) -> None:
    db_path = tmp_path / "specops-integrity.db"
    client = make_sqlite_client(db_path)
    spec_section_id = create_spec_section(client)
    note_id = create_note(client, spec_section_id)
    requirement_id = create_requirement(client, spec_section_id, note_id)
    test_requirement_id = create_test_requirement(client, requirement_id)
    attach_audit_rationale(client, requirement_id, spec_section_id)
    attach_audit_rationale(client, test_requirement_id, spec_section_id)

    connection = sqlite3.connect(db_path)
    try:
        integrity_result = connection.execute("PRAGMA integrity_check").fetchone()
        assert integrity_result == ("ok",)

        requirement_note_links = connection.execute(
            "SELECT requirement_id, note_id, position FROM requirement_source_notes"
        ).fetchall()
        assert requirement_note_links == [(requirement_id, note_id, 0)]

        requirement_spec_links = connection.execute(
            "SELECT requirement_id, spec_id, position FROM requirement_source_specs"
        ).fetchall()
        assert requirement_spec_links == [(requirement_id, spec_section_id, 0)]

        test_requirement_links = connection.execute(
            "SELECT test_requirement_id, requirement_id, position FROM test_requirement_sources"
        ).fetchall()
        assert test_requirement_links == [(test_requirement_id, requirement_id, 0)]
    finally:
        connection.close()


def test_sqlite_repository_creates_query_indexes(tmp_path: Path) -> None:
    db_path = tmp_path / "specops-indexes.db"
    client = make_sqlite_client(db_path)
    spec_section_id = create_spec_section(client)
    note_id = create_note(client, spec_section_id)
    requirement_id = create_requirement(client, spec_section_id, note_id)
    create_test_requirement(client, requirement_id)

    connection = sqlite3.connect(db_path)
    try:
        def index_names(table: str) -> set[str]:
            return {row[1] for row in connection.execute(f"PRAGMA index_list({table})").fetchall()}

        assert "idx_spec_sections_section_key" in index_names("spec_sections")
        assert "idx_spec_sections_status" in index_names("spec_sections")
        assert "idx_notes_status" in index_names("notes")
        assert "idx_requirements_status" in index_names("requirements")
        assert "idx_requirements_variant_scope" in index_names("requirements")
        assert "idx_requirements_audit_rationale_id" in index_names("requirements")
        assert "idx_test_requirements_status" in index_names("test_requirements")
        assert "idx_test_requirements_audit_rationale_id" in index_names("test_requirements")
        assert "idx_audit_rationales_artifact_id" in index_names("audit_rationales")
        assert "idx_reviews_artifact_id" in index_names("reviews")
        assert "idx_trace_entries_artifact_type" in index_names("trace_entries")
        assert "idx_note_source_specs_spec_id" in index_names("note_source_specs")
        assert "idx_requirement_source_specs_spec_id" in index_names("requirement_source_specs")
        assert "idx_requirement_source_notes_note_id" in index_names("requirement_source_notes")
        assert "idx_test_requirement_sources_requirement_id" in index_names("test_requirement_sources")
    finally:
        connection.close()


def test_sqlite_repository_enforces_link_foreign_keys(tmp_path: Path) -> None:
    db_path = tmp_path / "specops-fk.db"
    client = make_sqlite_client(db_path)
    spec_section_id = create_spec_section(client)
    note_id = create_note(client, spec_section_id)
    requirement_id = create_requirement(client, spec_section_id, note_id)

    connection = sqlite3.connect(db_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        assert connection.execute("PRAGMA foreign_keys").fetchone() == (1,)

        raised = False
        try:
            connection.execute(
                "INSERT INTO requirement_source_notes (requirement_id, note_id, position) VALUES (?, ?, ?)",
                (requirement_id, "N-missing", 1),
            )
            connection.commit()
        except sqlite3.IntegrityError:
            raised = True

        assert raised is True
    finally:
        connection.close()


def test_sqlite_repository_cascades_link_cleanup_on_parent_delete(tmp_path: Path) -> None:
    db_path = tmp_path / "specops-cascade.db"
    client = make_sqlite_client(db_path)
    spec_section_id = create_spec_section(client)
    note_id = create_note(client, spec_section_id)
    requirement_id = create_requirement(client, spec_section_id, note_id)
    test_requirement_id = create_test_requirement(client, requirement_id)

    connection = sqlite3.connect(db_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")

        connection.execute("DELETE FROM requirements WHERE id = ?", (requirement_id,))
        connection.commit()

        requirement_note_links = connection.execute(
            "SELECT requirement_id, note_id FROM requirement_source_notes"
        ).fetchall()
        requirement_spec_links = connection.execute(
            "SELECT requirement_id, spec_id FROM requirement_source_specs"
        ).fetchall()
        test_requirement_links = connection.execute(
            "SELECT test_requirement_id, requirement_id FROM test_requirement_sources"
        ).fetchall()

        assert requirement_note_links == []
        assert requirement_spec_links == []
        assert test_requirement_links == []

        orphan_test_requirement = connection.execute(
            "SELECT id FROM test_requirements WHERE id = ?",
            (test_requirement_id,),
        ).fetchone()
        assert orphan_test_requirement == (test_requirement_id,)
    finally:
        connection.close()

