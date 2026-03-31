# SpecOps 技術規格 (Technical Specs)

> 版本: v4.2  
> 角色: 資料結構、儲存策略與圖譜定義

---

## 一、ID 與追蹤系統 (ID System)

### ID 命名規則

- **SPEC-ID**: `S-<品牌>-<機種>-<版本>-<區塊>`
- **REQ-ID**: `R-<SPEC-ID>-<流水號>`
- **TREQ-ID**: `T-<REQ-ID>-<流水號>`

### 追蹤陣列 (Traceability Matrix)

存儲於 `spec_to_req.json`:

```json
{
  "S-001": ["R-001", "R-002"]
}
```

---

## 二、資料架構與儲存 (Data Architecture)

採用 **Git-based JSON** 檔案系統，確保透明度與版本回溯。

### 1. 目錄結構原則

- 版本化目錄 (v1.0, v1.1, ...)。
- 全局索引 (`trace_map.json`) 作為導航主鍵。

### 2. 版本管理機制
- **Git Commit**: 每次審查存檔即自動 Commit。
- **Delta Storage**: 利用 Git Diff 特性存儲變更。
- **Variant Version Lock**: 在 `variant_config.json` 中紀錄目前鎖定的 Base Commit ID。

---

## 三、圖譜模式定義 (Graph Schema)

針對複雜系統關聯，採用 Property Graph 模型。

### 1. 節點定義 (Nodes)
- `Spec`, `Note`, `Req`, `Test`, `Signal`, `Data Node`.

### 2. 關係定義 (Edges)
- `DERIVES_FROM`, `DECOMPOSED_TO`, `MAPS_TO`, `DEPENDS_ON`, `CONFLICTS_WITH`.

---

## 四、多源數據抽象層 (Multi-Source Ingestion)

除了 Markdown 文本，支援「結構化數據源」併入。

### 1. 數據入口類型
- **Parameters**: JSON/CSV 參數對應表。
- **Signal Specs**: 通訊協議定義檔 (DBC, ARXML, LDF)。

### 2. 預算指標定義 (Budgeting)
- `token_usage_limit`: 儲存於專案配置，定義總消耗預算。

---

## 五、併發處理與存取控制 (Concurrency & RBAC)

為了確保多位工程師同時審查大規模規格書時，資料不被覆蓋且符合合規性要求。

### 1. 併發處理機制 (Concurrency Control)
採用 **樂觀鎖 (Optimistic Locking)** 與 **Git 分支策略**。
- **Atomic File Locking**: 當用戶開啟特定 `SPEC-ID` 進行編輯時，系統在 Redis 或 Git 伺服器建立臨時 `Lock` 標記（TTL 30min）。
- **Branch per Task**: 複雜改版建議採用「任務分支」。
- **Conflict Detection**: 在 `APPROVED` 存檔前，系統自動執行 `git fetch` 與 `diff`。

### 2. 權限管理 (RBAC - Role Based Access Control)
- **Viewer**, **Engineer**, **Reviewer**, **Safety Manager**.

### 3. 資料追蹤 (Audit Trail)
- 每一筆 `APPROVED` 動作皆需附加 `User ID` 與 `Timestamp`。
- **數位簽章 (Digital Signature)**: 對於 ASIL C/D 需求，存檔時需進行數位簽章校驗。

---

## 六、訊號詞彙映射表 (Signal Glossary)

為了解決自然語言描述與技術訊號 (DBC/ARXML) 之間的對應鴻溝，系統維護一份映射清單。

### 1. 資料格式 (`signal_glossary.json`)
```json
{
  "project": "Project_Name",
  "mappings": [
    {
      "nl_term": "Vehicle Speed",
      "dbc_message": "ABS_Status_01",
      "dbc_signal": "Veh_Spd_Raw",
      "status": "APPROVED"
    }
  ]
}
```

---

## 七、審查反饋模式 (Review Feedback Schema)

### 1. 需求物件擴展
```json
{
  "req_id": "R-001",
  "status": "REJECTED",
  "rejection_tags": ["SEMANTIC_ERROR", "FORMAT_ERROR"],
  "human_opinion": "..."
}
```
