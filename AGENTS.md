# VerifyImportAI Project Rules

- Before every commit in this repository, check GitHub for newly opened issues with `gh issue list --state open --limit 20`.
- Before every commit in this repository, check GitHub for newly opened pull requests with `gh pr list --state open --limit 20`.
- If either command shows new work that may conflict with the current milestone, review it before committing.
- For every implementation milestone in this repository, use a three-agent workflow.
- One agent is responsible for production code changes only.
- One agent is responsible for writing or updating tests for the milestone only.
- One separate agent is responsible for reviewing whether the tests fully cover the milestone scope, key paths, edge cases, and regressions.
- Do not collapse these three responsibilities into one agent when sub-agents are available.
- Before committing a milestone, complete all three roles: implementation, test authoring, and test coverage review.
- If the coverage-review agent finds gaps, address them before commit and push.
