# SpecOps OpenAPI Notes

## Files

- `specops-api.yaml`: source-of-truth MVP API contract
- `examples/`: request and response examples for key MVP endpoints
- `../schemas/`: JSON schema drafts for artifact payloads

## Scope

This API currently covers the SpecOps MVP core plus the minimum audit path required to approve and export a requirement:

- parsed spec sections
- note creation and lookup
- requirement draft creation and patching
- test requirement creation and lookup
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
uvicorn main:app --reload
```

## Test Run

```bash
pytest
```

## Key Endpoints

- `POST /spec-sections`
- `POST /notes`
- `GET /notes/{noteId}`
- `POST /requirements`
- `PATCH /requirements/{requirementId}`
- `POST /test-requirements`
- `GET /test-requirements/{testRequirementId}`
- `POST /audit-rationales`
- `GET /audit-rationales/{auditRationaleId}`
- `POST /requirements/{requirementId}/submit-review`
- `POST /reviews`
- `POST /locks/{sectionKey}`
- `GET /trace/{artifactId}`
- `POST /exports/codebeamer`

## Design Notes

- Default persistence is now SQLite via `specops.db`.
- Tests use both in-memory and temp SQLite repositories.
- Error responses are normalized to `{ error, detail }` except lock conflicts, which additionally include `current_lock`.
- The repository boundary keeps future Postgres migration isolated from route handlers.
