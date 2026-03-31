from pathlib import Path

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


def attach_audit_rationale(client: TestClient, requirement_id: str, source_spec_id: str) -> str:
    audit_response = client.post(
        "/audit-rationales",
        json={
            "artifact_id": requirement_id,
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

    patch_response = client.patch(
        f"/requirements/{requirement_id}",
        json={"audit_rationale_id": audit_id},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["audit_rationale_id"] == audit_id
    return audit_id


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


def test_lock_conflict_flow() -> None:
    client = make_memory_client()

    first = client.post("/locks/sec_001", json={"owner_id": "user-a", "ttl_minutes": 30})
    assert first.status_code == 200

    second = client.post("/locks/sec_001", json={"owner_id": "user-b", "ttl_minutes": 30})
    assert second.status_code == 409
    assert second.json()["error"] == "Lock conflict"


def test_sqlite_repository_persists_across_app_instances(tmp_path: Path) -> None:
    db_path = tmp_path / "specops-test.db"
    client_a = make_sqlite_client(db_path)
    spec_section_id = create_spec_section(client_a)
    note_id = create_note(client_a, spec_section_id)
    requirement_id = create_requirement(client_a, spec_section_id, note_id)
    attach_audit_rationale(client_a, requirement_id, spec_section_id)

    client_b = make_sqlite_client(db_path)
    note_response = client_b.get(f"/notes/{note_id}")
    assert note_response.status_code == 200
    assert note_response.json()["id"] == note_id

    requirement_response = client_b.get(f"/requirements/{requirement_id}")
    assert requirement_response.status_code == 200
    assert requirement_response.json()["id"] == requirement_id

    trace_response = client_b.get(f"/trace/{requirement_id}")
    assert trace_response.status_code == 200
