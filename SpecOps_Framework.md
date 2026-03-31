# SpecOps 核心框架 (Framework)

> 版本: v4.6  
> 角色: 核心邏輯、原則、主流程與共通治理規則

---

## 一、系統目標

透過 LLM、結構化資料與圖譜技術，降低規格工程中的追蹤成本、更新延遲與人工檢核負擔。

- **效率**: 自動生成初版 Note、Requirement、Test Requirement。
- **精確度**: 偵測跨章節邏輯衝突、訊號映射失配與版本漂移。
- **完整性**: 以可量測指標追蹤需求覆蓋率與漏失率，而非不可驗證的 100% 宣稱。
- **可追蹤性**: 建立從來源規格到測試需求與稽核依據的雙向追蹤。
- **合規證據**: 為 ISO 26262 / ISO 21434 保留審查、生成與修正依據。

---

## 二、核心設計原則

1. **全流程可追蹤**: `SPEC -> NOTE -> REQUIREMENT -> TEST_REQUIREMENT`，並保留 `GRAPH`、`AUDIT_RATIONALE`、`SIGNAL_MAPPING` 與 `VARIANT_OVERLAY` 關聯。
2. **Human-in-the-loop**: LLM 只提供候選產出與修正建議，人工審查才是最終核准來源。
3. **NDA 隔離**: 知識資產必須根據 `visibility`、`brand_id`、`project_id` 過濾後才能注入生成流程。
4. **可審計**: 保留生成依據、Prompt 版本、人工修正、模型版本與人工操作軌跡，但保存策略須遵守脫敏與權限規則。
5. **模組化變體**: 採 Base + Overlay 管理變體，避免複製整套需求。
6. **知識閉環**: 只有通過品質閘門的候選條目才能成為 Silver Dataset 正式條目。

---

## 三、五階段核心流程 (The 5-Stage Pipeline)

1. **Stage 1: Spec Structuring (PDF -> Markdown)**  
   解析 OCR、版面、表格與來源座標，產出可引用的規格章節。
2. **Stage 2: Note Generation**  
   將規格整理為語義清晰、可審查的 Note 與初步圖譜節點。
3. **Stage 3: Requirement Generation**  
   從 Note 推導可驗證 Requirement，建立來源與下游追蹤鏈。
4. **Stage 4: Test Requirement Generation**  
   從 Requirement 產生可驗證的 Test Requirement 與驗收依據。
5. **Stage 5: Change Sync / Signal-Sync**  
   當 Spec、Signal、Base Variant 或外部整合資料變更時，執行 Impact Analysis 與同步修正。

註: Stage 5 為持續性流程，可在 Stage 1-4 完成後重複觸發。

---

## 四、結構化審查系統 (Review System)

採用 **Atomic Review** 與 **Section Locking**。

### 1. 併發衝突管理

- **Section-level Pessimistic Locking**: 章節被編輯時鎖定為唯讀。
- **Pending Edge Request**: 跨章節圖譜關係變更需由另一側持鎖者或授權審查者核准。
- **Lock TTL**: 鎖具時效，逾時後需續租或釋放。

### 2. 正式狀態集合

- `DRAFT`: 初始草稿。
- `IN_REVIEW`: 已提交人工審查。
- `APPROVED`: 審查核准，可作為正式產物與下游同步來源。
- `REJECTED`: 人工退回，需附結構化原因標籤。
- `AUTO_FIX_IN_PROGRESS`: 系統根據退回原因或 impact 進行自動修正。
- `AUTO_FIXED_PENDING_REVIEW`: 已自動修正，待人工覆核。
- `IMPACTED`: 因上游變更而失效或待重審。
- `MANUAL_RECOVERY`: 無法安全自動修正，需人工處理。
- `ARCHIVED`: 歷史資料封存。

### 3. 狀態治理原則

- `APPROVED` 不等於自動進入 Silver Dataset，只會先成為 `silver_candidate`。
- 所有自動修正都必須附 `fix_rationale` 與 diff。
- `IMPACTED` 與 `MANUAL_RECOVERY` 必須指派 owner、severity 與 due date。

---

## 五、變更管理 (Change Management)

### 1. Impact Analysis 流程

1. **Diff Detection**: 比對新舊版 Spec / Signal / Variant / 外部 ALM 資料。
2. **Impact Scope Resolution**: 依 traceability 與 graph edge 找出受影響節點。
3. **Auto-Fix Eligibility Check**: 判斷是否允許自動修正。
4. **Propagation**:
   - 可安全自動修正: 進入 `AUTO_FIX_IN_PROGRESS`，成功後轉 `AUTO_FIXED_PENDING_REVIEW`。
   - 不可安全自動修正: 轉 `MANUAL_RECOVERY`。
   - 僅需重審: 標記為 `IMPACTED`。

### 2. Signal-Sync 原則

- 僅針對已建立 signal mapping 的需求啟動。
- 置信度門檻預設為 `0.6`，但低於門檻時不得直接覆寫正式核准內容。
- 單位轉換、枚舉調整、多對一映射拆分屬高風險場景，預設需人工覆核。

### 3. 變體同步策略

- **Version Locking**: Overlay 預設鎖定 Base 版本或 Commit。
- **Manual Sync Trigger**: 由工程師顯式觸發同步。
- **Selective Sync**: 僅同步被 impact scope 命中的 Overlay 節點。

---

## 六、品質校驗 (Quality Validation)

1. **Schema Validation**: JSON Schema、欄位完整性與 ID 唯一性檢查。
2. **Graph Consistency Check**: 以統一 edge taxonomy 檢查跨章節一致性與衝突。
3. **Multi-Agent Consensus**: 以多代理評分與仲裁檢查覆蓋率、可測性與合規性。
4. **Audit Rationale**: 保留來源座標、引用節點、Prompt 版本、模型版本與人工操作軌跡。
5. **Golden Test Suite**: Prompt、模型或規則更新後執行回歸檢查。
6. **Quality Hotspot Map**: 視覺化低信心、高退回率與高 impact 區塊。
7. **Budget Control**: 追蹤各 stage token、延遲與重試成本。

---

## 七、資料演進與架構治理 (Data Evolution)

- 所有核心物件皆須具備 `schema_version`。
- 版本升級需提供 migration 規則與回溯策略。
- 舊版資料若無法完整升級，必須明示降級能力與限制。

---

## 八、文件分層原則

本文件只定義框架與共通規則，實作細節分別由下列文件承接：

- `SpecOps_State_Machine.md`
- `SpecOps_Data_Schema.md`
- `SpecOps_Evaluation_KPI.md`
- `SpecOps_Integration_Codebeamer.md`
- `SpecOps_Privacy_Audit_Policy.md`
- `SpecOps_SQLite_Relational_Schema.md`
