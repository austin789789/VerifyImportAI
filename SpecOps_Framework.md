# SpecOps 核心框架 (Framework)

> 版本: v4.1  
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
- `APPROVED`: 通過審查。
- `REJECTED`: 退回修正。
- `FIXED`: 修正後重啟流程。
- `IMPACTED`: 因上層變動導致失效。

---

## 五、變更管理 (Change Management)

實現 **Automated Impact Analysis**。

1. **Markdown Diff**: 對比新舊版規格。
2. **Impact Analysis**: 識別受影響的下游節點（Note, Req, Test, Signal）。
3. **Propagation**: 自動將相關節點改為 `IMPACTED` 並高亮顯示。

---

## 六、品質校驗 (Quality Validation)

1. **結構檢核**: JSON Schema 與 ID 唯一性檢查。
2. **語義檢核 (GraphRAG)**:
   - **Coverage Check**: 檢查 Spec 是否皆有對應需求。
   - **Conflict Detection**: 偵測邏輯矛盾與互斥。
3. **自動化數據校驗 (Data Cross-Check)**: 自動對比需求描述與底層訊號定義 (DBC/ARXML) 是否吻合。
4. **置信度門檻 (Confidence Gate)**: LLM 生成時需附帶置信評分，低於 `0.8` 時觸發人工高風險審查標記。

---

## 七、變體與配置管理 (Variant & Configuration)

- **Base (基準層)**: 存儲跨機種共享的「通用規格」。
- **Overlay (疊加層)**: 存儲特定機種的差異化改動。
- **Resolution**: 動態生成最終視圖：`Final = Base + Overlay`。
