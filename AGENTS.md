# VerifyImportAI Project Rules

## Scope

- These rules apply to the entire repository.
- These rules apply to every implementation milestone unless the user explicitly overrides them.

## GitHub Checks Before Commit

- Before every commit in this repository, check GitHub for newly opened issues with `gh issue list --state open --limit 20`.
- Before every commit in this repository, check GitHub for newly opened pull requests with `gh pr list --state open --limit 20`.
- If either command shows new work that may conflict with the current milestone, review it before committing.

## Milestone Workflow

- Every implementation milestone in this repository must use a four-agent workflow.
- Do not collapse these four responsibilities into one agent when sub-agents are available.
- Before commit and push, complete all four roles for the current milestone.

## Agent Roles

### 1. Production-Code Agent

- Responsible for production code changes only.
- May edit application code, API code, repository code, pipeline code, schema/model code, and other non-test implementation files.
- Must not write or modify tests as part of its assigned role.
- Must clearly state whether production code changes are required for the milestone.

### 2. Production-Code Review Agent

- Responsible for reviewing whether production code truly satisfies the current milestone requirements.
- Must not act as the implementation agent for production code.
- Must inspect behavior, interfaces, data flow, persistence, edge cases, and requirement alignment.
- Must identify any production gap that would make the milestone incomplete even if tests pass.

### 3. Test Agent

- Responsible for writing or updating tests only.
- May edit regression tests, smoke tests, lifecycle tests, persistence tests, and related test fixtures when required.
- Must not edit production code as part of its assigned role.
- Must report which test files changed and what behaviors were covered.

### 4. Coverage-Review Agent

- Responsible for reviewing whether the tests fully cover the current milestone.
- Must not act as the test implementation agent.
- Must check main paths, edge cases, regression risk, persistence or reload behavior when relevant, and important assertions tied to the milestone.
- Must explicitly say what a sufficient milestone test must assert.

## Review Gates

- If the production-code review agent finds a requirement gap, address it before commit and push.
- If the coverage-review agent finds a test coverage gap, address it before commit and push.
- Do not treat passing tests alone as proof that the milestone is complete.
- Do not commit or push a milestone while any required agent review still has unresolved gaps.

## Commit And Push Gate

- The milestone may be committed only after:
- The production-code agent has completed its work or explicitly confirmed that no production changes are needed.
- The production-code review agent has confirmed that production behavior satisfies the milestone.
- The test agent has completed the required tests.
- The coverage-review agent has confirmed that test coverage is sufficient for the milestone.
- Fresh verification commands have been run for the milestone.

## Verification Expectations

- Run the relevant focused tests for the current milestone before claiming it is complete.
- Run the broader regression suite used by this repository before commit when the milestone changes behavior or tests.
- Report the verification commands that were run and their results when closing out a milestone.

## Default Operating Rule

- If there is any conflict between speed and milestone completeness, prefer milestone completeness.
- If an agent result is ambiguous or off-target, do not treat that role as complete; redirect or rerun the role until it is usable.
