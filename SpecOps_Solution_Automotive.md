# SpecOps 車載解決方案 (Automotive Solution)

> 版本: v4.6  
> 角色: 車載領域專屬標籤、合規流程、Signal-Sync 與 ALM 對接

---

## 一、系統目標 (車載專項)

針對車載儀表與控制系統開發，強化：

- **Traceability**: 從 spec 到 requirement、test requirement、signal 與 ALM 項目之完整追蹤。
- **Consistency**: 跨章節、跨變體、跨訊號定義的一致性檢查。
- **Safety & Security**: 對齊 ISO 26262 與 ISO 21434 的審查與證據要求。

---

## 二、合規標籤設計 (Compliance Labels)

### 1. ISO 26262

- `FSR`, `TSR`, `HSR`, `SSR`
- `ASIL`: `QM | A | B | C | D`

### 2. ISO 21434

- `CSR`
- `CAL`: `QM | 1 | 2 | 3 | 4`

### 3. 掛載原則

- `ASIL`, `CAL`, requirement class 掛載於 `requirement` 與 `test_requirement`。
- `THREAT` 與 `CONTROL` 為 graph node。
- `MITIGATED_BY` 用於 threat/control 與 requirement/control 關係。

### 4. 風險重估

- 當 safety/security 相關 artifact 進入 `IMPACTED` 或 `MANUAL_RECOVERY` 時，必須建立 risk re-assessment item。

---

## 三、外部訊號整合 (Signal Integration)

### 1. 支援格式

- `DBC` for CAN
- `ARXML` for AUTOSAR / Ethernet related definitions
- `LDF` for LIN

### 2. Signal Glossary

- 使用 `signal_glossary.json` 維護自然語言、縮寫、枚舉值與單位對應。

### 3. Signal-Sync

- 僅對已建立 `signal_mapping` 的 artifact 啟動。
- 支援數值、單位、枚舉值與欄位名稱變更檢查。
- 多對一或一對多映射為高風險場景，預設轉入 `MANUAL_RECOVERY`。

### 4. Mapping Status

- `DRAFT`
- `APPROVED`
- `STALE`

---

## 四、工具鑑定與穩定性 (Tool Qualification)

### 1. Golden Test Suite

- 維護標準 spec、note、requirement、signal mapping 與 expected output。
- Prompt、模型、抽取規則或同步邏輯變更後必須執行回歸。
- Ground truth 必須定期人工覆核。

### 2. 最低評估項目

- requirement extraction precision / recall
- signal-sync exact match rate
- safety/security false negative rate
- auto-fix approval rate

---

## 五、車載變體實務 (Variant Implementation)

- 採 `Base + Overlay`。
- Overlay override 類型至少包含 `add`, `modify`, `suppress`, `rebind_signal`。
- Base 版本變更後只同步 impacted scope。

---

## 六、ALM 整合：Codebeamer Sync

### 1. 同步原則

- 僅 `APPROVED` artifact 可同步。
- 同步內容包含 requirement 本體、合規標籤、trace 與 audit reference。
- 同步需支援 idempotent retry 與 partial failure recovery。

### 2. Source of Truth

- SpecOps 為需求生成與審查真相來源。
- Codebeamer 為外部協作與 ALM 消費端。

詳細欄位映射由 `SpecOps_Integration_Codebeamer.md` 承接。

---

## 七、Parser / MinerU 車載配置

- `Layout JSON`: 保存頁面區塊與表格座標。
- `Table CSV`: 提取燈號矩陣、診斷碼與通訊定義。
- 對解析失真區塊應保留人工校正入口與原文回鏈。
