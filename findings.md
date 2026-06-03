# Findings

## 2026-04-14

- `SpecOps_MVP_Implementation_Roadmap.md` 將 MVP 成功標準定義為 6 件事，其中包含「將 approved requirement 以穩定格式輸出」。
- `SpecOps_Implementation_Plan.md` 把 Controlled Export + Metrics 放在 `Phase 3`，但整體目標仍描述為 MVP 端到端流程的一部分。
- README 顯示目前 baseline 已有 real-spec extraction、review、approval、export、test-requirement generation flows。
- 工作樹目前已有未提交變更：`AGENTS.md`、`tests/test_api_smoke.py`。
- 四代理盤點後確認原本仍有兩個 MVP gate 缺口：
  - `REJECTED` artifact 雖可 patch，但無法重新送審。
  - export 只有即時回傳 queued job，缺少 idempotent/stable semantics。
- 已補齊的實作：
  - rejected requirement / test requirement 在 patch 後回到 `DRAFT`，可再次 `submit-review`。
  - SQLite export 新增 `export_jobs` persistence 與 `(requirement_id, idempotency_key)` 唯一語意；in-memory repo 同步支援同鍵穩定回應。
- 新增回歸測試 `tests/test_mvp_gate_regressions.py`，覆蓋 rework loop 與 export idempotency。

## 2026-06-03

- Graphify 可借鑑的核心不是直接導入工具，而是其輕量 knowledge graph pipeline：`detect -> extract -> build_graph -> analyze -> report -> export`。
- Graphify 的 extraction schema 對 SpecOps 有直接參考價值：node 保留來源位置，edge 保留 relation 與 `EXTRACTED` / `INFERRED` / `AMBIGUOUS` confidence。
- SpecOps 目前已有 `spec_section -> note -> requirement -> test_requirement` trace flow 與 `/trace/{artifact_id}`，但 graph 多半仍是 API 即時計算或欄位概念，尚未成為可重建 artifact。
- 最小可落地借鑑是新增 `trace_graph.json` 與 `TRACE_GRAPH_REPORT.md`，先從現有 link tables / trace records 產生 `EXTRACTED` edges。
- Graph report 應優先服務審查與 audit：斷鏈、缺 audit、high-degree artifact、可能 impact scope、ambiguous edge review queue。
- 不建議現階段引入 Neo4j、完整 GraphRAG、always-on hook、完整 graph editor 或多模態圖片理解；這些會超過目前 MVP 邊界。
- Source fingerprint cache 值得納入後續規劃，尤其是 Markdown、content list 與 image manifest 來源固定時，可避免 unchanged source 重複抽取。
