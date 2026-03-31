# SpecOps 操作流程 (UX Workflow)

> 版本: v4.2  
> 角色: 目錄結構、UI 原型與審查 SOP

---

## 一、專案目錄架構 (Directory Structure)
...

---

## 二、UI/UX 原型設計 (Split-View Reviewer)

### 1. 雙欄對照介面 (Split View)
- **Source View (左)**: 渲染規格 Markdown。
- **Editor View (右)**: LLM 產出的需求表單。

### 2. 變更與同步儀表板 (Impact & Sync Dashboard)
- **紅色標記**: `IMPACTED` 節點。
- **Version Sync 按鈕**: 當 Base 規格有新版本時，顯示「Sync to Base (New Commit)」按鈕。點擊後系統自動對比差異並標記受影響範圍。

### 3. 訊號映射工具 (Signal Mapper Tool)
...

### 4. 品質預警視圖 (Quality Hotspot Map)
- **Heatmap 顯示**: 導覽樹背景顏色根據「品質分數」變化。
- **紅色區塊**: 表示該章節頻繁被 `REJECTED` 或 `llm_confidence < 0.8`。
- **預算進度條**: 顯示目前 Token 消耗與預算上限的比率。

---

## 三、人工審查標準作業程序 (Review SOP)

### 審查流程
1. **Atomic Select**: 選擇一條 `DRAFT` 狀態的需求。
2. **Context Check**: 參照 Source View 確認原文。
3. **Decision**:
   - `APPROVED`: 進入追蹤鏈。
   - **`REJECTED`**: 系統強制彈出 **「退回理由標籤選擇器」**（如：語義錯誤、格式問題）。
4. **Self-Fix Loop**: 點擊 `REJECTED` 後，系統自動觸發 LLM 根據標籤內容進行修正，狀態變更為 `FIXING`。
5. **Re-Review**: 修正完成後，工程師進行第二次審查，核對修正結果。

---

## 四、未來擴展 UX
- **AI 輔助檢漏**, **Coverage 圖表**.
