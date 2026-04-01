from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi import HTTPException, status

from .models import (
    AuditRationale,
    AuditSourceRef,
    CreateMarkdownExtractionRequest,
    GenerateRequirementBundleRequest,
    Note,
    Requirement,
    RequirementBundleResponse,
    RequirementTrace,
    SourceRef,
    SpecSection,
)
from .repository import Repository, next_id


REPO_ROOT = Path(__file__).resolve().parents[1]
HEADING_PATTERN = re.compile(r"^#\s+(\d+)\s+(.+?)\s*$", re.MULTILINE)
SECTION_TITLE_PATTERN = re.compile(r"^\s*(\d+)[\.\s]+(.+?)\s*$")


def extract_markdown_sections(request: CreateMarkdownExtractionRequest, repository: Repository) -> list[SpecSection]:
    markdown_path = _resolve_repo_path(request.markdown_path)
    content_list_path = markdown_path.with_name(f"{markdown_path.stem}_content_list_v2.json")
    if content_list_path.exists():
        sections = _extract_sections_from_content_list(request.document_id, content_list_path)
    else:
        sections = _extract_sections_from_markdown(request.document_id, markdown_path)
    return [repository.upsert_spec_section(section) for section in sections]


def generate_requirement_bundle(
    spec_section_id: str,
    request: GenerateRequirementBundleRequest,
    repository: Repository,
) -> RequirementBundleResponse:
    section = repository.get_spec_section(spec_section_id)
    summary = _first_sentence(section.normalized_text or section.text)
    note = repository.create_note(
        Note(
            id=next_id("N"),
            schema_version="1.0.0",
            version="v1.0",
            title=f"{section.title} note",
            summary=summary,
            source_spec_ids=[section.id],
        )
    )

    requirement = repository.create_requirement(
        Requirement(
            id=next_id("R"),
            schema_version="1.0.0",
            version="v1.0",
            title=f"{section.title} requirement",
            statement=_derive_requirement_statement(section),
            source_spec_ids=[section.id],
            source_note_ids=[note.id],
            compliance=request.compliance,
            trace=RequirementTrace(graph_node_id=next_id("GN")),
            variant_scope=request.variant_scope,
        )
    )

    audit = repository.create_audit_rationale(
        AuditRationale(
            id=next_id("AR"),
            artifact_id=requirement.id,
            source_refs=[
                AuditSourceRef(
                    spec_id=section.id,
                    page=source_ref.page,
                    bbox=source_ref.bbox,
                )
                for source_ref in section.source_refs
            ],
            prompt_version=request.prompt_version,
            model_version=request.model_version,
        )
    )
    requirement = repository.patch_requirement(requirement.id, None, None, None, audit.id)
    return RequirementBundleResponse(note=note, requirement=requirement, audit_rationale=audit)


def _resolve_repo_path(raw_path: str) -> Path:
    path = Path(raw_path)
    resolved = path.resolve(strict=True)
    try:
        resolved.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="markdown_path must stay within the repo workspace") from exc
    if resolved.suffix.lower() != ".md":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="markdown_path must point to a Markdown file")
    return resolved


def _extract_sections_from_markdown(document_id: str, markdown_path: Path) -> list[SpecSection]:
    content = markdown_path.read_text(encoding="utf-8")
    matches = list(HEADING_PATTERN.finditer(content))
    if not matches:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Markdown spec does not contain top-level numbered headings")

    sections: list[SpecSection] = []
    for index, match in enumerate(matches):
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        raw_body = content[match.end():next_start].strip()
        section_number = int(match.group(1))
        sections.append(
            SpecSection(
                id=f"S-{document_id}-sec_{section_number:03d}",
                schema_version="1.0.0",
                version="v1.0",
                section_key=f"sec_{section_number:03d}",
                title=match.group(2).strip(),
                text=raw_body,
                normalized_text=_normalize_text(raw_body),
                parser_warnings=_collect_parser_warnings(raw_body),
                source_refs=[SourceRef(page=1, bbox=None, table_ref=None)],
            )
        )
    return sections


