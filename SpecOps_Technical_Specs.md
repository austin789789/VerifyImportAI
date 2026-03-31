# SpecOps 技術規格 (Technical Specs)

> 版本: v4.3  
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
- **Migration Policy**: 當 Schema 變更時，由系統自動執行 `migrate_v42_to_v43.py` 等腳本進行轉換。

### 3. 版本管理機制
- **Git Commit**: 每次審查存檔即自動 Commit。
- **Variant Version Lock**: 在 `variant_config.json` 中紀錄鎖定的 Base Commit ID。

---

## 三、圖譜與知識庫模式 (Graph & Knowledge Base)

針對複雜系統關聯，採用 **Property Graph + GraphRAG** 架構。

### 1. 知識庫層級 (Tiered Library)
- **Global Layer**: 產業標準、法規通用需求。
- **Brand Layer**: 特定客戶的設計規範（與 NDA 隔離連動）。
- **Project Layer**: 當前專案的特定邏輯。

### 2. 關係定義 (Edges)
- `DERIVES_FROM`: 需求源於規格。
- `DECOMPOSED_TO`: ASIL 分解或需求拆解路徑。
- `MAPS_TO`: 訊號數據與需求的映射。
- `SIMILAR_TO`: 跨專案知識推薦（GraphRAG 核心關係）。

---

## 四、AI 評估資產：白銀資料集 (Silver Dataset)

系統有機生長的「高質量對照組」。

### 1. 資料格式 (`silver_dataset.json`)
```json
{
  "source_spec": "規格原文片段",
  "approved_req": "最終人工核准的需求內容",
  "provenance": {
    "project_id": "Project_A",
    "reviewer": "Senior_Engineer",
    "edit_distance": 0.05
  }
}
```

---

## 五、併發處理與存取控制 (Concurrency & RBAC)

- **Atomic File Locking**, **Optimistic Locking**.
- **Roles**: Viewer, Engineer, Reviewer, Safety Manager.

---

## 六、預算與性能監控 (Observability)

- **Token Budgeting**: 定義專案消耗上限。
- **Evaluation Logs**: 儲存 Multi-Agent Consensus 的評分過程與結論。
