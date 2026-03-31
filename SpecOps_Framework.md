# SpecOps 核心框架 (Framework)

> 版本: v4.3  
> 角色: 核心邏輯、原則與通用流程

---

## 一、系統目標

透過 LLM 與 圖譜技術，解決規格工程中「追蹤難、更新慢、檢核累」的痛點。
- **效率**: 自動化生成初步需求與測試案例。
- **精確度**: 跨章節邏輯衝突自動偵測。
- **完整性**: 確保規格內容 100% 覆蓋需求。
- **可追蹤性**: 全流程雙向追蹤 (Bi-directional Traceability)。

---

## 二、核心設計原則

1. **全流程可追蹤**: `SPEC → NOTE → REQUIREMENT → TEST REQUIREMENT`。
2. **Human-in-the-loop**: LLM 為輔，人工審查為最終準則。
3. **全資料留存 (Auditability)**: 儲存所有 LLM 原始輸入/輸出與人工修正紀錄。
4. **模組化變體**: 支援 Base + Overlay 模式管理多機種差異。
5. **知識閉環 (Knowledge Loop)**: 系統從人工核准的資料中自動學習，形成企業級知識庫與「白銀資料集」。

---

## 三、四大核心階段 (The 4-Stage Process)

1. **階段 1: Spec 結構化 (PDF → Markdown)**: 解決 OCR 與版面解析問題。
2. **階段 2: 規格理解對齊 (Note Generation)**: 建立語義中繼站，過濾雜訊。
3. **階段 3: 需求生成 (Req Generation)**: 從 Note 衍生出可測試的需求。
4. **階段 4: 測試需求 (Test Req Generation)**: 確保需求可驗證。

---

## 四、結構化審查系統 (Review System)

採用 **Atomic Review（單條審查）** 模式。

### 審查狀態機 (Status Machine)
- `DRAFT`: 待審查。
- `APPROVED`: 通過審查。**自動同步至 Silver Dataset** 作為 AI 學習範本。
- `REJECTED`: 退回修正。需強制選擇結構化標籤。
- `FIXING`: 系統根據退回標籤進行 **Self-Fix (自動修正)**。
- `FIXED`: 修正後重啟流程，待人工二次審查。
- `IMPACTED`: 因上層變動導致失效。

---

## 五、變更管理 (Change Management)

實現 **Automated Impact Analysis**。

### 1. 影響分析流程
1. **Markdown Diff**: 對比新舊版規格。
2. **Impact Analysis**: 識別受影響的下游節點。
3. **Propagation**: 自動將相關節點改為 `IMPACTED`。

### 2. 變體同步策略 (Variant Sync Strategy)
- **Version Locking**: Overlay 預設鎖定在特定 Base 版本。
- **Manual Sync**: 需由工程師手動觸發「版本同步」，確保開發環境穩定。

---

## 六、品質校驗 (Quality Validation)

1. **結構檢核**: JSON Schema 與 ID 唯一性檢查。
2. **語義檢核 (GraphRAG)**: 利用圖譜檢索確保跨章節邏輯的一致性。
3. **多代理共識評分 (Multi-Agent Consensus)**: 使用「分析師」與「審核員」兩個獨立 Agent 對產出進行多維度評分與辯論。
4. **品質預警機制 (Quality Hotspot Map)**: 視覺化呈現低置信度或高退回率的規格章節。
5. **預算控管 (Budget Cap)**: 設定 Token 消耗上限。

---

## 七、資料遷移與架構演進 (Data Evolution)

確保系統升級時，歷史專案資料的可用性。
- **Schema Versioning**: 所有資料物件皆附帶版本標籤。
- **Auto-Migration**: 系統提供升級腳本，自動將舊格式 JSON 遷移至新版架構。

---

## 八、未來展望 (Future Outlook)

1. **合規閉環 (Compliance Loop)**: 自動生成 ISO 26262/21434 合規證明報告與 FMEA 映射。
2. **測試閉環 (Test Feedback Loop)**: HIL/SIL 測試結果自動反向回溯。
3. **AI 輔助檢漏**: 系統自動提示可能遺漏的需求章節。
