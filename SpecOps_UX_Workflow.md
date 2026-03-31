# SpecOps 操作流程 (UX Workflow)

> 版本: v4.6  
> 角色: 目錄結構、介面原型、審查 SOP 與例外流程

---

## 一、專案目錄架構 (Directory Structure)

- `spec/`, `note/`, `graph/`, `requirement/`, `test_requirement/`, `traceability/`, `audit/`, `integration/`
- `library/`: 存放 glossary、共通規則、Silver 索引與品牌映射資料

---

## 二、UI/UX 原型設計

### 1. Split View Reviewer

- 左側 `Source View`: 顯示來源章節、引用座標、版本差異。
- 右側 `Editor / Review View`: 顯示 Note / Requirement / Test Requirement 與狀態。
- 顯示 `Locking Status`、`status badge`、`visibility badge`、`audit trace`。

### 2. Graph Visual Editor

- `Pending Edges` 以虛線顯示。
- `Conflict Highlight` 顯示 `CONFLICTS_WITH` 與 impact 節點。
- 支援 request preview，顯示 edge 變更前後差異。

### 3. Impact & Sync Dashboard

- 顯示 `IMPACTED`、`AUTO_FIXED_PENDING_REVIEW`、`MANUAL_RECOVERY` 清單。
- 顯示 auto-fix diff、confidence、owner、due date、severity。
- 支援依品牌、專案、變體、章節與狀態篩選。

### 4. Privacy & Audit View

- 推薦清單必須顯示 `GLOBAL / BRAND / PROJECT`。
- 點擊 artifact 可查看生成依據、引用來源、Prompt / model version。

---

## 三、人工審查標準作業程序 (Review SOP)

1. **Acquire Lock**: 取得章節鎖或進入唯讀比較模式。
2. **Review Impact Queue**: 優先處理 `MANUAL_RECOVERY` 與 `IMPACTED`。
3. **Inspect Diff & Rationale**: 檢查 auto-fix diff、來源與修正理由。
4. **Decision**:
   - `APPROVED`: 核准 artifact，本身成為正式資料，另標記為 `silver_candidate`。
   - `REJECTED`: 選擇結構化原因標籤並可附文字說明。
5. **Graph Calibration**: 跨章節 edge 修改需等待對側核准。
6. **Close Review**: 釋放鎖、更新 trace 與審計紀錄。

---

## 四、例外流程與操作回復

- **Lock 取得失敗**: 可加入 waitlist 或進入唯讀 compare mode。
- **Lock 即將到期**: 到期前 5 分鐘提醒續租。
- **Lock 已過期**: 若未續租，保留本地未提交變更但不得自動覆蓋伺服端版本。
- **Edge Request 超時**: 自動失效並通知發起者。
- **Auto-Fix 失敗**: 直接進入 `MANUAL_RECOVERY`。
- **高風險項目**: safety/security 類別在 UI 上應強制顯示顯著警示。

---

## 五、未來擴展 UX

- 一鍵產出合規報告
- 多模態圖表與流程圖解析回顯
- 批次 review queue 與 team workload dashboard
