from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from specops_api.app import create_app
from specops_api.repository import InMemoryRepository


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "review_cases"


def make_memory_client() -> TestClient:
    return TestClient(create_app(InMemoryRepository()))


def load_cases() -> list[dict]:
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(FIXTURE_DIR.glob("*.json"))]


def resolve_tokens(value, tokens: dict[str, str]):
    if isinstance(value, str):
        for token, replacement in tokens.items():
            value = value.replace(token, replacement)
        return value
    if isinstance(value, list):
        return [resolve_tokens(item, tokens) for item in value]
    if isinstance(value, dict):
        return {key: resolve_tokens(item, tokens) for key, item in value.items()}
    return value


def test_review_regression_fixtures_cover_requirement_and_test_requirement_gates() -> None:
    client = make_memory_client()
    cases = load_cases()

    assert len(cases) == 2

    requirement_case = next(case for case in cases if case["expected"]["artifact_type"] == "requirement")
    failure_case = next(case for case in cases if case["expected"]["artifact_type"] == "test_requirement")

    spec_response = client.post("/spec-sections", json=requirement_case["spec_section"])
    assert spec_response.status_code == 201
    note_response = client.post("/notes", json=requirement_case["note_request"])
    assert note_response.status_code == 201
    note = note_response.json()

    requirement_request = resolve_tokens(requirement_case["requirement_request"], {"$note.id": note["id"]})
    requirement_response = client.post("/requirements", json=requirement_request)
    assert requirement_response.status_code == 201
    requirement = requirement_response.json()

    audit_request = resolve_tokens(requirement_case["audit_request"], {"$requirement.id": requirement["id"]})
    audit_response = client.post("/audit-rationales", json=audit_request)
    assert audit_response.status_code == 201
    audit_id = audit_response.json()["id"]

    patch_response = client.patch(f"/requirements/{requirement['id']}", json={"audit_rationale_id": audit_id})
    assert patch_response.status_code == 200

    submit_response = client.post(
        f"/requirements/{requirement['id']}/submit-review",
        json=requirement_case["submit_review_request"],
    )
    assert submit_response.status_code == 200
    assert submit_response.json()["status"] == "IN_REVIEW"

    review_request = resolve_tokens(requirement_case["review_request"], {"$requirement.id": requirement["id"]})
    approve_response = client.post("/reviews", json=review_request)
    assert approve_response.status_code == 201
    assert approve_response.json()["artifact"]["status"] == requirement_case["expected"]["final_status"]
    assert approve_response.json()["artifact"]["audit_rationale_id"] == audit_id

    export_request = resolve_tokens(requirement_case["export_request"], {"$requirement.id": requirement["id"]})
    export_response = client.post("/exports/codebeamer", json=export_request)
    assert export_response.status_code == 200
    assert export_response.json()["status"] == requirement_case["expected"]["export_status"]

    spec_response = client.post("/spec-sections", json=failure_case["spec_section"])
    assert spec_response.status_code == 201
    note_response = client.post("/notes", json=failure_case["note_request"])
    assert note_response.status_code == 201
    note = note_response.json()

    requirement_request = resolve_tokens(failure_case["requirement_request"], {"$note.id": note["id"]})
    requirement_response = client.post("/requirements", json=requirement_request)
    assert requirement_response.status_code == 201
    requirement = requirement_response.json()

    test_requirement_request = resolve_tokens(
        failure_case["test_requirement_request"],
        {"$requirement.id": requirement["id"]},
    )
    test_requirement_response = client.post("/test-requirements", json=test_requirement_request)
    assert test_requirement_response.status_code == 201
    test_requirement = test_requirement_response.json()

    submit_response = client.post(
        f"/test-requirements/{test_requirement['id']}/submit-review",
        json=failure_case["submit_review_request"],
    )
    assert submit_response.status_code == 200
    assert submit_response.json()["status"] == "IN_REVIEW"

    review_request = resolve_tokens(failure_case["review_request"], {"$test_requirement.id": test_requirement["id"]})
    approve_response = client.post("/reviews", json=review_request)
    assert approve_response.status_code == 409
    assert approve_response.json() == {"error": failure_case["expected"]["error"], "detail": None}
