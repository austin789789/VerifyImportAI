# SpecOps 狀態機規格 (State Machine)

> 版本: v1.0  
> 角色: 定義 artifact 正式狀態、轉移規則與責任邊界

---

## 一、適用範圍

本文件適用於 `note`, `requirement`, `test_requirement`, `signal_mapping` 等需經審查治理的 artifact。

---

## 二、正式狀態

- `DRAFT`
- `IN_REVIEW`
- `APPROVED`
- `REJECTED`
- `AUTO_FIX_IN_PROGRESS`
- `AUTO_FIXED_PENDING_REVIEW`
- `IMPACTED`
- `MANUAL_RECOVERY`
- `ARCHIVED`

---

## 三、轉移表

| From | To | Trigger | Actor | Required Metadata |
|---|---|---|---|---|
| DRAFT | IN_REVIEW | submit_review | Editor | reviewer_id |
| IN_REVIEW | APPROVED | approve | Reviewer | review_id, approval_note |
| IN_REVIEW | REJECTED | reject | Reviewer | rejection_tags, rejection_note |
| REJECTED | AUTO_FIX_IN_PROGRESS | start_auto_fix | System | fix_job_id |
| REJECTED | DRAFT | manual_edit_restart | Editor | editor_id |
| AUTO_FIX_IN_PROGRESS | AUTO_FIXED_PENDING_REVIEW | auto_fix_success | System | fix_rationale, diff_ref, confidence |
| AUTO_FIX_IN_PROGRESS | MANUAL_RECOVERY | auto_fix_failed_or_low_confidence | System | failure_reason, confidence |
| APPROVED | IMPACTED | upstream_change_detected | System | impact_job_id, impact_reason |
| IMPACTED | AUTO_FIX_IN_PROGRESS | eligible_auto_fix | System | fix_job_id |
| IMPACTED | IN_REVIEW | manual_recheck | Reviewer | review_id |
| MANUAL_RECOVERY | DRAFT | manual_rework | Editor | owner_id |
| APPROVED | ARCHIVED | retire | Architect/Admin | archive_reason |

---

## 四、轉移限制

- `APPROVED` 不可被背景工作直接覆寫為其他內容，只能先轉 `IMPACTED`。
- `AUTO_FIXED_PENDING_REVIEW` 必須人工確認後才能回到 `APPROVED`。
- safety/security 類 artifact 不允許跳過 `IN_REVIEW`。

---

## 五、附帶動作

- 進入 `APPROVED` 時，建立或更新 traceability links 與 audit record。
- 進入 `REJECTED` 時，必填結構化標籤。
- 進入 `MANUAL_RECOVERY` 時，必須指派 owner、severity、due date。
