# SpecOps 車載解決方案 (Automotive Solution)

> 版本: v4.1  
> 角色: 領域專屬標籤、合規與工具對接 (Plugin)

---

## 一、系統目標 (車載專項)

針對車載儀表開發，利用圖譜技術 (Graph) 提升：

- **Traceability**: 因果層級需求追蹤。
- **Consistency**: 跨章節邏輯衝突自動偵測。
- **Safety**: 符合 ISO 26262 功能安全。

---

## 二、ISO 26262 標籤設計 (Compliance Labels)

精細化定義安全相關元數據。

### 1. 需求分層

- `FSR` (Functional Safety Requirements)
- `TSR` (Technical Safety Requirements)
- `HSR` (Hardware Safety Requirements)
- `SSR` (Software Safety Requirements)

### 2. 安全元數據 (Properties)

- `ASIL`: [QM, A, B, C, D]
- `Inheritance`: 標記分解後的原始父項。
- `DECOMPOSED_TO`: ASIL 分解路徑。

---

## 三、外部訊號整合 (Signal Integration)

解決「規格描述」與「底層訊號」的脫節。

### 1. 支持格式

- **DBC**: CAN 通訊矩陣解析。
- **ARXML/LDF**: Ethernet/LIN 服務定義。

### 2. 語義校準流程 (Semantic Alignment)

由於規格書使用自然語言（如 Vehicle Speed）而 DBC 使用技術縮寫（如 Veh_Spd），需建立校準機制：

1. **Extraction**: LLM 從規格書提取所有與訊號相關的自然語言詞彙。
2. **Auto-Mapping**: LLM 根據語義相似度，預測其對應的 DBC Message 與 Signal。
3. **Glossary Entry**: 將預測結果寫入 `signal_glossary.json`，狀態標記為 `DRAFT`。
4. **Human Correction**: 工程師透過 UI 工具校正誤判，並將狀態改為 `APPROVED`。

### 3. 校驗機制 (Consistency Check)

- **Signal Mapping**: 將 `Signal` 節點 `MAPS_TO` 需求節點（依據 `signal_glossary.json`）。
- **Range Check**: 自動比對規格數值範疇與 DBC 定義。

---

## 四、車載變體實務 (Variant Implementation)

管理多套硬體（Entry, Mid, High-end）開發。

### 1. 變體策略

- **Common Spec**: 80% 共通功能。
- **Variant Delta**:
  - `High-end`: 3D 渲染、ADAS。
  - `Entry-level`: Segment LCD 簡化邏輯。

### 2. 輸出控制

- 根據「變體代碼」自動篩選需求組合。

---

## 五、ALM 整合：Codebeamer Sync

### 1. 同步策略

- 只有 `APPROVED` 狀態且通過品質校驗的需求才同步。
- **同步內容**: `REQ-ID`, `Description`, `Traceability Link`.

### 2. 反向追蹤

- Codebeamer 需求項目保留回溯本系統 (Split-View) 的 URL。

---

## 六、MinerU 車載配置 (Parsing Setup)

- **Layout JSON**: 精確捕捉表格坐標，支援一鍵回溯 PDF 原文。
- **Table CSV**: 提取燈號矩陣與通訊定義表。
