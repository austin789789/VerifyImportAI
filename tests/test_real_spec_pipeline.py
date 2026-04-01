from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from specops_api.app import create_app
from specops_api.repository import InMemoryRepository, SQLiteRepository


ROOT = Path(__file__).resolve().parents[1]
TRIUMPH_SPEC_PATH = ROOT / "Triumph" / "S6867_07" / "S6867_07.md"
KAWASAKI_SPEC_PATH = ROOT / "Kawasaki" / "全体要件" / "全体要件.md"


def make_memory_client() -> TestClient:
    return TestClient(create_app(InMemoryRepository()))


def make_sqlite_client(db_path: Path) -> TestClient:
    return TestClient(create_app(SQLiteRepository(db_path)))


def test_extract_markdown_sections_from_real_spec_fixture() -> None:
    client = make_memory_client()

    response = client.post(
        "/pipelines/markdown-specs/extract",
        json={
            "document_id": "triumph-s6867-07",
            "markdown_path": str(TRIUMPH_SPEC_PATH),
        },
    )

    assert response.status_code == 201
    payload = response.json()
    items = payload["items"]

    assert len(items) == 8
    assert items[0]["id"] == "S-triumph-s6867-07-sec_001"
    assert items[0]["title"] == "Overview"
    assert items[0]["source_refs"][0]["page"] == 1
    assert items[1]["section_key"] == "sec_002"
    assert items[1]["title"] == "Input Signals"
    assert items[6]["section_key"] == "sec_007"
    assert items[6]["title"] == "Operation"
    assert "Range to Empty calculation shall be carried out" in items[6]["text"]
    assert [ref["page"] for ref in items[6]["source_refs"]] == [2, 3, 4]


def test_generate_requirement_bundle_from_extracted_real_spec_section() -> None:
    client = make_memory_client()
    extract_response = client.post(
        "/pipelines/markdown-specs/extract",
        json={
            "document_id": "triumph-s6867-07",
            "markdown_path": str(TRIUMPH_SPEC_PATH),
        },
    )
    assert extract_response.status_code == 201

    section_id = "S-triumph-s6867-07-sec_007"
    bundle_response = client.post(
        f"/pipelines/spec-sections/{section_id}/generate-requirement-bundle",
        json={
            "prompt_version": "deterministic-note-v1",
            "model_version": "rule-based-generator-v1",
            "variant_scope": "base",
        },
    )

    assert bundle_response.status_code == 201
    payload = bundle_response.json()

    note = payload["note"]
    requirement = payload["requirement"]
    audit = payload["audit_rationale"]

    assert note["source_spec_ids"] == [section_id]
    assert "Operation" in note["title"]
    assert "Range to Empty calculation" in note["summary"]

    assert requirement["source_spec_ids"] == [section_id]
    assert requirement["source_note_ids"] == [note["id"]]
    assert requirement["variant_scope"] == "base"
    assert requirement["audit_rationale_id"] == audit["id"]
    assert "shall" in requirement["statement"]

    assert audit["artifact_id"] == requirement["id"]
    assert audit["prompt_version"] == "deterministic-note-v1"
    assert audit["model_version"] == "rule-based-generator-v1"
    assert [ref["spec_id"] for ref in audit["source_refs"]] == [section_id, section_id, section_id]
    assert [ref["page"] for ref in audit["source_refs"]] == [2, 3, 4]

    trace_response = client.get(f"/trace/{requirement['id']}")
    assert trace_response.status_code == 200
    trace = trace_response.json()
    assert section_id in trace["upstream_ids"]
    assert note["id"] in trace["upstream_ids"]
    assert trace["audit_rationale_id"] == audit["id"]

