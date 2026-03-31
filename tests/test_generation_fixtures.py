from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from specops_api.app import create_app
from specops_api.repository import InMemoryRepository


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "generation_cases"


def make_memory_client() -> TestClient:
    return TestClient(create_app(InMemoryRepository()))


def load_cases() -> list[dict]:
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(FIXTURE_DIR.glob("*.json"))]


def test_generation_fixture_chain_runs_through_note_and_requirement_contracts() -> None:
    client = make_memory_client()
    cases = load_cases()

    assert len(cases) == 3

    for case in cases:
        spec_response = client.post("/spec-sections", json=case["spec_section"])
        assert spec_response.status_code == 201
        spec_id = spec_response.json()["id"]

        note_response = client.post("/notes", json=case["note_request"])
        assert note_response.status_code == 201
        note = note_response.json()

        requirement_request = json.loads(json.dumps(case["requirement_request"]).replace("$note.id", note["id"]))
        requirement_response = client.post("/requirements", json=requirement_request)
        assert requirement_response.status_code == 201
        requirement = requirement_response.json()

        assert note["source_spec_ids"] == [spec_id]
        assert note["summary"] == case["expected"]["note_summary"]
        assert requirement["source_spec_ids"] == [spec_id]
        assert requirement["source_note_ids"] == [note["id"]]
        assert requirement["title"] == case["expected"]["requirement_title"]
        assert requirement["variant_scope"] == case["expected"]["requirement_variant_scope"]
        assert requirement["trace"]["graph_node_id"].startswith(case["expected"]["trace_graph_node_prefix"])


def test_generation_fixtures_are_queryable_by_source_spec() -> None:
    client = make_memory_client()
    cases = load_cases()

    for case in cases:
        client.post("/spec-sections", json=case["spec_section"])
        client.post("/notes", json=case["note_request"])

    response = client.get("/notes", params={"source_spec_id": "S-oemx-diag-v3_0-sec_027"})
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["title"] == "Diagnostic timeout note"
