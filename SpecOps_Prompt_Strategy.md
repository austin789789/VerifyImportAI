# SpecOps AI 策略 (Prompt Strategy)

> 版本: v4.5  
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

### 5. Stage 5 (調和者 - Harmonizer / Signal-Sync)
- 當底層通訊協議變更時，自動修正需求中的數值描述與物理單位。

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

### 1. 學習與精選機制
- **Silver Dataset**: 僅存入 `APPROVED` 狀態且 `edit_distance` 極小的需求。
- **Architect Selection**: 定期由資深架構師進行二次精選，移除冗餘或過時邏輯。
- **Validity Period**: 所有條目預設有效期為 **3 年**，過期需重新評估或降級。

### 2. 數據安全與隱私隔離 (NDA Isolation)
- **Visibility Labels**: 所有 Silver Dataset 條目必須標註權限：
    - `GLOBAL`: 通用產業知識，可跨專案使用。
    - `BRAND`: 特定客戶 (OEM) 規範，僅限該品牌專案使用。
    - `PROJECT`: 極度敏感邏輯，僅限原專案使用。
- **NDA-aware Injection**: 在 Prompt 生成階段，系統強制根據當前專案背景過濾不符權限的條目，防止技術方案洩漏。

### 3. 生成注入
- **Few-shot Injection**: 在後續生成時，從精選且符合隱私標籤的 Silver Dataset 中檢索相似規格作為範本注入 Prompt。

---

## 四、大規模規格處理與圖譜檢索 (Large-Scale GraphRAG)

針對 500 頁以上的規格書，使用圖譜檢索代替單純向量搜尋。
- **Hierarchical Chunking**: 按標題層級切片。
- **Graph Traversal**: 沿著 `DEPENDS_ON` 或 `CONFLICTS_WITH` 邊尋找跨章節關聯。
- **Visual Calibration**: 支援人工透過 UI 修正圖譜關係，跨章節修改需經由 `Edge Request` 流程。

---

## 五、安全性與部署 (Security & Deployment)

### 1. 脫敏機制
- **Regex Masker**, **LLM Scrubber**.

### 2. 部署藍圖
- **Phase 1**: 雲端 API + 脫敏。
- **Phase 2**: 地端私有化模型。