def test_real_spec_requirement_bundle_can_be_reviewed_approved_and_exported() -> None:
    client = make_memory_client()
    extract_response = client.post(
        "/pipelines/markdown-specs/extract",
        json={
            "document_id": "triumph-s6867-07",
            "markdown_path": str(TRIUMPH_SPEC_PATH),
        },
    )
    assert extract_response.status_code == 201

    section_id = "S-triumph-s6867-07-sec_007"
    bundle_response = client.post(
        f"/pipelines/spec-sections/{section_id}/generate-requirement-bundle",
        json={
            "prompt_version": "deterministic-note-v1",
            "model_version": "rule-based-generator-v1",
            "variant_scope": "base",
        },
    )
    assert bundle_response.status_code == 201

    requirement_id = bundle_response.json()["requirement"]["id"]
    audit_id = bundle_response.json()["audit_rationale"]["id"]

    submit_response = client.post(
        f"/requirements/{requirement_id}/submit-review",
        json={"reviewer_id": "reviewer-a", "review_note": "ready from real spec"},
    )
    assert submit_response.status_code == 200
    assert submit_response.json()["status"] == "IN_REVIEW"

    queue_response = client.get("/requirements", params={"review_queue": "pending_review"})
    assert queue_response.status_code == 200
    pending_ids = [item["id"] for item in queue_response.json()["items"]]
    assert requirement_id in pending_ids

    approve_response = client.post(
        "/reviews",
        json={
            "artifact_id": requirement_id,
            "decision": "APPROVED",
            "reviewer_id": "reviewer-a",
            "review_note": "Approved from real markdown pipeline.",
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

    trace_response = client.get(f"/trace/{requirement_id}")
    assert trace_response.status_code == 200
    trace = trace_response.json()
    assert trace["status"] == "APPROVED"
    assert trace["audit_rationale_id"] == audit_id
    assert trace["last_review_id"] is not None


def test_extract_and_generate_bundle_from_kawasaki_japanese_spec() -> None:
    client = make_memory_client()

    response = client.post(
        "/pipelines/markdown-specs/extract",
        json={
            "document_id": "kawasaki-global-req",
            "markdown_path": str(KAWASAKI_SPEC_PATH),
        },
    )

    assert response.status_code == 201
    items = response.json()["items"]
    assert len(items) == 5
    assert items[0]["id"] == "S-kawasaki-global-req-sec_001"
    assert items[0]["title"] == "テストスペック"
    assert items[0]["source_refs"][0]["page"] == 1

    section_id = "S-kawasaki-global-req-sec_001"
    bundle_response = client.post(
        f"/pipelines/spec-sections/{section_id}/generate-requirement-bundle",
        json={
            "prompt_version": "deterministic-note-v1",
            "model_version": "rule-based-generator-v1",
            "variant_scope": "base",
        },
    )

    assert bundle_response.status_code == 201
    payload = bundle_response.json()
    assert payload["note"]["summary"] == "テストスペック49245-1528を満足すること"
    assert payload["requirement"]["statement"] == "テストスペック49245-1528を満足すること"
    assert payload["audit_rationale"]["source_refs"][0]["page"] == 1


def test_approved_real_spec_requirement_can_generate_downstream_test_requirement() -> None:
    client = make_memory_client()
    extract_response = client.post(
        "/pipelines/markdown-specs/extract",
        json={
            "document_id": "triumph-s6867-07",
            "markdown_path": str(TRIUMPH_SPEC_PATH),
        },
    )
    assert extract_response.status_code == 201

    section_id = "S-triumph-s6867-07-sec_007"
    bundle_response = client.post(
        f"/pipelines/spec-sections/{section_id}/generate-requirement-bundle",
        json={
            "prompt_version": "deterministic-note-v1",
            "model_version": "rule-based-generator-v1",
            "variant_scope": "base",
        },
    )
    assert bundle_response.status_code == 201
    payload = bundle_response.json()
    requirement_id = payload["requirement"]["id"]

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
    assert "Range to Empty calculation shall be carried out" in generated["statement"]

    requirement_trace = client.get(f"/trace/{requirement_id}")
    assert requirement_trace.status_code == 200
    assert generated["id"] in requirement_trace.json()["downstream_ids"]

    test_requirement_trace = client.get(f"/trace/{generated['id']}")
    assert test_requirement_trace.status_code == 200
    assert requirement_id in test_requirement_trace.json()["upstream_ids"]


def test_real_spec_pipeline_persists_across_sqlite_app_instances(tmp_path: Path) -> None:
    db_path = tmp_path / "real-spec-pipeline.db"
    client_a = make_sqlite_client(db_path)

    extract_response = client_a.post(
        "/pipelines/markdown-specs/extract",
        json={
            "document_id": "triumph-s6867-07",
            "markdown_path": str(TRIUMPH_SPEC_PATH),
        },
    )
    assert extract_response.status_code == 201

    section_id = "S-triumph-s6867-07-sec_007"
    bundle_response = client_a.post(
        f"/pipelines/spec-sections/{section_id}/generate-requirement-bundle",
        json={
            "prompt_version": "deterministic-note-v1",
            "model_version": "rule-based-generator-v1",
            "variant_scope": "base",
        },
    )
    assert bundle_response.status_code == 201
    payload = bundle_response.json()

    note_id = payload["note"]["id"]
    requirement_id = payload["requirement"]["id"]
    audit_id = payload["audit_rationale"]["id"]

    client_b = make_sqlite_client(db_path)

    note_response = client_b.get(f"/notes/{note_id}")
    assert note_response.status_code == 200
    assert note_response.json()["source_spec_ids"] == [section_id]

    requirement_response = client_b.get(f"/requirements/{requirement_id}")
    assert requirement_response.status_code == 200
    assert requirement_response.json()["audit_rationale_id"] == audit_id

    audit_response = client_b.get(f"/audit-rationales/{audit_id}")
    assert audit_response.status_code == 200
    assert [ref["page"] for ref in audit_response.json()["source_refs"]] == [2, 3, 4]

    trace_response = client_b.get(f"/trace/{requirement_id}")
    assert trace_response.status_code == 200
    trace = trace_response.json()
    assert section_id in trace["upstream_ids"]
    assert note_id in trace["upstream_ids"]
    assert trace["audit_rationale_id"] == audit_id
