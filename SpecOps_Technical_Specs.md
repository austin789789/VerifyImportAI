# SpecOps 技術規格 (Technical Specs)

> 版本: v4.1  
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
- **Delta Storage**: 利用 Git Diff 特性存儲變更，方便改版對照。

---

## 三、圖譜模式定義 (Graph Schema)

針對複雜系統關聯，採用 Property Graph 模型。

### 1. 節點定義 (Nodes)

- `Spec`: 規格原始區塊。
- `Note`: 語義解析中繼站。
- `Req`: 具體需求物件。
- `Test`: 測試驗證方案。
- `Signal`: 硬體/通訊訊號（來自 DBC/ARXML）。
- `Data Node`: 外部參數或配置數據。

### 2. 關係定義 (Edges)

- `DERIVES_FROM`: 需求源於規格。
- `DECOMPOSED_TO`: ASIL 分解或需求進一步拆解路徑。
- `MAPS_TO`: 訊號數據與需求的映射。
- `DEPENDS_ON`: 跨功能間的邏輯依賴。
- `CONFLICTS_WITH`: 偵測邏輯矛盾。

---

## 五、併發處理與存取控制 (Concurrency & RBAC)

為了確保多位工程師同時審查大規模規格書時，資料不被覆蓋且符合合規性要求。

### 1. 併發處理機制 (Concurrency Control)

採用 **樂觀鎖 (Optimistic Locking)** 與 **Git 分支策略**。

- **Atomic File Locking**: 當用戶開啟特定 `SPEC-ID` 進行編輯時，系統在 Redis 或 Git 伺服器建立臨時 `Lock` 標記（TTL 30min），防止他人同時修改同一物件。
- **Branch per Task**: 複雜改版建議採用「任務分支」，審查完成後再 Merge 回主版本線。
- **Conflict Detection**: 在 `APPROVED` 存檔前，系統自動執行 `git fetch` 與 `diff`，若偵測到該 `REQ-ID` 已被他人更新，則觸發 **Merge Conflict UI**。

### 2. 權限管理 (RBAC - Role Based Access Control)

定義四種核心角色與操作權限：

| 角色 | 權限能力 | 適用對象 |
| :--- | :--- | :--- |
| **Viewer** | 僅讀取所有追蹤鏈與原文。 | 專案經理、客戶。 |
| **Engineer** | 建立 `DRAFT`、提交 `FIXED`、執行 `Impact Analysis`。 | 需求工程師、開發者。 |
| **Reviewer** | 執行 `APPROVE` / `REJECT` 操作，修改 `human_opinion`。 | 資深工程師、架構師。 |
| **Safety Manager** | 僅限操作 `FSR/TSR` 等安全標籤，簽署合規報告。 | 功能安全專家。 |

### 3. 資料追蹤 (Audit Trail)

- 每一筆 `APPROVED` 動作皆需附加 `User ID` 與 `Timestamp`。
- **數位簽章 (Digital Signature)**: 對於 ASIL C/D 需求，存檔時需進行數位簽章校驗，確保審查流程的法律效力。
