from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from specops_api.app import create_app
from specops_api.repository import InMemoryRepository, SQLiteRepository
from specops_api import pipeline as pipeline_module


ROOT = Path(__file__).resolve().parents[1]
TRIUMPH_SPEC_PATH = ROOT / "Triumph" / "S6867_07" / "S6867_07.md"
KAWASAKI_SPEC_PATH = ROOT / "Kawasaki" / "全体要件" / "全体要件.md"


def make_memory_client() -> TestClient:
    return TestClient(create_app(InMemoryRepository()))


def make_sqlite_client(db_path: Path) -> TestClient:
    return TestClient(create_app(SQLiteRepository(db_path)))


def _content_list_image_paths(content_list_path: Path) -> set[Path]:
    pages = json.loads(content_list_path.read_text(encoding="utf-8"))
    image_paths: set[Path] = set()
    for page in pages:
        for item in page:
            raw_path = item.get("content", {}).get("image_source", {}).get("path")
            if raw_path:
                image_paths.add(content_list_path.parent / raw_path)
    return image_paths


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


def test_tracked_real_spec_image_references_exist() -> None:
    tracked_refs = _content_list_image_paths(TRIUMPH_SPEC_PATH.with_name("S6867_07_content_list_v2.json"))
    tracked_refs.update(_content_list_image_paths(KAWASAKI_SPEC_PATH.with_name("全体要件_content_list_v2.json")))

    assert tracked_refs
    missing_refs = sorted(str(path) for path in tracked_refs if not path.exists())
    assert missing_refs == []


def test_triumph_real_spec_extraction_retains_equations_as_math_warnings() -> None:
    client = make_memory_client()

    response = client.post(
        "/pipelines/markdown-specs/extract",
        json={
            "document_id": "triumph-s6867-07",
            "markdown_path": str(TRIUMPH_SPEC_PATH),
        },
    )

    assert response.status_code == 201
    items = response.json()["items"]
    operation = items[6]

    assert operation["section_key"] == "sec_007"
    assert "math content retained as extracted text" in operation["parser_warnings"]
    assert "D i s t _ {M a x _ {m i l e s}}" in operation["text"]
    assert "D i s t _ {C a l c}" in operation["text"]


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


def test_kawasaki_real_spec_extraction_retains_table_image_and_math_content() -> None:
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
    battery_instant_drop = items[4]

    assert battery_instant_drop["section_key"] == "sec_005"
    assert "image reference retained as markdown" in battery_instant_drop["parser_warnings"]
    assert "math content retained as extracted text" in battery_instant_drop["parser_warnings"]
    assert "![](images/" in battery_instant_drop["text"]
    assert "\\mathrm {U B} = 1 2 \\mathrm {V}" in battery_instant_drop["text"]


