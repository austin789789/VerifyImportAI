# SpecOps 技術規格 (Technical Specs)

> 版本: v4.4  
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
- **Audit Rationale**: 每條需求包含以下合規追蹤資訊：
    ```json
    {
      "rationale": {
        "pdf_coordinates": [x, y, w, h],
        "silver_template_id": "SV-992",
        "prompt_version": "v4.4.2",
        "agent_id": "Analyst_Agent_01"
      }
    }
    ```

### 3. 版本管理機制
- **Git Commit**: 每次審查存檔即自動 Commit。
- **Variant Version Lock**: 在 `variant_config.json` 中紀錄鎖定的 Base Commit ID。

---

## 三、圖譜與知識庫模式 (Graph & Knowledge Base)

針對複雜系統關聯，採用 **Property Graph + GraphRAG** 架構。

### 1. 視覺化圖譜編輯器 (Visual Editor)
- 支援透過 GUI 介面直觀地「斷開」或「建立」需求間的 `DEPENDS_ON` / `CONFLICTS_WITH` 關係。
- 編輯器操作直接同步更新 `graph.json` 節點。

### 2. 關係定義 (Edges)
- `DERIVES_FROM`: 需求源於規格。
- `DECOMPOSED_TO`: ASIL 分解或需求拆解路徑。
- `MAPS_TO`: 訊號數據與需求的映射。
- `SIMILAR_TO`: 跨專案知識推薦（GraphRAG 核心關係）。

---

## 四、AI 評估資產：白銀資料集 (Silver Dataset)

系統有機生長的「高質量對照組」。

### 1. 生命週期管理
- **Architect Selection**: 定期由專家進行品質過濾。
- **Validity TTL**: 設有 **3 年有效期**。逾期條目需經人工標記為「負面案例」或「再核准」。

### 2. 資料格式 (`silver_dataset.json`)
```json
{
  "source_spec": "規格原文片段",
  "approved_req": "最終人工核准的需求內容",
  "provenance": {
    "project_id": "Project_A",
    "reviewer": "Senior_Engineer",
    "expiry_date": "2029-03-31"
  }
}
```

---

## 五、併發處理與存取控制 (Concurrency & RBAC)

### 1. 章節級悲觀鎖 (Section-level Pessimistic Locking)
- **Lock Granularity**: 鎖定單位為單個規格章節（Section）。
- **TTL Mechanism**: 預設租期為 **30 分鐘**。若使用者持續活動則自動續約，斷線則自動釋放。
- **Admin Override**: 管理員可強制解鎖已鎖定章節，並記錄於操作日誌。

### 2. 角色權限 (Roles)
- Viewer, Engineer, Reviewer (資深工程師，具解鎖權限), Safety Manager.

---

## 六、預算與性能監控 (Observability)

- **Token Budgeting**: 以「章節」為單位進行預算預估與消耗追蹤。
- **Evaluation Logs**: 儲存 Multi-Agent Consensus 的評分過程與結論。

