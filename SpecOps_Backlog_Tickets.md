# SpecOps 第一批 Backlog Tickets

> 版本: v1.0
> 角色: 第一批可直接排進 Sprint 的任務清單

---

## Epic A: Domain Model

### T1. 定義 spec_section schema
- 目標: 固定 section artifact 欄位
- 輸出: schema、範例 JSON、欄位說明
- 驗收:
  - 含穩定 section id
  - 含 source page / coordinate metadata
  - 含 schema_version

### T2. 定義 note schema
- 目標: 固定 note artifact 欄位
- 輸出: schema、範例 JSON
- 驗收:
  - 可連回 source spec
  - 可進入 review workflow

### T3. 定義 requirement schema
- 目標: 固定 requirement artifact 欄位
- 輸出: schema、範例 JSON
- 驗收:
  - 含 trace 欄位
  - 含 compliance 欄位
  - 含 audit_rationale_id

### T4. 定義 review_record schema
- 目標: 固定 reviewer decision 結構
- 驗收:
  - 支援 approve / reject
  - reject 可帶 tags
  - 可記錄 reviewer 與時間

### T5. 定義 audit_rationale schema
- 目標: 固定生成依據結構
- 驗收:
  - source_refs 必填
  - prompt_version 必填
  - model_version 必填

---

## Epic B: Workflow Core

### T6. 定義 state machine v1
- 目標: 固定 MVP 狀態與轉移
- 範圍:
  - DRAFT
  - IN_REVIEW
  - APPROVED
  - REJECTED
- 驗收:
  - 有正式 transition table
  - 每個 transition 有 actor 與 metadata 要求

### T7. 定義 rejection tags v1
- 目標: 讓 reject 可被結構化處理
- 建議 tags:
  - missing_constraint
  - unclear_condition
  - wrong_unit
  - missing_trace
  - safety_risk
  - security_risk
- 驗收:
  - tag 列表固定
  - 每個 tag 有文字定義

### T8. 定義 trace_map contract
- 目標: 固定 artifact 關聯索引
- 驗收:
  - 可從 requirement 找回 source spec
  - 可從 source spec 找 downstream requirement

---

## Epic C: Parsing / Generation

### T9. 定義 parser output contract
- 目標: 固定 parser 輸出格式
- 驗收:
  - section text
  - page refs
  - coordinate refs
  - parse warnings

### T10. 建立 parser fixture set v1
- 目標: 建立 3 份真實輸入樣本
- 驗收:
  - 至少含表格
  - 至少含多層章節
  - 至少含解析失真案例

### T11. 定義 note generation contract
- 目標: 固定 note generation 輸入與輸出
- 驗收:
  - 輸入為 spec_section
  - 輸出為 structured note
  - 保留 source refs

### T12. 定義 requirement generation contract
- 目標: 固定 requirement generation 輸入與輸出
- 驗收:
  - 輸入為 note
  - 輸出為 requirement
  - 包含 audit metadata

---

## Epic D: Review / Audit

### T13. 實作 review API / service contract
- 目標: 建立 submit / approve / reject 介面
- 驗收:
  - reject 必填 tags
  - approve 產生 review record

### T14. 定義 section lock contract
- 目標: 定義 lock acquire / renew / release
- 驗收:
  - TTL 明確
  - lock owner 明確
  - timeout 行為明確

### T15. 定義 audit trail persistence contract
- 目標: 固定哪些事件一定要留存
- 驗收:
  - generation event
  - review event
  - export event

---

## Epic E: Export / Quality

### T16. 定義 Codebeamer export payload v1
- 目標: 建立最小單向匯出格式
- 驗收:
  - 僅 approved 可匯出
  - payload 欄位固定
  - 有 idempotency key

### T17. 建立 regression fixtures v1
- 目標: 建立 Golden Test Suite 最小集合
- 驗收:
  - 含 expected note
  - 含 expected requirement
  - 含評估比對方式

### T18. 定義 KPI collection baseline
- 目標: 決定 MVP 先收哪些數據
- 驗收:
  - precision / recall
  - review cycle time
  - rejection rate
  - export success rate

---

## 建議優先順序

- P0: T1, T3, T4, T5, T6, T8, T9, T12
- P1: T2, T7, T10, T11, T13, T14
- P2: T15, T16, T17, T18
