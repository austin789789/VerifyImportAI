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
