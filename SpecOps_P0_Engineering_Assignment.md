# SpecOps P0 工程分工建議

> 版本: v1.0
> 角色: 將 P0 任務拆成可並行執行的工程責任區

---

## 一、P0 目標

在第一個可控 Sprint 內固定 4 件事：

- 核心 schema
- state machine v1
- parser / generation contract
- trace / audit contract

---

## 二、分工原則

- Domain team 負責資料契約與狀態治理
- AI pipeline team 負責 parser / generation I/O 契約
- Platform team 負責持久化與可觀測性入口
- Frontend team 暫不做重 UI，只參與 contract review

---

## 三、建議責任切分

### Workstream A: Domain / Backend

Owner:
- Backend engineer
- Tech lead / architect

任務:
- T1 spec_section schema
- T3 requirement schema
- T4 review_record schema
- T5 audit_rationale schema
- T6 state machine v1
- T8 trace_map contract

交付物:
- JSON Schema
- transition table
- example payloads
- contract review notes

風險:
- 若 schema 反覆改動，後續 parser、review service、export 都會重工

### Workstream B: AI Pipeline

Owner:
- AI engineer
- Applied engineer

任務:
- T9 parser output contract
- T12 requirement generation contract

交付物:
- parser output schema or typed payload
- generation input/output contract
- sample fixtures
- failure mode list

風險:
- parser 輸出若沒有穩定 section key，traceability 會失效

### Workstream C: Platform / Infra

Owner:
- Platform engineer

任務:
- trace_map storage strategy review
- audit trail persistence review
- schema storage conventions
- regression fixture storage convention

交付物:
- storage path convention
- versioning convention
- event persistence contract

風險:
- 若主資料與 Git 角色混淆，後面版本治理會很亂

### Workstream D: Product / QA / Review Ops

Owner:
- PM / QA lead / reviewer representative

任務:
- review rejection tags v1 review
- approve / reject metadata review
- KPI baseline review

交付物:
- rejection tags glossary
- review checklist
- MVP acceptance checklist

風險:
- rejection tags 若太鬆散，後面 auto-fix 與品質分析無法做

---

## 四、建議並行順序

可先並行:
- T1 / T3 / T4 / T5
- T9 / T12
- trace_map contract review

必須等待前置完成:
- T6 需等 T3 / T4 基本欄位定型
- integration payload 不應早於 requirement schema 定案

---

## 五、建議會議節點

### Kickoff Review
- 目標: 對齊 P0 範圍
- 參與: backend, AI, PM, reviewer rep

### Contract Review
- 目標: 凍結 schema / state machine / parser output
- 參與: backend, AI, architect

### MVP Gate Review
- 目標: 確認可以開始寫 service 與 pipeline code
- 參與: 全體核心成員

---

## 六、完成判斷

P0 完成不代表產品完成，只代表團隊可以安全開始實作而不會因契約反覆重寫。
