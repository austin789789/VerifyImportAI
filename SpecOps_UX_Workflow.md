# SpecOps 操作流程 (UX Workflow)

> 版本: v4.4  
> 角色: 目錄結構、UI 原型與審查 SOP

---

## 一、專案目錄架構 (Directory Structure)
- `spec/`, `note/`, `graph/`, `requirement/`, `test_requirement/`, `traceability/`.
- `library/` (儲存 Brand/Global Common 映射資料)。

---

## 二、UI/UX 原型設計 (Split-View Reviewer)

### 1. 雙欄對照介面 (Split View)
- **Source View (左)**, **Editor View (右)**.
- **Locking Status**: 頂部顯示「🔓 章節可編輯」或「🔒 已由 工程師 A 鎖定 (剩餘 25m)」。

### 2. 視覺化圖譜編輯器 (Graph Visual Editor)
- **Node-Link Interface**: 以節點圖呈現需求關聯，支援滑鼠拖拽建立/刪除關係邊。
- **Conflict Highlight**: 視覺化標記偵測到的 `CONFLICTS_WITH` 節點路徑。

### 3. 變更與同步儀表板 (Impact & Sync Dashboard)
- **Signal-Sync Indicator**: 標註哪些需求已由 Agent 自動修正 (`FIXED-Auto`)。
- **Risk Re-assessment Alert**: 針對 `IMPACTED` 章節顯示受影響的 TARA/FMEA 數量。

### 4. 知識庫與 AI 評估
- **Audit Trace**: 點擊需求可顯示原文座標與生成依據 (Rationale)。
- **Silver Dataset 入庫提示**: 顯示「✓ 已加入 Silver Dataset (有效期至 2029)」。

---

## 三、人工審查標準作業程序 (Review SOP)

### 審查流程
1. **Section Lock**: 選擇章節並獲得編輯鎖。
2. **Signal-Sync Verify**: 優先檢查 `FIXED (Auto)` 狀態的訊號修正內容。
3. **Decision**:
   - `APPROVED`: 系統自動存入具有 3 年有效期的 Silver Dataset。
   - `REJECTED`: 強制選擇退回標籤，觸發 `FIXING` 流程。
4. **Graph Calibration**: 使用視覺化編輯器手動調整或確認依賴關係。

---

## 四、未來擴展 UX
- **合規報告一鍵產出**, **AI 輔助檢漏**.