def test_kawasaki_real_spec_bundle_can_flow_through_review_export_and_test_generation() -> None:
    client = make_memory_client()

    extract_response = client.post(
        "/pipelines/markdown-specs/extract",
        json={
            "document_id": "kawasaki-global-req",
            "markdown_path": str(KAWASAKI_SPEC_PATH),
        },
    )
    assert extract_response.status_code == 201

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
    requirement_id = payload["requirement"]["id"]
    audit_id = payload["audit_rationale"]["id"]

    submit_response = client.post(
        f"/requirements/{requirement_id}/submit-review",
        json={"reviewer_id": "reviewer-a", "review_note": "ready from kawasaki spec"},
    )
    assert submit_response.status_code == 200
    assert submit_response.json()["status"] == "IN_REVIEW"

    approve_response = client.post(
        "/reviews",
        json={
            "artifact_id": requirement_id,
            "decision": "APPROVED",
            "reviewer_id": "reviewer-a",
            "review_note": "Approved from Kawasaki markdown pipeline.",
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

    generate_response = client.post(f"/requirements/{requirement_id}/generate-test-requirement")
    assert generate_response.status_code == 201
    generated = generate_response.json()
    assert generated["artifact_type"] == "test_requirement"
    assert generated["source_requirement_ids"] == [requirement_id]
    assert generated["statement"].startswith("Verify:")
    assert "テストスペック49245-1528を満足すること" in generated["statement"]


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


def test_kawasaki_real_spec_pipeline_persists_and_generates_downstream_artifacts_in_sqlite(tmp_path: Path) -> None:
    db_path = tmp_path / "kawasaki-real-spec-pipeline.db"
    client_a = make_sqlite_client(db_path)

    extract_response = client_a.post(
        "/pipelines/markdown-specs/extract",
        json={
            "document_id": "kawasaki-global-req",
            "markdown_path": str(KAWASAKI_SPEC_PATH),
        },
    )
    assert extract_response.status_code == 201

    section_id = "S-kawasaki-global-req-sec_001"
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

    requirement_id = payload["requirement"]["id"]
    note_id = payload["note"]["id"]
    audit_id = payload["audit_rationale"]["id"]

    submit_response = client_a.post(
        f"/requirements/{requirement_id}/submit-review",
        json={"reviewer_id": "reviewer-a"},
    )
    assert submit_response.status_code == 200

    approve_response = client_a.post(
        "/reviews",
        json={
            "artifact_id": requirement_id,
            "decision": "APPROVED",
            "reviewer_id": "reviewer-a",
            "review_note": "Approved from Kawasaki sqlite pipeline.",
        },
    )
    assert approve_response.status_code == 201

    generate_response = client_a.post(f"/requirements/{requirement_id}/generate-test-requirement")
    assert generate_response.status_code == 201
    test_requirement_id = generate_response.json()["id"]

    client_b = make_sqlite_client(db_path)

    note_response = client_b.get(f"/notes/{note_id}")
    assert note_response.status_code == 200
    assert note_response.json()["source_spec_ids"] == [section_id]

    requirement_response = client_b.get(f"/requirements/{requirement_id}")
    assert requirement_response.status_code == 200
    assert requirement_response.json()["status"] == "APPROVED"
    assert requirement_response.json()["audit_rationale_id"] == audit_id

    audit_response = client_b.get(f"/audit-rationales/{audit_id}")
    assert audit_response.status_code == 200
    assert audit_response.json()["source_refs"][0]["spec_id"] == section_id
    assert audit_response.json()["source_refs"][0]["page"] == 1

    test_requirement_response = client_b.get(f"/test-requirements/{test_requirement_id}")
    assert test_requirement_response.status_code == 200
    assert test_requirement_response.json()["source_requirement_ids"] == [requirement_id]
    assert "テストスペック49245-1528を満足すること" in test_requirement_response.json()["statement"]

    requirement_trace = client_b.get(f"/trace/{requirement_id}")
    assert requirement_trace.status_code == 200
    trace = requirement_trace.json()
    assert note_id in trace["upstream_ids"]
    assert section_id in trace["upstream_ids"]
    assert test_requirement_id in trace["downstream_ids"]
    assert trace["audit_rationale_id"] == audit_id


def test_generated_real_spec_test_requirement_can_be_approved_in_sqlite_without_manual_audit_patch(tmp_path: Path) -> None:
    db_path = tmp_path / "generated-test-requirement-audit.db"
    client = make_sqlite_client(db_path)

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

    submit_requirement = client.post(
        f"/requirements/{requirement_id}/submit-review",
        json={"reviewer_id": "reviewer-a"},
    )
    assert submit_requirement.status_code == 200

    approve_requirement = client.post(
        "/reviews",
        json={
            "artifact_id": requirement_id,
            "decision": "APPROVED",
            "reviewer_id": "reviewer-a",
            "review_note": "Approved for downstream generation.",
        },
    )
    assert approve_requirement.status_code == 201

    generate_test_requirement = client.post(f"/requirements/{requirement_id}/generate-test-requirement")
    assert generate_test_requirement.status_code == 201
    generated = generate_test_requirement.json()
    test_requirement_id = generated["id"]
    assert generated["audit_rationale_id"] is not None

    submit_test_requirement = client.post(
        f"/test-requirements/{test_requirement_id}/submit-review",
        json={"reviewer_id": "reviewer-a"},
    )
    assert submit_test_requirement.status_code == 200

    approve_test_requirement = client.post(
        "/reviews",
        json={
            "artifact_id": test_requirement_id,
            "decision": "APPROVED",
            "reviewer_id": "reviewer-a",
            "review_note": "Approved generated test requirement.",
        },
    )
    assert approve_test_requirement.status_code == 201
    assert approve_test_requirement.json()["artifact"]["status"] == "APPROVED"
    assert approve_test_requirement.json()["artifact"]["audit_rationale_id"] == generated["audit_rationale_id"]


def test_generated_real_spec_test_requirement_can_be_approved_in_memory_without_manual_audit_patch() -> None:
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

    submit_requirement = client.post(
        f"/requirements/{requirement_id}/submit-review",
        json={"reviewer_id": "reviewer-a"},
    )
    assert submit_requirement.status_code == 200

    approve_requirement = client.post(
        "/reviews",
        json={
            "artifact_id": requirement_id,
            "decision": "APPROVED",
            "reviewer_id": "reviewer-a",
            "review_note": "Approved for downstream generation.",
        },
    )
    assert approve_requirement.status_code == 201

    generate_test_requirement = client.post(f"/requirements/{requirement_id}/generate-test-requirement")
    assert generate_test_requirement.status_code == 201
    generated = generate_test_requirement.json()
    test_requirement_id = generated["id"]
    assert generated["audit_rationale_id"] is not None

    submit_test_requirement = client.post(
        f"/test-requirements/{test_requirement_id}/submit-review",
        json={"reviewer_id": "reviewer-a"},
    )
    assert submit_test_requirement.status_code == 200

    approve_test_requirement = client.post(
        "/reviews",
        json={
            "artifact_id": test_requirement_id,
            "decision": "APPROVED",
            "reviewer_id": "reviewer-a",
            "review_note": "Approved generated test requirement.",
        },
    )
    assert approve_test_requirement.status_code == 201
    assert approve_test_requirement.json()["artifact"]["status"] == "APPROVED"
    assert approve_test_requirement.json()["artifact"]["audit_rationale_id"] == generated["audit_rationale_id"]


def test_markdown_extraction_rejects_paths_outside_repo() -> None:
    client = make_memory_client()
    outside_path = Path.cwd().anchor + "outside-spec.md"

    response = client.post(
        "/pipelines/markdown-specs/extract",
        json={
            "document_id": "outside-doc",
            "markdown_path": outside_path,
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "error": "markdown_path must stay within the repo workspace",
        "detail": None,
    }


def test_markdown_only_fallback_extraction_without_content_list(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = make_memory_client()
    markdown_path = tmp_path / "fallback-spec.md"
    markdown_path.write_text(
        "# 1 Scope\n\nThe system shall support fallback extraction.\n\n# 2 Constraints\n\nThe device shall remain deterministic.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(pipeline_module, "REPO_ROOT", tmp_path)

    response = client.post(
        "/pipelines/markdown-specs/extract",
        json={
            "document_id": "fallback-doc",
            "markdown_path": str(markdown_path),
        },
    )

    assert response.status_code == 201
    items = response.json()["items"]
    assert len(items) == 2
    assert items[0]["id"] == "S-fallback-doc-sec_001"
    assert items[0]["title"] == "Scope"
    assert items[0]["source_refs"] == [{"page": 1, "bbox": None, "table_ref": None}]
    assert items[1]["id"] == "S-fallback-doc-sec_002"
    assert items[1]["title"] == "Constraints"