def _extract_sections_from_content_list(document_id: str, content_list_path: Path) -> list[SpecSection]:
    pages = json.loads(content_list_path.read_text(encoding="utf-8"))
    flat_items: list[tuple[int, dict]] = []
    for page_index, page_items in enumerate(pages):
        for item in page_items:
            flat_items.append((page_index + 1, item))

    titles: list[tuple[int, int, str]] = []
    for flat_index, (_, item) in enumerate(flat_items):
        if item.get("type") != "title":
            continue
        title = _extract_title_text(item)
        match = SECTION_TITLE_PATTERN.match(title)
        if not match:
            continue
        titles.append((flat_index, int(match.group(1)), match.group(2).strip()))

    if not titles:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Content list does not contain numbered title blocks")

    sections: list[SpecSection] = []
    for title_index, (start_flat_index, section_number, title) in enumerate(titles):
        end_flat_index = titles[title_index + 1][0] if title_index + 1 < len(titles) else len(flat_items)
        section_items = flat_items[start_flat_index + 1 : end_flat_index]
        page_bboxes: dict[int, list[float]] = {}
        warnings: set[str] = set()
        text_chunks: list[str] = []

        title_page, title_item = flat_items[start_flat_index]
        _merge_bbox(page_bboxes, title_page, title_item.get("bbox"))
        for page_number, item in section_items:
            chunk, item_warnings = _extract_item_text(item)
            if chunk:
                text_chunks.append(chunk)
            warnings.update(item_warnings)
            _merge_bbox(page_bboxes, page_number, item.get("bbox"))

        raw_text = "\n\n".join(chunk for chunk in text_chunks if chunk).strip()
        sections.append(
            SpecSection(
                id=f"S-{document_id}-sec_{section_number:03d}",
                schema_version="1.0.0",
                version="v1.0",
                section_key=f"sec_{section_number:03d}",
                title=title,
                text=raw_text,
                normalized_text=_normalize_text(raw_text),
                parser_warnings=sorted(warnings),
                source_refs=[
                    SourceRef(page=page_number, bbox=page_bboxes[page_number], table_ref=None)
                    for page_number in sorted(page_bboxes)
                ],
            )
        )
    return sections


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _collect_parser_warnings(text: str) -> list[str]:
    warnings: list[str] = []
    if "<table>" in text:
        warnings.append("table content retained as inline html")
    if "![](images/" in text:
        warnings.append("image reference retained as markdown")
    if "????" in text:
        warnings.append("unresolved source tokens retained from markdown")
    return warnings


def _first_sentence(text: str) -> str:
    normalized = _normalize_text(text)
    if not normalized:
        return "Empty section imported from markdown spec."
    parts = re.split(r"(?<=[.!?])\s+", normalized, maxsplit=1)
    return parts[0]


def _derive_requirement_statement(section: SpecSection) -> str:
    candidates = re.split(r"(?<=[.!?])\s+", _normalize_text(section.text))
    for candidate in candidates:
        if " shall " in f" {candidate.lower()} ":
            return candidate.strip()
    first_sentence = _first_sentence(section.text)
    if _looks_like_japanese_requirement(first_sentence):
        return first_sentence
    if first_sentence.endswith("."):
        return first_sentence[:-1] + " shall be implemented."
    return first_sentence + " shall be implemented."


def _looks_like_japanese_requirement(text: str) -> bool:
    normalized = text.strip()
    if not normalized:
        return False
    if re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", normalized) is None:
        return False
    return normalized.endswith("こと") or normalized.endswith("こと。")


def _extract_title_text(item: dict) -> str:
    title_parts = item.get("content", {}).get("title_content", [])
    return _normalize_text(" ".join(part.get("content", "") for part in title_parts))


def _extract_item_text(item: dict) -> tuple[str, set[str]]:
    item_type = item.get("type")
    content = item.get("content", {})
    warnings: set[str] = set()

    if item_type == "paragraph":
        parts = content.get("paragraph_content", [])
        return _normalize_text(" ".join(part.get("content", "") for part in parts)), warnings
    if item_type == "table":
        warnings.add("table content retained as inline html")
        return content.get("html", "").strip(), warnings
    if item_type == "math":
        warnings.add("math content retained as extracted text")
        return content.get("math_content", "").strip(), warnings
    if item_type == "image":
        warnings.add("image reference retained as markdown")
        path = content.get("image_source", {}).get("path")
        return (f"![]({path})" if path else ""), warnings
    if item_type in {"list", "list_item"}:
        list_content = content.get("list_content", []) or content.get("item_content", [])
        return _normalize_text(" ".join(part.get("content", "") for part in list_content)), warnings
    return "", warnings


def _merge_bbox(page_bboxes: dict[int, list[float]], page_number: int, bbox: list[float] | None) -> None:
    if not bbox:
        return
    existing = page_bboxes.get(page_number)
    if existing is None:
        page_bboxes[page_number] = list(bbox)
        return
    page_bboxes[page_number] = [
        min(existing[0], bbox[0]),
        min(existing[1], bbox[1]),
        max(existing[2], bbox[2]),
        max(existing[3], bbox[3]),
    ]
