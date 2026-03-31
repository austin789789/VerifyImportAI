# SpecOps 實作計畫 (Implementation Plan)

> 版本: v1.0
> 角色: 依據 MVP 路線圖拆解可執行的實作順序、依賴與驗收條件

---

## 一、目標

在最短可控週期內完成一條端到端 MVP 流程：

- 匯入 spec
- 產生 sectionized markdown
- 生成 note / requirement
- 進入人工審查
- 留存 trace 與 audit
- 匯出 approved requirement

---

## 二、實作原則

- 先穩資料契約，再做 UI
- 先做人工可控流程，再做自動修正
- 先確保 traceability 與 auditability，再追求生成品質優化
- 先做單向整合，再談雙向同步

---

## 三、工作分期

### Phase 0: Domain Foundation

目標:
- 固定核心資料模型與狀態機

範圍:
- requirement / note / spec_section / review_record / audit_rationale schema
- state machine rules
- trace_map contract
- rejection tags v1

輸出:
- schema docs
- API contract draft
- fixture examples

完成條件:
- 工程團隊可依 schema 開始切 service / storage
- reviewer flow 的狀態轉移不再變動

### Phase 1: Parsing + Generation Core

目標:
- 從 spec 跑出可審查 requirement

範圍:
- parser output contract
- section extraction
- source coordinate retention
- note generation
- requirement generation
- audit_rationale persistence

輸出:
- parser prototype
- generation pipeline prototype
- trace creation logic

完成條件:
- 至少一份真實 spec 可產生可審查 requirement
- 每條 requirement 均可追到 source section

### Phase 2: Review Workflow

目標:
- 完成人工核准閉環

範圍:
- review API
- approve / reject
- rejection tags
- section lock
- review history
- approved artifact persistence

輸出:
- review service
- basic reviewer UI or CLI workflow
- audit trail

完成條件:
- reviewer 可完整走完 approve / reject
- approved artifact 不會被背景程序直接覆蓋

### Phase 3: Controlled Export + Metrics

目標:
- 讓 approved requirement 可穩定輸出，並開始量測品質

範圍:
- codebeamer export stub
- integration log
- golden regression fixtures
- KPI collection baseline

輸出:
- export payload builder
- regression suite v1
- KPI dashboard data source

完成條件:
- approved requirement 可被穩定匯出
- regression suite 可在 prompt / model 更新後重跑

### Phase 4: Post-MVP

目標:
- 擴展進階能力

範圍:
- test requirement generation
- auto-fix
- manual recovery queue
- signal-sync
- variant sync
- automotive extensions

完成條件:
- impacted flow 與 automotive metadata 真正進入日常流程

---

## 四、依賴順序

1. Schema
2. State machine
3. Parser contract
4. Generation contract
5. Trace / audit persistence
6. Review workflow
7. Export
8. KPI / regression
9. Advanced automation

---

## 五、每階段驗收

### Phase 0 驗收
- schema 有範例 JSON
- 狀態轉移表固定
- rejection tags 可列舉

### Phase 1 驗收
- parser 可穩定產出 section ID
- requirement 有 source_spec_ids
- audit_rationale 至少含 source_refs / prompt_version / model_version

### Phase 2 驗收
- approve / reject 可重現
- reject 必填 tag
- review record 可查詢

### Phase 3 驗收
- export 僅接受 approved artifact
- 匯出失敗有 integration log
- regression suite 可自動執行

---

## 六、建議人力切分

- **Backend / Domain**: schema, state machine, trace, audit, export
- **AI / Pipeline**: parser, note generation, requirement generation, regression fixtures
- **Frontend / Workflow**: review UI, lock handling, audit display

---

## 七、目前最合理的第一個 Sprint

Sprint 1 只做：

- spec_section / note / requirement schema
- review_record / audit_rationale schema
- state machine v1
- rejection tags v1
- parser output contract
- 3 份真實 fixture spec

Sprint 1 不做：

- graph visual editor
- signal-sync
- variant sync
- full codebeamer integration
- advanced automotive metadata automation
