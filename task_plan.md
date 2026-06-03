# Task Plan

## Goal

在不破壞既有工作樹變更的前提下，依據 repo 既有路線圖與實作計畫，逐一完成剩餘 MVP 里程碑；每個里程碑都遵守四代理工作流、補齊驗證，直到達成使用者確認的 MVP 完成定義。

## Current Phase

- `completed` 釐清 MVP 完成範圍與下一個里程碑
- `completed` 盤點目前實作與文件差距
- `completed` 執行下一個 milestone 的四代理循環
- `completed` 跑 focused / broader verification
- `completed` 修補 review rework loop 與 export idempotency 缺口後達成 MVP gate
- `completed` 將 Graphify 可借鑑的 graph pipeline / confidence taxonomy / report-export-cache-security 方向併入 roadmap 與工作紀錄
- `pending` 後續若進入 graph milestone，優先實作 `trace_graph.json` export 與 `TRACE_GRAPH_REPORT.md`，先只產生 `EXTRACTED` edges

## Constraints

- 以繁體中文回覆
- 不可覆蓋使用者既有未提交變更
- 每個 implementation milestone 必須完成四代理角色
- 宣稱完成前必須有新鮮驗證結果
- 文件型 milestone 若 sub-agent 工具政策不允許主動 spawn，仍需在本地完成 production / production-review / test / coverage-review gate 紀錄

## Open Questions

- 「MVP 完成」是否以路線圖第十一節的 6 項成功標準為準，等同至少做到 export gate，而不包含 post-MVP / 進階自動化？
- 下一個 graph milestone 是否只做 report/export artifact，或同步補 API endpoint 與 SQLite persistence？

## Errors Encountered

- `tests/test_mvp_gate_regressions.py` 初次 red run 失敗，確認根因為 rejected artifact patch 後未回到 `DRAFT`，以及 export 未實作 idempotent/stable response semantics；已修復。
