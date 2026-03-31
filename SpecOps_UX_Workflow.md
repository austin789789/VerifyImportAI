# SpecOps 操作流程 (UX Workflow)

> 版本: v4.1  
> 角色: 目錄結構、UI 原型與審查 SOP

---

## 一、專案目錄架構 (Directory Structure)

```text
品牌/
  系列/
    機種/
      v1.0/
        spec/ (Raw, Markdown, Review Log)
        note/ (Refined Spec Notes)
        graph/ (Graph Store)
        requirement/ (JSON/CSV)
        test_requirement/ (JSON/CSV)
        traceability/ (Trace Matrix)
```

---

## 二、UI/UX 原型設計 (Split-View Reviewer)

聚焦於「原文對照」與「變更引導」。

### 1. 雙欄對照介面 (Split View)

- **Source View (左)**: 渲染規格 Markdown，高亮當前審查區塊。
- **Editor View (右)**: LLM 產出的需求表單 (JSON)，提供編輯與審查按鈕。

### 2. 變更儀表板 (Impact Dashboard)

- **紅色標記**: `IMPACTED` 節點。
- **Diff Mode**: 自動對比新舊版需求差異，引導工程師修正。

---

## 三、人工審查標準作業程序 (Review SOP)

確保每一筆 LLM 產出皆經過精確核實。

### 審查流程

1. **Atomic Select**: 選擇一條 `DRAFT` 狀態的需求。
2. **Context Check**: 參照 Source View 確認原文意圖。
3. **Decision**:
   - `APPROVED`: 進入追蹤鏈。
   - `REJECTED`: 填寫 `human_opinion` 退回。
4. **Impact Review**: 若為 `IMPACTED` 節點，優先檢查 Diff。

---

## 四、未來擴展 UX

- **AI 輔助檢漏**: 系統自動提示可能遺漏的需求章節。
- **Coverage 圖表**: 視覺化呈現規格覆蓋率。
