# SpecOps 與 Codebeamer 整合規格 (Integration Codebeamer)

> 版本: v1.0  
> 角色: 定義同步契約、欄位映射、錯誤處理與責任邊界

---

## 一、整合原則

- 只有 `APPROVED` artifact 可同步到 Codebeamer。
- 同步為 downstream publishing，不反向覆寫 SpecOps 正式內容。
- 同步需具備 idempotency key。

---

## 二、欄位映射

| SpecOps Field | Codebeamer Field | Required | Notes |
|---|---|---|---|
| `id` | External ID | Yes | 穩定唯一鍵 |
| `title` | Name | Yes | 簡述 |
| `statement` | Description | Yes | 主內容 |
| `status` | Workflow State | Yes | 僅同步 APPROVED |
| `compliance.asil` | ASIL | Conditional | ISO 26262 項目 |
| `compliance.cal` | CAL | Conditional | ISO 21434 項目 |
| `audit_rationale_id` | Rationale Link | Yes | 追溯依據 |
| `source_spec_ids` | Upstream Ref | Yes | 上游規格鏈 |

---

## 三、同步流程

1. 建立同步批次
2. 驗證 artifact 狀態與必要欄位
3. 產生 payload 與 idempotency key
4. 呼叫 Codebeamer API
5. 記錄結果到 integration log

---

## 四、錯誤處理

- 單筆失敗不得中止整批結果記錄。
- 支援 retry with backoff。
- partial failure 必須保留成功與失敗明細。
- API 成功但回寫失敗時，需標記為 reconciliation required。
