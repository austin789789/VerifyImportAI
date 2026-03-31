# SpecOps P0 Jira / ClickUp Tickets

> 版本: v1.0
> 角色: 可直接貼到 Jira / ClickUp 的 ticket 內容

---

## P0-1 Define spec_section schema

### Summary
Define the canonical JSON schema for `spec_section`.

### Description
Create the initial JSON schema and example payload for `spec_section`. This artifact is the parser output foundation and must support stable section identity plus source traceability.

### Scope
- stable section id
- section title
- raw / normalized text
- source page references
- source coordinates
- parser warnings
- schema_version

### Acceptance Criteria
- schema file exists in repo
- example payload exists
- section id is stable and not UI-order dependent
- source reference fields are documented

### Dependencies
- none

---

## P0-2 Define requirement schema

### Summary
Define the canonical JSON schema for `requirement`.

### Description
Create the initial JSON schema and example payload for requirement artifacts used in the MVP review workflow.

### Scope
- requirement id
- title
- statement
- source_spec_ids
- source_note_ids
- compliance
- trace
- audit_rationale_id
- variant_scope
- status
- schema_version

### Acceptance Criteria
- schema file exists in repo
- example payload exists
- approved artifact requires audit_rationale_id
- trace fields are documented

### Dependencies
- P0-1 recommended
- P0-4 recommended

---

## P0-3 Define review_record schema

### Summary
Define the canonical JSON schema for `review_record`.

### Description
Create the structure for reviewer decisions supporting approve / reject and future audit analysis.

### Scope
- review id
- artifact id
- decision
- reviewer id
- rejection tags
- review note
- timestamp

### Acceptance Criteria
- reject supports structured tags
- approve / reject represented explicitly
- schema file exists in repo

### Dependencies
- none

---

## P0-4 Define audit_rationale schema

### Summary
Define the canonical JSON schema for `audit_rationale`.

### Description
Create the structure that preserves source references, prompt version, model version, and optional silver references.

### Scope
- audit id
- artifact id
- source refs
- prompt version
- model version
- optional silver refs

### Acceptance Criteria
- source refs support page and coordinate metadata
- schema file exists in repo
- example payload exists

### Dependencies
- P0-1 recommended
- P0-2 recommended

---

## P0-5 Define state machine v1

### Summary
Freeze MVP workflow states and transitions.

### Description
Document and agree the first workflow state machine for draft, review, approval, and rejection.

### Scope
- DRAFT
- IN_REVIEW
- APPROVED
- REJECTED
- actor rules
- transition metadata
- invalid transition notes

### Acceptance Criteria
- state table exists
- allowed transitions are explicit
- transition actor is explicit
- approved cannot be silently overwritten

### Dependencies
- P0-2
- P0-3

---

## P0-6 Define trace_map contract

### Summary
Define the minimal contract for artifact traceability indexing.

### Description
Create the minimum structure required to resolve upstream and downstream links across core artifacts.

### Scope
- artifact id
- artifact type
- upstream ids
- downstream ids
- status
- version
- schema_version
- audit_rationale_id

### Acceptance Criteria
- requirement can resolve back to source spec
- source spec can resolve downstream requirement
- contract is documented

### Dependencies
- P0-1
- P0-2
- P0-4

---

## P0-7 Define parser output contract

### Summary
Define the parser output contract used by the pipeline.

### Description
Specify the expected output from the parser before note generation begins.

### Scope
- spec_section payload
- parser warnings
- page refs
- coordinate refs
- normalization flags

### Acceptance Criteria
- parser output format is documented
- can represent table extraction issues
- can represent OCR uncertainty or warnings

### Dependencies
- P0-1

---

## P0-8 Define requirement generation contract

### Summary
Define the requirement generation input/output contract.

### Description
Specify the contract between note generation and requirement generation, including trace and audit requirements.

### Scope
- input note refs
- output requirement payload
- trace fields
- audit metadata
- error cases

### Acceptance Criteria
- contract is documented
- output maps cleanly to requirement schema
- minimum audit metadata is required

### Dependencies
- P0-2
- P0-4
- P0-7
