from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from specops_api.app import create_app
from specops_api.models import SpecSection
from specops_api.repository import InMemoryRepository


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "parser_sections"


def make_memory_client() -> TestClient:
    return TestClient(create_app(InMemoryRepository()))


def load_fixture_payloads() -> list[dict]:
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(FIXTURE_DIR.glob("*.json"))]


def test_parser_fixtures_validate_as_spec_sections() -> None:
    payloads = load_fixture_payloads()

    assert len(payloads) == 3
    assert len({payload["id"] for payload in payloads}) == len(payloads)
    assert len({payload["section_key"] for payload in payloads}) == len(payloads)

    for payload in payloads:
        section = SpecSection.model_validate(payload)
        assert section.artifact_type == "spec_section"
        assert section.source_refs


def test_parser_fixture_set_can_be_ingested_and_filtered() -> None:
    client = make_memory_client()
    payloads = load_fixture_payloads()

    for payload in payloads:
        response = client.post("/spec-sections", json=payload)
        assert response.status_code == 201
        assert response.json()["id"] == payload["id"]

    list_response = client.get("/spec-sections")
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()["items"]] == [payload["id"] for payload in payloads]

    filtered_response = client.get("/spec-sections", params={"section_key": "sec_027"})
    assert filtered_response.status_code == 200
    filtered_items = filtered_response.json()["items"]
    assert len(filtered_items) == 1
    assert filtered_items[0]["id"] == "S-oemx-diag-v3_0-sec_027"
    assert filtered_items[0]["parser_warnings"] == ["timeout value extracted from adjacent table row"]
