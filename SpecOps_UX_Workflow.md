# SpecOps 操作流程 (UX Workflow)

> 版本: v4.4 -> v4.5  
> 角色: 目錄結構、UI 原型與審查 SOP

---

## 一、專案目錄架構 (Directory Structure)
- `spec/`, `note/`, `graph/`, `requirement/`, `test_requirement/`, `traceability/`.
- `library/` (儲存 Brand/Global Common 映射資料)。

---

## 二、UI/UX 原型設計 (Split-View Reviewer)

### 1. 雙欄對照介面 (Split View)
- **Source View (左)**, **Editor View (右)**.
- **Locking Status**: 顯示章節鎖定狀態。
- **Edge Request Notification**: 當其他使用者請求建立/刪除連向您鎖定章節的邊時，彈出「🔔 連線變更請求」通知，支援一鍵核准/拒絕。

### 2. 視覺化圖譜編輯器 (Graph Visual Editor)
- **Pending Edges**: 以虛線顯示待核准的跨章節連線。
- **Conflict Highlight**: 視覺化標記偵測到的邏輯衝突。

### 3. 變更與同步儀表板 (Impact & Sync Dashboard)
- **Recovery Status**: 針對 AI 置信度 < 0.6 的訊號變更，標記為 `⚠️ MANUAL_RECOVERY`。
- **Signal-Sync Indicator**: 標註已自動修正的需求。

### 4. 數據隱私與合規
- **Visibility Badge**: 在白銀資料集推薦清單中標註 `GLOBAL`, `BRAND`, `PROJECT` 標籤。
- **Audit Trace**: 點擊需求顯示生成依據。

---

## 三、人工審查標準作業程序 (Review SOP)

### 審查流程
1. **Section Lock**: 選擇章節並獲得編輯鎖。
2. **Signal-Sync & Recovery**: 
    - 優先處理 `MANUAL_RECOVERY` 項目。
    - 驗證 `FIXED (Auto)` 狀態。
3. **Decision**:
   - `APPROVED`: 系統根據當前專案背景自動帶入隱私標籤存入 Silver Dataset。
   - `REJECTED`: 觸發修正流程。
4. **Graph Calibration**: 
    - 修改跨章節關係時，需等待對方核准（Edge Request）。
    - 對方發起請求時，需於 5 分鐘內決定核准與否，以利並行開發。

---

## 四、未來擴展 UX
- **合規報告一鍵產出**, **多模態解析 (圖表、流程圖) 一鍵提取**.
