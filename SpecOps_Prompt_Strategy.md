# SpecOps AI 策略 (Prompt Strategy)

> 版本: v4.1  
> 角色: AI 角色定義、CoT 與 安全脫敏

---

## 一、階段性角色定義 (Role-based Strategy)

### 1. Stage 1 (解析器 - Parser)

- **定位**: 精準文字掃描員。
- **專注**: PDF 轉換 Markdown、表格提取、漏字校正。

### 2. Stage 2 (分析師 - Analyst)

- **定位**: 資深規格工程師。
- **專注**: 規格邏輯提煉、隱含邊界條件識別。

### 3. Stage 3 (架構師 - Architect)

- **定位**: 資深系統架構師。
- **專注**: 需求拆解、邏輯一致性檢核 (CoT)。

---

## 二、思維鏈模板 (Chain of Thought - CoT)

確保 LLM 生成邏輯穩定、可追溯。

```text
[System] You are a Senior Architect...
[Task] Break down the SPEC block into Requirements...
[Thinking Process] 
1. Identify functional actions.
2. Identify constraints (HW, SW, Performance).
3. Cross-check with global standards (e.g., ISO26262).
4. Map to target JSON Schema.
```

---

## 三、安全性與部署 (Security & Deployment)

### 1. 脫敏機制 (Data Masking)

- **Regex Masker**: 過濾 IP、人名、專案代號。
- **LLM Scrubber**: 使用本地端小型模型進行語義脫敏。

### 2. 部署藍圖

- **Phase 1**: 雲端 API + 安全脫敏。
- **Phase 2**: 地端私有化模型 (Llama 3 / DeepSeek)。

---

## 四、Prompt 管理機制

存儲路徑與版本：

```text
prompts/
  stage1/ (Parser)
  stage2/ (Analyst)
  stage3/ (Architect)
```

- **Registry**: 記錄「模型版本-提示詞-性能分數」對應表。
- **Feedback Loop**: 收集人工審查意見，自動標籤化分析以優化 Prompt。

---

## 五、大規模規格處理策略 (Large-Scale Spec Handling)

針對 500 頁以上的超大型規格書，避免 Context Window 溢出且不丟失全域關聯。

### 1. 分層切片 (Hierarchical Chunking)

- **結構化切分**: 不使用固定字數切片，而是根據 MinerU 解析的 Markdown 標題層級（Chapter > Section > Block）進行物理切分。
- **重疊機制 (Overlapping)**: 每個區塊保留 10% 的上下文重疊，確保跨頁邏輯不中斷。

### 2. 全域背景注入 (Global Context Injection)

- **GCI 索引**: 每一條發送給 LLM 的 Prompt 都會附帶一份「全域索引」，包含：
  - **Table of Contents (TOC)**: 當前區塊在全體規格中的位置。
  - **Definition List**: 全規格統一的縮寫與定義。
  - **Shared Signals**: 跨模組共用的關鍵訊號 (如 Speed, Gear)。

### 3. 生成策略 (Generation Pattern)

- **Map-Reduce 模式**:
  - **Map**: 各個區塊並行產出初步需求。
  - **Reconcile (Reduce)**: 針對具有 `DEPENDS_ON` 關係的區塊，進行二次校驗，確保邏輯不衝突（如：第 1 章的電源定義與第 10 章的休眠邏輯是否一致）。

---

## 六、幻覺偵測與質量護欄 (Hallucination Guardrails)

除了人工審查，系統內建三道自動化防線。

### 1. 數據校驗 (Data Cross-Check)

- **Signal-to-Text**: 系統自動比對 LLM 產出的數值描述與 `Signal` 節點（DBC/ARXML）的定義。若 LLM 寫入「0-255」但 DBC 定義為「0-100」，自動標記高風險。
- **Template Match**: 檢查產出是否符合特定的車載語義模板。

### 2. 邏輯校驗 (Self-Correction Loop)

- **雙模型互檢 (Dual-Model Check)**: 使用較強的模型（如 GPT-4o）對較輕量模型（如 Llama 3）的產出進行邏輯矛盾偵測。
- **矛盾路徑偵測**: 在圖譜中尋找是否存在 `CONFLICTS_WITH` 的環狀路徑。

### 3. 置信度門檻 (Confidence Gate)

- LLM 在輸出 JSON 時需附帶 `llm_confidence` 評分。
- 評分 `< 0.8` 的項目，在 UI 介面中強制標註為「需重點審查」。
