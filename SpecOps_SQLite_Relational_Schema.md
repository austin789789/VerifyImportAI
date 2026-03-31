# SpecOps SQLite Relational Schema

This note documents the current SQLite persistence layout used by the SpecOps MVP API after the move away from `payload` blob storage.

## Purpose

The relational SQLite layer exists to make the MVP easier to inspect, migrate, and validate. The API contract is unchanged, but storage now exposes stable columns for the main workflow artifacts and dedicated link tables for ordered relationships.

## Main Tables

`spec_sections`
- Stores parsed source sections.
- Important columns: `id`, `status`, `section_key`, `title`, `text`, `created_at`, `updated_at`.
- JSON columns retained where a fully relational split is not yet worth the cost: `parser_warnings_json`, `source_refs_json`.

`notes`
- Stores analyst notes derived from spec sections.
- Important columns: `id`, `status`, `title`, `summary`, `created_at`, `updated_at`.

`requirements`
- Stores reviewable requirements.
- Important columns: `id`, `status`, `title`, `statement`, `variant_scope`, `audit_rationale_id`.
- Compliance and graph metadata remain explicit columns: `classes_json`, `asil`, `cal`, `graph_node_id`.

`test_requirements`
- Stores downstream verification artifacts.
- Important columns: `id`, `status`, `statement`, `audit_rationale_id`, `created_at`, `updated_at`.
- Acceptance criteria are stored in `acceptance_criteria_json`.

`audit_rationales`
- Stores rationale records linked to a requirement or test requirement.
- Important columns: `id`, `artifact_id`, `prompt_version`, `model_version`, `created_at`.

`reviews`
- Stores approve/reject decisions.
- Important columns: `id`, `artifact_id`, `decision`, `reviewer_id`, `reviewed_at`.
- `rejection_tags_json` remains JSON because the MVP does not yet query tags relationally.

`locks`
- Stores section edit locks.
- Important columns: `section_key`, `owner_id`, `expires_at`, `status`.

`trace_entries`
- Stores artifact-level trace metadata.
- Important columns: `artifact_id`, `artifact_type`, `status`, `version`, `schema_version`, `last_review_id`, `audit_rationale_id`.
- Upstream and downstream links are derived from link tables at read time.

## Link Tables

`note_source_specs`
- Ordered mapping from note to source spec sections.
- Columns: `note_id`, `spec_id`, `position`.

`requirement_source_specs`
- Ordered mapping from requirement to source spec sections.
- Columns: `requirement_id`, `spec_id`, `position`.

`requirement_source_notes`
- Ordered mapping from requirement to source notes.
- Columns: `requirement_id`, `note_id`, `position`.

`test_requirement_sources`
- Ordered mapping from test requirement to source requirements.
- Columns: `test_requirement_id`, `requirement_id`, `position`.

## Migration Behavior

When `SQLiteRepository` opens a database and detects the old `payload` schema in `requirements`, it performs an in-place migration:

1. Load legacy rows from all payload tables into Pydantic models.
2. Drop the old payload tables.
3. Create the relational tables.
4. Rehydrate the relational rows and ordered link tables from the loaded models.

This migration is covered by tests using a hand-built legacy SQLite fixture.

## Current Limits

- Foreign keys are only enforced on the ordered link tables.
- Some structured fields remain JSON-backed for speed of implementation.
- Trace edges are recomputed from link tables rather than normalized into separate edge tables.
- This schema is still an MVP persistence layer, not a final production database design.
- Polymorphic relationships such as `audit_rationales.artifact_id` are still application-enforced rather than database-enforced.

## Operational Checks

Current tests verify:

- relational columns exist instead of `payload`
- legacy payload databases migrate correctly
- link-table rows are written with the expected positions
- link-table foreign key violations are rejected by SQLite
- query-supporting indexes are created for current lookup paths
- `PRAGMA integrity_check` returns `ok`

## Current Index Baseline

Current SQLite indexes are intentionally small and only cover the query paths used by the MVP repository:

- `spec_sections(section_key)`
- `spec_sections(status)`
- `notes(status)`
- `requirements(status)`
- `requirements(variant_scope)`
- `requirements(audit_rationale_id)`
- `test_requirements(status)`
- `test_requirements(audit_rationale_id)`
- `audit_rationales(artifact_id)`
- `reviews(artifact_id)`
- `trace_entries(artifact_type)`
- `note_source_specs(spec_id)`
- `requirement_source_specs(spec_id)`
- `requirement_source_notes(note_id)`
- `test_requirement_sources(requirement_id)`

## Foreign Key Baseline

SQLite foreign key enforcement is enabled at connection start with `PRAGMA foreign_keys = ON`.

Current enforced relationships:

- `note_source_specs.note_id -> notes.id`
- `note_source_specs.spec_id -> spec_sections.id`
- `requirement_source_specs.requirement_id -> requirements.id`
- `requirement_source_specs.spec_id -> spec_sections.id`
- `requirement_source_notes.requirement_id -> requirements.id`
- `requirement_source_notes.note_id -> notes.id`
- `test_requirement_sources.test_requirement_id -> test_requirements.id`
- `test_requirement_sources.requirement_id -> requirements.id`

These constraints currently use `ON DELETE CASCADE` so that future cleanup paths can remove parent artifacts without leaving orphaned links.

The next step, if needed, is to extend constraint coverage where the data model is no longer polymorphic and then review whether composite indexes are justified by real query volume.
