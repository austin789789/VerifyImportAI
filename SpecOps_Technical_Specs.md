# SpecOps 技術規格 (Technical Specs)

> 版本: v4.4 -> v4.5  
> 角色: 資料結構、儲存策略與圖譜定義

---

## 一、ID 與追蹤系統 (ID System)

### ID 命名規則
- **SPEC-ID**: `S-<品牌>-<機種>-<版本>-<區塊>`
- **REQ-ID**: `R-<SPEC-ID>-<流水號>`
- **TREQ-ID**: `T-<REQ-ID>-<流水號>`

---

## 二、資料架構與儲存 (Data Architecture)

### 1. 目錄結構原則
- 版本化目錄 (v1.0, v1.1, ...)。
- 全局索引 (`trace_map.json`) 作為導航主鍵。

### 2. 資料演進與相容性 (Schema Evolution)
- **Metadata Versioning**: 每個 JSON 文件皆需包含 `schema_version` 欄位。
- **Audit Rationale**: 每條需求包含合規追蹤資訊（PDF 座標、Prompt 版本等）。

### 3. 版本管理機制
- **Git Commit**: 每次審查存檔即自動 Commit。
- **Variant Version Lock**: 在 `variant_config.json` 中紀錄鎖定的 Base Commit ID。

---

## 三、圖譜與知識庫模式 (Graph & Knowledge Base)

針對複雜系統關聯，採用 **Property Graph + GraphRAG** 架構。

### 1. 視覺化圖譜編輯器 (Visual Editor)
- 支援透過 GUI 介面直觀地「斷開」或「建立」需求間的關係。

### 2. 跨章節連線衝突處理：圖譜變更請求 (Edge Request)
- **Problem**: 跨鎖定章節（Section A 與 Section B）的連線修改權限衝突。
- **Mechanism**: **Pending Edge Request (核准制)**。
    - 當工程師甲（持有 Section A 鎖）欲修改連向 Section B 的線時，系統發起 `Pending Request`。
    - 必須由工程師乙（持有 Section B 鎖）於介面確認同意後，圖譜連線才正式更新。
- **Ownership**: 連線 (Edge) 不單獨屬於 Source 或 Target，而是雙方共有的公共資產。

### 3. 關係定義 (Edges)
- `DERIVES_FROM`, `DECOMPOSED_TO`, `MAPS_TO`, `SIMILAR_TO`.

---

## 四、AI 評估資產：白銀資料集 (Silver Dataset)

系統有機生長的「高質量對照組」。

### 1. 生命週期管理
- **Architect Selection**: 定期由專家進行品質過濾。
- **Validity TTL**: 設有 **3 年有效期**。

### 2. 數據隱私標籤 (NDA Isolation)
- **Visibility & Brand Isolation**: 在 Schema 中強制加入 `visibility` 與 `brand_id`。
```json
{
  "source_spec": "規格原文片段",
  "approved_req": "最終人工核准的需求內容",
  "provenance": {
    "project_id": "Project_A",
    "brand_id": "OEM_X",
    "visibility": "BRAND",
    "expiry_date": "2029-03-31"
  }
}
```

---

## 五、併發處理與存取控制 (Concurrency & RBAC)

### 1. 章節級悲觀鎖 (Section-level Pessimistic Locking)
- **Lock Granularity**: 鎖定單位為單個規格章節（Section）。
- **TTL Mechanism**: 預設租期為 **30 分鐘**。

---

## 六、預算與性能監控 (Observability)

- **Token Budgeting**: 以「章節」為單位進行預算預估。
- **Evaluation Logs**: 儲存 Multi-Agent Consensus 的評分過程與結論。

