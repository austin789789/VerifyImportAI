# SpecOps OpenAPI Notes

## Files

- `specops-api.yaml`: source-of-truth MVP API contract
- `examples/`: request and response examples for key MVP endpoints
- `../schemas/`: JSON schema drafts for artifact payloads

## Scope

This API currently covers the SpecOps MVP core plus the minimum audit path required to approve and export a requirement:

- parsed spec sections
- note creation and lookup
- requirement draft creation, patching, and review
- test requirement creation, patching, and review
- audit rationale creation and lookup
- review submission and review decisions
- section locking
- trace lookup
- Codebeamer export stub

## Excluded From This Version

- auto-fix orchestration
- signal-sync automation
- variant synchronization
- automotive-specific workflow APIs
- graph editor mutation APIs

## Local Run

Install dependencies, then run:

```bash
uv sync
uv run uvicorn main:app --reload
```

## Test Run

```bash
uv run pytest -q
```

## Key Endpoints

- `POST /spec-sections`
- `POST /notes`
- `GET /notes/{noteId}`
- `POST /requirements`
- `PATCH /requirements/{requirementId}`
- `POST /requirements/{requirementId}/submit-review`
- `POST /test-requirements`
- `PATCH /test-requirements/{testRequirementId}`
- `POST /test-requirements/{testRequirementId}/submit-review`
- `GET /test-requirements/{testRequirementId}`
- `POST /audit-rationales`
- `GET /audit-rationales/{auditRationaleId}`
- `POST /reviews`
- `POST /locks/{sectionKey}`
- `GET /trace/{artifactId}`
- `POST /exports/codebeamer`

## Design Notes

- Default persistence is now SQLite via `specops.db`.
- Dependency resolution and local execution are standardized on `uv`.
- `uv.lock` should be committed and treated as the reproducible MVP dependency baseline.
- Tests use both in-memory and temp SQLite repositories.
- Error responses are normalized to `{ error, detail }` except lock conflicts, which additionally include `current_lock`.
- Review decisions now support both `requirement` and `test_requirement` artifacts.
- The repository boundary keeps future Postgres migration isolated from route handlers.
