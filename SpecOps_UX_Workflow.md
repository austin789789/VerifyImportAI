# SpecOps 操作流程 (UX Workflow)

> 版本: v4.3  
> 角色: 目錄結構、UI 原型與審查 SOP

---

## 一、專案目錄架構 (Directory Structure)
- `spec/`, `note/`, `graph/`, `requirement/`, `test_requirement/`, `traceability/`.
- **新增**: `library/` (儲存 Brand/Global Common 映射資料)。

---

## 二、UI/UX 原型設計 (Split-View Reviewer)

### 1. 雙欄對照介面 (Split View)
- **Source View (左)**, **Editor View (右)**.

### 2. 變更與同步儀表板 (Impact & Sync Dashboard)
- **Version Locking Status**: 顯示當前鎖定的 Base 版本。
- **Version Sync Button**: 點擊後啟動差分對比。

### 3. 知識庫瀏覽器 (Knowledge Library Browser)
- **Common Library 預覽**: 生成需求時，側邊欄自動推薦相似的歷史範本。
- **Silver Dataset 入庫提示**: 審查完成後，顯示「✓ 已加入 Silver Dataset」通知。

### 4. AI 評估儀表板 (AI Evaluation Dashboard)
- **品質熱點圖 (Heatmap)**: 標註低置信度章節。
- **Consensus Score**: 顯示 Agent A 與 Agent B 的評分趨勢與辯論總結。

---

## 三、人工審查標準作業程序 (Review SOP)

### 審查流程
1. **Atomic Select**: 選擇 `DRAFT` 項目。
2. **Knowledge Reference**: 參考系統推薦的歷史需求描述。
3. **Decision**:
   - `APPROVED`: 系統自動計算 **Edit Distance (人工修改量)** 並存入 Silver Dataset。
   - `REJECTED`: 強制選擇退回標籤，觸發 `FIXING` 流程。

---

## 四、未來擴展 UX
- **合規報告一鍵產出**, **AI 輔助檢漏**.
