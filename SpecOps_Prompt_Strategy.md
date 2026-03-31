# SpecOps AI 策略 (Prompt Strategy)

> 版本: v4.3  
> 角色: AI 角色定義、CoT 與 安全脫敏

---

## 一、階段性角色定義 (Role-based Strategy)

### 1. Stage 1 (解析器 - Parser)
- PDF 轉換 Markdown、表格提取、漏字校正。

### 2. Stage 2 (分析師 - Analyst)
- 規格邏輯提煉、隱含邊界條件識別。

### 3. Stage 3 (架構師 - Architect)
- 需求拆解、邏輯一致性檢核 (CoT)。

### 4. Stage 4 (修正者 - Corrector)
- 根據退回標籤進行精準修正。

---

## 二、多代理共識評分 (Multi-Agent Consensus)

為了解決評估模型不足的問題，採用多代理辯論機制。

### 1. 代理職責
- **Agent A (分析師 Analyst)**: 檢查「語義完整度」，確認是否漏掉規格書中的數值或限制。
- **Agent B (審核員 Auditor)**: 檢查「規範性與安全性」，確認是否符合 ISO 26262 格式與資安原則。

### 2. 評分機制
- 兩者獨立評分 (0-10)。
- 若分數差異 > 3，觸發「代理辯論」機制，由第三個 Agent 進行仲裁或標記為高風險人工審查。

---

## 三、知識閉環與白銀資料集 (Knowledge Loop)

### 1. 學習來源
- 系統自動將 `APPROVED` 狀態且 `edit_distance` 極小的需求存入 **Silver Dataset**。
- **Few-shot Injection**: 在後續生成時，從 Silver Dataset 中檢索相似規格作為範本注入 Prompt。

---

## 四、大規模規格處理與圖譜檢索 (Large-Scale GraphRAG)

針對 500 頁以上的規格書，使用圖譜檢索代替單純向量搜尋。
- **Hierarchical Chunking**: 按標題層級切片。
- **Graph Traversal**: 沿著 `DEPENDS_ON` 或 `CONFLICTS_WITH` 邊尋找跨章節關聯。

---

## 五、安全性與部署 (Security & Deployment)

### 1. 脫敏機制
- **Regex Masker**, **LLM Scrubber**.

### 2. 部署藍圖
- **Phase 1**: 雲端 API + 脫敏。
- **Phase 2**: 地端私有化模型。
