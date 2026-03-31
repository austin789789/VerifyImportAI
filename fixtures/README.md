# Parser Fixtures

This directory stores `spec_section` fixture payloads for parser and generation contract tests.

Current baseline:

- `parser_sections/vehicle_speed_display.json`
- `parser_sections/door_lock_feedback.json`
- `parser_sections/diagnostic_session_timeout.json`
- `generation_cases/metric_speed_display_case.json`
- `generation_cases/door_lock_feedback_case.json`
- `generation_cases/diagnostic_timeout_case.json`

These fixtures are intentionally small but cover:

- plain paragraph extraction
- HMI plus controller cross-domain wording
- table-adjacent extraction with `parser_warnings`
- note / requirement contract regression cases built on top of stable `spec_section` samples
