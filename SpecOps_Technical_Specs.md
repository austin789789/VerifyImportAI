# SpecOps 技術規格 (Technical Specs)

> 版本: v4.6  
> 角色: 核心資料結構、儲存策略、圖譜與技術治理

---

## 一、ID 與追蹤系統 (ID System)

### 1. ID 命名規則

- **SPEC-ID**: `S-<brand>-<program>-<spec_version>-<section_key>`
- **NOTE-ID**: `N-<SPEC-ID>-<seq>`
- **REQ-ID**: `R-<SPEC-ID>-<seq>`
- **TREQ-ID**: `T-<REQ-ID>-<seq>`
- **EDGE-ID**: `E-<source_node_id>-<edge_type>-<target_node_id>`
- **REVIEW-ID**: `RV-<artifact_id>-<seq>`
- **AUDIT-ID**: `AR-<artifact_id>-<seq>`

### 2. 穩定性原則

- `section_key` 應為穩定鍵，不可直接依賴純展示序號。
- 變體 Overlay 預設沿用 Base artifact ID，另以 `variant_scope` 區分。
- 被封存的 ID 不得重複使用。

---

## 二、資料架構與儲存 (Data Architecture)

### 1. 目錄結構原則

- `spec/`, `note/`, `graph/`, `requirement/`, `test_requirement/`, `traceability/`, `audit/`, `integration/`, `library/`.
- 採版本化目錄，例如 `v1.0`, `v1.1`。
- `trace_map.json` 為全域導航索引，但不是唯一真相來源。

### 2. trace_map.json 最低欄位

- `artifact_id`
- `artifact_type`
- `upstream_ids`
- `downstream_ids`
- `status`
- `version`
- `schema_version`
- `last_review_id`
- `audit_rationale_id`

### 3. 版本管理機制

- 審查存檔可觸發版本化快照，但 Git 不是唯一資料庫。
- `variant_config.json` 必須記錄 Base 鎖定版本、同步策略與 override 規則。
- 外部同步需支援 idempotent retry，避免重複建立資料。

---

## 三、圖譜與知識庫模式 (Graph & Knowledge Base)

採用 **Property Graph + GraphRAG**。

### 1. 節點類型

- `SPEC_SECTION`
- `NOTE`
- `REQUIREMENT`
- `TEST_REQUIREMENT`
- `SIGNAL`
- `VARIANT`
- `THREAT`
- `CONTROL`

### 2. 關係定義 (Canonical Edge Taxonomy)

- `DERIVES_FROM`
- `DECOMPOSED_TO`
- `MAPS_TO`
- `DEPENDS_ON`
- `CONFLICTS_WITH`
- `SIMILAR_TO`
- `MITIGATED_BY`
- `OVERRIDES`

### 3. Edge Request

- 跨鎖定章節修改 edge 時，建立 `pending_edge_request`。
- request 最低欄位應包含 `request_id`, `edge_id`, `requested_change`, `requester`, `target_owner`, `created_at`, `expires_at`, `status`。
- request 超時後自動失效，不得無限懸掛。

### 4. GraphRAG 檢索原則

- 先以階層切片找候選 chunk，再沿 canonical edge taxonomy 擴展關聯。
- `DEPENDS_ON` 與 `CONFLICTS_WITH` 優先用於 impact 與一致性檢查。
- `DERIVES_FROM` 與 `DECOMPOSED_TO` 優先用於 traceability 與生成注入。

---

## 四、Silver Dataset

### 1. 角色定位

Silver Dataset 是可注入生成流程的高品質參考資產，不是所有 `APPROVED` 條目的鏡像。

### 2. 生命週期

- `candidate`
- `curated`
- `active`
- `expired`
- `quarantined`
- `retired`

### 3. 收錄條件

- 來源 artifact 必須為 `APPROVED`。
- 通過品質閘門與隱私檢查。
- `edit_distance`、約束保真度與術語一致性達標。
- 通過專家抽樣精選或規則允許的自動升級。

### 4. 隱私欄位

- `visibility`: `GLOBAL | BRAND | PROJECT`
- `brand_id`
- `project_id`
- `sensitivity_reason`
- `expiry_date`
- `allowed_use_cases`

---

## 五、併發處理與存取控制 (Concurrency & RBAC)

### 1. Section-level Pessimistic Locking

- 鎖定單位為單一 Section。
- 預設 TTL 為 30 分鐘。
- 到期前須提醒續租。
- 逾時後未續租者，鎖可被回收，但未提交內容不得自動視為已保存。

### 2. 權限原則

- Editor 可編輯本章節內容。
- Reviewer 可執行審查與狀態轉移。
- Architect / Admin 可執行高風險仲裁、Silver 精選與緊急解鎖。

---

## 六、Observability

- **Token Budgeting**: 至少以 stage 與 section 為單位追蹤。
- **Evaluation Logs**: 保存評分過程、模型版本與仲裁結果。
- **Job Telemetry**: 記錄 sync job、auto-fix job、integration job 的成功率、重試與耗時。

---

## 七、核心物件最小集合

實作時至少要正式定義以下 schema：

- `spec_section`
- `note`
- `requirement`
- `test_requirement`
- `graph_node`
- `graph_edge`
- `review_record`
- `audit_rationale`
- `silver_dataset_entry`
- `variant_config`
- `signal_mapping`

詳細欄位定義由 `SpecOps_Data_Schema.md` 承接。
