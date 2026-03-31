# SpecOps AI 策略 (Prompt Strategy)

> 版本: v4.6  
> 角色: AI 角色、評分治理、知識注入與脫敏規則

---

## 一、階段性角色定義 (Role-based Strategy)

### 1. Stage 1: Parser

- PDF 轉 Markdown、表格提取、來源座標回填、章節切片。

### 2. Stage 2: Analyst

- 提煉規格邏輯、找出限制、例外與邊界條件，產出 Note 與初步圖譜關聯。

### 3. Stage 3: Architect

- 產出 Requirement，檢查可測性、約束保真度與追蹤鏈完整性。

### 4. Stage 4: Corrector

- 根據 rejection tags、impact scope 與 reviewer 意見做精準修正。

### 5. Stage 5: Harmonizer / Signal-Sync

- 處理底層訊號、變體與外部資料變更後的同步修正。

---

## 二、多代理共識評分 (Multi-Agent Consensus)

### 1. 代理職責

- **Agent A / Analyst**: 檢查覆蓋率、數值與限制條件完整性。
- **Agent B / Auditor**: 檢查規範性、測試性與 safety/security 風險。
- **Agent C / Arbiter**: 只在高分歧或高風險時仲裁。

### 2. 評分維度

- `coverage_completeness`
- `constraint_fidelity`
- `testability`
- `terminology_consistency`
- `safety_security_compliance`

### 3. Gate 規則

- 各代理分數範圍為 `0-10`。
- 平均分 `< 8.0` 不得自動通過。
- `safety_security_compliance < 7.0` 時必須人工審查。
- 任兩代理分差 `> 3` 時觸發仲裁。

---

## 三、知識閉環與 Silver Dataset

### 1. 收錄流程

1. artifact 先被標記為 `APPROVED`
2. 進入 `silver_candidate`
3. 經 quality gate、privacy gate 與抽樣精選
4. 成為 `silver_dataset_entry`

### 2. 收錄準則

- `edit_distance` 應以 normalized metric 量測。
- 不得因修飾性編輯掩蓋實質邏輯變更。
- safety/security 相關要求若被人工重寫過多，預設不自動升級。

### 3. 注入原則

- 僅可注入符合 `visibility`、`brand_id`、`project_id` 與 `allowed_use_cases` 的條目。
- 注入時保留來源標識，方便審計與失效清理。

---

## 四、大規模規格處理與 GraphRAG

- 500 頁以上規格優先使用階層切片加圖譜檢索。
- 先檢索同節點與直接上游，再擴展到 `DEPENDS_ON`、`CONFLICTS_WITH`。
- 跨章節圖譜修改必須走 `Edge Request`。

---

## 五、安全性與部署 (Security & Deployment)

### 1. 脫敏機制

- 先執行規則型 `Regex Masker`，再執行語義型 `LLM Scrubber`。
- 不允許將未脫敏高敏感欄位直接送往雲端模型。
- 稽核留存格式必須遵守 `SpecOps_Privacy_Audit_Policy.md`。

### 2. 部署藍圖

- **Phase 1**: 雲端 API + 脫敏閘門 + 審計留存。
- **Phase 2**: 地端私有化模型處理高敏感專案。

---

## 六、Auto-Fix / Signal-Sync 原則

- 只有通過 eligibility check 的 impacted artifact 才能 auto-fix。
- 低於 `0.6` 的 confidence 不得直接覆寫核准內容。
- 所有 auto-fix 結果必須輸出 diff、引用依據與 `fix_rationale`。
