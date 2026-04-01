# VerifyImportAI

SpecOps MVP baseline for importing real Markdown specs, extracting `spec_section` artifacts, generating requirement bundles, reviewing artifacts, and exporting downstream traces.

## Current Baseline

- FastAPI app with in-memory and SQLite repositories
- Real-spec extraction from tracked Triumph and Kawasaki Markdown fixtures
- Deterministic note / requirement / audit generation
- Review, approval, export, and downstream test-requirement generation flows
- Regression coverage for real-spec extraction, persistence, and lifecycle traces

## Fixture Policy

- Track only the fixture files needed by the current pipeline: `.md`, `*_content_list_v2.json`, and referenced `images/`
- Ignore reproducible derivative artifacts such as `*_content_list.json`, `*_middle.json`, `*_model.json`, and source/layout PDFs

## Local Setup

```bash
uv sync
python -m pytest -q
```

The repository targets Python `3.13`, which is also reflected in `.python-version`.
