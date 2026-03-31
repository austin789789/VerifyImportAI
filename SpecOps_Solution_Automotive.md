# SpecOps 車載解決方案 (Automotive Solution)

> 版本: v4.3  
> 角色: 領域專屬標籤、合規與工具對接 (Plugin)

---

## 一、系統目標 (車載專項)

針對車載儀表開發，利用圖譜技術 (Graph) 提升：
- **Traceability**: 因果層級需求追蹤。
- **Consistency**: 跨章節邏輯衝突自動偵測。
- **Safety & Security**: 符合 ISO 26262 功能安全與 ISO 21434 道路車輛資安。

---

## 二、合規標籤設計 (Compliance Labels)

精細化定義安全與資安相關元數據。

### 1. ISO 26262 功能安全
- `FSR`, `TSR`, `HSR`, `SSR`.
- `ASIL`: [QM, A, B, C, D].

### 2. ISO 21434 道路車輛資安
- `CSR` (Cybersecurity Requirements).
- `CAL`: [QM, 1, 2, 3, 4] (Cybersecurity Assurance Level).
- **TARA 整合**: 在圖譜中新增 `THREAT` 節點與 `MITIGATED_BY` 關係。

---

## 三、外部訊號整合 (Signal Integration)

解決「規格描述」與「底層訊號」的脫節。

### 1. 支持格式
- **DBC** (CAN), **ARXML/LDF** (Ethernet/LIN).

### 2. 語義校準流程 (Semantic Alignment)
- **Signal Glossary**: 維護 `signal_glossary.json` 對應自然語言與技術縮寫。
- **Mapping Status**: AI 預測映射 (DRAFT) 與人工校正核准 (APPROVED)。

---

## 四、車載變體實務 (Variant Implementation)

管理多套硬體（Entry, Mid, High-end）開發。
- **Common Spec**, **Variant Delta**.
- **Version Locking**: 變體層鎖定基準層版本。

---

## 五、ALM 整合：Codebeamer Sync

### 1. 同步策略
- 只有 `APPROVED` 狀態的需求才進入同步。
- 同步內容包含 `ASIL/CAL` 等合規標籤。

---

## 六、MinerU 車載配置 (Parsing Setup)

- **Layout JSON**: 捕捉表格坐標，支援回溯 PDF 原文。
- **Table CSV**: 提取燈號矩陣與通訊定義。
