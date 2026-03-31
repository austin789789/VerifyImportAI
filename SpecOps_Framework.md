# SpecOps 核心框架 (Framework)

> 版本: v4.4 -> v4.5  
> 角色: 核心邏輯、原則與通用流程

---

## 一、系統目標

透過 LLM 與 圖譜技術，解決規格工程中「追蹤難、更新慢、檢核累」的痛點。
- **效率**: 自動化生成初步需求與測試案例。
- **精確度**: 跨章節邏輯衝突自動偵測。
- **完整性**: 確保規格內容 100% 覆蓋需求。
- **可追蹤性**: 全流程雙向追蹤 (Bi-directional Traceability)。
- **合規證據**: 提供符合 ISO 26262/21434 的自動化審計追蹤 (Audit Rationale)。

---

## 二、核心設計原則

1. **全流程可追蹤**: `SPEC → NOTE → REQUIREMENT → TEST REQUIREMENT`。
2. **Human-in-the-loop**: LLM 為輔，人工審查為最終準則。
3. **數據隱私與 NDA 隔離 (Data Isolation)**: 確保跨專案、跨品牌 (OEM) 的知識不被 AI 學習洩漏。
4. **全資料留存 (Auditability)**: 儲存所有 LLM 原始輸入/輸出、Prompt 版本與人工修正紀錄。
5. **模組化變體**: 支援 Base + Overlay 模式管理多機種差異。
6. **知識閉環 (Knowledge Loop)**: 系統從人工核准且經過資深架構師精選的資料中自動學習，建立具備時效性 (3 年) 的「白銀資料集」。

---

## 三、四大核心階段 (The 4-Stage Process)

1. **階段 1: Spec 結構化 (PDF → Markdown)**: 解決 OCR 與版面解析問題。
2. **階段 2: 規格理解對齊 (Note Generation)**: 建立語義中繼站，過濾雜訊。
3. **階段 3: 需求生成 (Req Generation)**: 從 Note 衍生出可測試的需求。
4. **階段 4: 測試需求 (Test Req Generation)**: 確保需求可驗證。
5. **階段 5: 變更同步 (Signal-Sync)**: 底層訊號變更後的自動修正機制。

---

## 四、結構化審查系統 (Review System)

採用 **Atomic Review（單條審查）** 與 **Section Locking（章節鎖定）** 模式。

### 併發衝突管理
- **Pessimistic Locking**: 使用者編輯某章節時，系統鎖定該區段，防止並行衝突。
- **Edge Request**: 跨章節連線修改權限採請求核准制 (Pending Request)。

### 審查狀態機 (Status Machine)
- `LOCKED`: 某使用者正在編輯該章節，其他使用者僅能讀取 (唯讀)。
- `DRAFT`: 待審查。
- `APPROVED`: 通過審查。**自動同步至 Silver Dataset** 作為 AI 學習範本。
- `REJECTED`: 退回修正。需強制選擇結構化標籤。
- `FIXING`: 系統根據退回標籤進行 **Self-Fix (自動修正)**。
- `FIXED`: 修正後重啟流程，待人工二次審查。
- `IMPACTED`: 因上層變動或訊號更新導致失效。
- `MANUAL_RECOVERY`: 複雜變更導致 AI 置信度過低，強制進入人工修復。

---

## 五、變更管理 (Change Management)

實現 **Automated Impact Analysis** 與 **Signal-Sync**。

### 1. 影響分析流程
1. **Markdown Diff**: 對比新舊版規格。
2. **Impact Analysis**: 識別受影響的下游節點。
3. **Signal Integration**: 當底層訊號 (DBC/ARXML) 變更時，觸發 **Signal-Sync Agent** 自動修正需求數值 (若 Confidence > 0.6)。
4. **Propagation**: 自動將相關節點改為 `IMPACTED` 或 `FIXED (Auto)`。

### 2. 變體同步策略 (Variant Sync Strategy)
- **Version Locking**: Overlay 預設鎖定在特定 Base 版本。
- **Manual Sync**: 需由工程師手動觸發「版本同步」，確保開發環境穩定。

---

## 六、品質校驗 (Quality Validation)

1. **結構檢核**: JSON Schema 與 ID 唯一性檢查。
2. **語義檢核 (GraphRAG)**: 利用圖譜檢索確保跨章節邏輯的一致性，並支援視覺化校準。
3. **多代理共識評分 (Multi-Agent Consensus)**: 使用「分析師」與「審核員」兩個獨立 Agent 對產出進行多維度評分與辯論。
4. **審計追蹤 (Audit Rationale)**: 系統產出需求時，自動記錄引用的 PDF 座標、Prompt 版本與 Silver Dataset 參考條目，作為合規證據。
5. **系統穩定性回歸 (Golden Test Suite)**: 每次升級 AI 邏輯後，自動執行對標測試，確保輸出一致性。
6. **品質預警機制 (Quality Hotspot Map)**: 視覺化呈現低置信度或高退回率的規格章節。
7. **預算控管 (Budget Cap)**: 以章節為單位預估 Token 消耗。

---

## 七、資料遷移與架構演進 (Data Evolution)

確保系統升級時，歷史專案資料的可用性。
- **Schema Versioning**: 所有資料物件皆附帶版本標籤。
- **Auto-Migration**: 系統提供升級腳本，自動將舊格式 JSON 遷移至新版架構。

---

## 八、未來展望 (Future Outlook)

1. **合規閉環 (Compliance Loop)**: 自動生成 ISO 26262/21434 合規證明報告與 FMEA 映射。
2. **多模態解析 (Multimodal Parsing)**: 自動解析 PDF 中的圖片、流程圖與狀態轉移圖。
3. **測試閉環 (Test Feedback Loop)**: HIL/SIL 測試結果自動反向回溯。
4. **AI 輔助檢漏**: 系統自動提示可能遺漏的需求、測試需求。
5. **AI 輔助撰寫測試案例**: 系統依據Graph自動產出測試案例。
