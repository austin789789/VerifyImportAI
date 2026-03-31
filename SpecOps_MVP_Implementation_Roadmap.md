# SpecOps MVP 實作路線圖 (MVP Implementation Roadmap)

> 版本: v1.0
> 角色: 將現有 SpecOps 規格壓縮為可執行的 MVP 範圍、開發順序與交付節點

---

## 一、文件目的

本文件不是再次重寫完整規格，而是將目前 10 份 SpecOps 文件收斂為：

- 第一階段一定要做什麼
- 哪些是 MVP，哪些延後
- 每一階段的輸入、輸出、完成條件
- 目前最值得先投資的技術路徑

---

## 二、MVP 目標

MVP 只解決 4 件事：

1. 將來源規格切成可引用章節。
2. 從章節生成 Note 與 Requirement。
3. 讓人工可審查、退回、再修正。
4. 保留完整 traceability 與 audit evidence。

MVP 先不追求完整車載閉環，不做過度承諾項目，例如：

- 自動產出完整合規報告
- 高成熟度 GraphRAG 大規模推理
- 全自動 Signal-Sync 修正
- 完整 Codebeamer 雙向同步
- 多模態流程圖解析
- 全量 Silver Dataset 自動精選

---

## 三、建議實作邊界

### In Scope

- Stage 1: PDF -> Markdown / section extraction
- Stage 2: Note generation
- Stage 3: Requirement generation
- 基本 review workflow:
  - `DRAFT`
  - `IN_REVIEW`
  - `APPROVED`
  - `REJECTED`
- 基本 traceability:
  - spec -> note
  - note -> requirement
- 基本 audit_rationale
- 基本 section lock
- 基本 visibility / privacy gate
- 基本 Golden Test Suite
- 單向 Codebeamer export stub

### Out of Scope

- Stage 4 的完整 test requirement 自動化量產
- Stage 5 的高成熟度 auto-fix orchestration
- Overlay variant selective sync automation
- 視覺化 graph editor 全功能版
- threat / control / TARA / FMEA 深度整合
- 地端模型部署
- 跨品牌知識精選平台化

---

## 四、MVP 系統切片

### Slice A: Parsing Foundation

輸入:
- PDF
- parser config

輸出:
- sectionized markdown
- source coordinates
- spec_section records

完成條件:
- 每個 section 有穩定 ID
- 可回鏈到 PDF 頁碼或座標
- 人工可校正抽取錯誤

### Slice B: Note / Requirement Pipeline

輸入:
- spec_section
- prompt config
- optional privacy-filtered few-shot examples

輸出:
- note
- requirement
- audit_rationale
- trace links

完成條件:
- 產物可被審查
- requirement 有來源 section
- requirement 有最小 audit record

### Slice C: Review Workflow

輸入:
- draft note / requirement
- reviewer action

輸出:
- review_record
- 狀態轉移
- rejection tags
- approved artifact

完成條件:
- reviewer 可 approve / reject
- reject 必須附標籤
- approved artifact 不可被背景流程直接覆寫

### Slice D: Audit / Traceability

輸入:
- artifacts
- review records
- prompt/model metadata

輸出:
- trace_map
- audit_rationale
- review history

完成條件:
- 任一 requirement 可追回 source spec
- 任一 approved artifact 可追回審查與生成依據

### Slice E: Controlled Export

輸入:
- approved requirement

輸出:
- codebeamer export payload
- integration log

完成條件:
- 僅 approved 可匯出
- 欄位映射固定
- 匯出失敗可重試

---

## 五、推薦開發順序

1. **資料模型先行**
   - 先落 `spec_section`, `note`, `requirement`, `review_record`, `audit_rationale`
   - 沒有 schema，不要先做 UI

2. **先做 review state machine**
   - 最少先支援 `DRAFT -> IN_REVIEW -> APPROVED / REJECTED`
   - 暫時不要一開始就做完整 auto-fix

3. **再做 parser 與 generation pipeline**
   - 先穩定輸入輸出契約
   - Prompt 可先簡化，但 trace 與 audit 欄位不能缺

4. **最後做 UI 與 export**
   - 先做可工作的 reviewer
   - 再做漂亮的 graph / dashboard

---

## 六、Phase 規劃

### Phase 0: Foundation

交付物:
- schema 初版
- state machine 初版
- trace_map 規格
- audit_rationale 規格

完成定義:
- 所有核心 artifact 都有正式欄位定義
- 狀態與轉移規則已固定

### Phase 1: MVP Core

交付物:
- parser prototype
- note / requirement generation
- reviewer workflow
- audit/trace persistence

完成定義:
- 可從一份 spec 跑到 approved requirement
- 全程可追溯
- 至少有基本 regression set

### Phase 2: MVP+

交付物:
- test requirement generation
- basic codebeamer export
- manual recovery queue
- silver candidate gate

完成定義:
- 可匯出 approved requirement
- 可追蹤待人工恢復項目
- 可開始收集品質數據

### Phase 3: Advanced

交付物:
- signal-sync
- variant sync
- richer graph reasoning
- automotive compliance extensions

完成定義:
- impacted flow 可控
- automotive metadata 真正進入工作流

---

## 七、最小技術決策建議

### 1. Source of Truth

- 以結構化 artifact store 為主
- Git 作為版本化與審計輔助，不要把 Git 當主交易資料庫

### 2. Graph

- MVP 可先用邏輯 graph model + adjacency storage
- 不急著上重型 graph database
- 先把 edge taxonomy 固定比較重要

### 3. LLM Strategy

- 先固定少量 prompt 模板
- 先做 deterministic logging
- 不要一開始就做複雜 multi-agent debate orchestration

### 4. Privacy

- 雲端模型前一定有 privacy gate
- visibility filter 必須早於 few-shot injection

---

## 八、目前最大風險

- parser 輸出不穩會污染後面全部流程
- requirement schema 若太晚定，後面每個模組都會重工
- 沒有 rejection taxonomy，auto-fix 會無法成形
- 太早做 graph UI 會消耗大量時間但不提升 MVP 成功率
- 太早做 automotive 深整合會把通用核心拖慢

---

## 九、建議的第一批 backlog

- 定義 `spec_section` schema
- 定義 `note` schema
- 定義 `requirement` schema
- 定義 `review_record` schema
- 定義 `audit_rationale` schema
- 定義最小 state machine API
- 建 parser output contract
- 建 requirement generation contract
- 建 review reject tags v1
- 建 golden regression fixtures v1

---

## 十、判斷 MVP 成功的標準

MVP 完成時，至少要能做到：

- 匯入一份真實 spec
- 切出穩定 section
- 生成可審查 requirement
- 完成人工 approve / reject
- 保存 trace 與 audit evidence
- 將 approved requirement 以穩定格式輸出

如果這 6 件還做不到，就不應該先做進階 graph UI、Signal-Sync 自動修正或完整車載合規閉環。
