# Progress Log

## 2026-04-14

- 讀取 repo 規則、MVP 路線圖、實作計畫與 README。
- 確認這不是從零開始的專案；目前已有 API、pipeline、SQLite persistence 與多組測試。
- 發現文件對「MVP 完成」與 `test_requirement` 是否屬於 MVP 本體存在切分差異，需先與使用者對齊。
- 使用四代理角色完成 MVP gate 盤點；production review 找出兩個 blocker，test / coverage roles確認主流程大致齊備。
- 依 TDD 新增 `tests/test_mvp_gate_regressions.py`，先得到 2 個 failing tests，再補 production code。
- 修改 `specops_api/models.py`、`specops_api/repository.py`、`specops_api/sqlite_repository_relational.py`：
  - patch rejected artifact 會回到 `DRAFT`
  - export 新增 stable/idempotent job semantics
- 驗證結果：
  - `uv run pytest tests/test_mvp_gate_regressions.py -q` -> `2 passed`
  - `uv run pytest tests/test_real_spec_pipeline.py tests/test_review_regression_fixtures.py tests/test_mvp_gate_regressions.py -q` -> `42 passed`
  - `uv run pytest -q` -> `79 passed`

## 2026-06-03

- 依使用者要求，將 Graphify 可借鑑之處併入專案文件。
- 重新確認 Graphify README / ARCHITECTURE 的重點：
  - 輕量 pipeline 分層：`detect -> extract -> build_graph -> analyze -> report -> export`
  - node / edge extraction schema
  - `EXTRACTED` / `INFERRED` / `AMBIGUOUS` edge confidence
  - `graph.json` / report / cache / validation / security / unit-test 模式
- 更新 `SpecOps_MVP_Implementation_Roadmap.md`：
  - 在 Graph 技術決策中加入 `trace_graph.json`、`TRACE_GRAPH_REPORT.md`、confidence taxonomy、ambiguous edge review rule、source fingerprint cache 與 validation 要求。
  - 在風險與 backlog 補上 graph artifact、edge confidence 與 graph report 相關項目。
- 更新 `findings.md` 與 `task_plan.md`，保留本次外部參考判斷與後續 graph milestone 候選工作。
- 本次為文件型變更，未修改 production code 或 tests。
- 本地四角色 gate：
  - Production-Code：確認本次不需要 production code 變更。
  - Production-Code Review：確認 roadmap / README / planning docs 已反映 Graphify 借鑑方向，且未承諾超出 MVP 的 Neo4j、完整 GraphRAG 或 graph UI。
  - Test：確認本次不需要新增或修改測試檔。
  - Coverage Review：確認文件型變更以 staged diff 與關鍵字搜尋驗證即可，不需 pytest。
- Commit 前 GitHub gate：
  - `gh issue list --state open --limit 20 --json number,title,url` -> `[]`
  - `gh pr list --state open --limit 20 --json number,title,headRefName,url` -> `[]`
- 文件驗證：
  - `git diff --cached --check` -> passed
