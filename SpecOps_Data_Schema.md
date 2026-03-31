# SpecOps 資料結構規格 (Data Schema)

> 版本: v1.0  
> 角色: 定義核心 JSON 物件最小欄位與一致性要求

---

## 一、共通欄位

所有核心物件至少包含：

```json
{
  "id": "string",
  "schema_version": "1.0.0",
  "created_at": "2026-03-31T00:00:00Z",
  "updated_at": "2026-03-31T00:00:00Z",
  "status": "DRAFT",
  "version": "v1.0"
}
```

---

## 二、requirement

```json
{
  "id": "R-oemx-cluster-v1_0-sec_001-001",
  "artifact_type": "requirement",
  "title": "Vehicle speed shall be displayed in km/h.",
  "statement": "The system shall display vehicle speed in km/h when market profile is metric.",
  "source_spec_ids": ["S-oemx-cluster-v1_0-sec_001"],
  "source_note_ids": ["N-oemx-cluster-v1_0-sec_001-001"],
  "compliance": {
    "classes": ["FSR"],
    "asil": "B",
    "cal": null
  },
  "trace": {
    "downstream_test_requirement_ids": ["T-R-oemx-cluster-v1_0-sec_001-001-001"],
    "graph_node_id": "R-oemx-cluster-v1_0-sec_001-001"
  },
  "audit_rationale_id": "AR-R-oemx-cluster-v1_0-sec_001-001-001",
  "variant_scope": "base"
}
```

---

## 三、test_requirement

```json
{
  "id": "T-R-oemx-cluster-v1_0-sec_001-001-001",
  "artifact_type": "test_requirement",
  "statement": "Verify speed is shown in km/h under metric market profile.",
  "source_requirement_ids": ["R-oemx-cluster-v1_0-sec_001-001"],
  "acceptance_criteria": [
    "Display unit is km/h",
    "Displayed value matches input signal tolerance"
  ],
  "audit_rationale_id": "AR-T-R-oemx-cluster-v1_0-sec_001-001-001-001"
}
```

---

## 四、graph_edge

```json
{
  "id": "E-R1-DEPENDS_ON-R2",
  "artifact_type": "graph_edge",
  "source_id": "R1",
  "target_id": "R2",
  "edge_type": "DEPENDS_ON",
  "status": "APPROVED",
  "created_by": "user_a"
}
```

---

## 五、review_record

```json
{
  "id": "RV-R1-001",
  "artifact_id": "R1",
  "decision": "REJECTED",
  "reviewer_id": "reviewer_a",
  "rejection_tags": ["missing_constraint", "unclear_unit"],
  "review_note": "Need explicit unit and trigger condition."
}
```

---

## 六、audit_rationale

```json
{
  "id": "AR-R1-001",
  "artifact_id": "R1",
  "source_refs": [
    {
      "spec_id": "S1",
      "page": 12,
      "bbox": [100, 200, 400, 260]
    }
  ],
  "prompt_version": "prompt-v4.6",
  "model_version": "model-x",
  "silver_refs": ["SD-001"]
}
```

---

## 七、silver_dataset_entry

```json
{
  "id": "SD-001",
  "artifact_id": "R1",
  "lifecycle_state": "active",
  "visibility": "BRAND",
  "brand_id": "OEM_X",
  "project_id": "Cluster_A",
  "allowed_use_cases": ["requirement_generation", "test_requirement_generation"],
  "expiry_date": "2029-03-31"
}
```

---

## 八、一致性要求

- 所有 reference id 必須可被 trace map 解析。
- `APPROVED` artifact 必須具備 `audit_rationale_id`。
- safety/security 類 requirement 必須顯式標示 `asil` 或 `cal`，若不適用則填 `null` 並附原因。

---

## 九、MVP Relational Persistence Mapping

本文件定義的是 artifact / API 層 JSON schema，但目前 MVP backend 已同步落地一套 SQLite relational persistence baseline。兩者關係如下：

- JSON schema 是對外契約與模型真相。
- SQLite schema 是當前 MVP 的持久化形態，不可反向覆蓋 JSON 契約。
- 若兩者衝突，以 API / Pydantic model 為準，再回寫 persistence mapping。

### 1. 主表對應

`spec_section`
- table: `spec_sections`
- 顯式欄位:
  - `id`
  - `artifact_type`
  - `schema_version`
  - `status`
  - `version`
  - `section_key`
  - `title`
  - `text`
  - `normalized_text`
  - `created_at`
  - `updated_at`
- JSON 欄位:
  - `parser_warnings_json`
  - `source_refs_json`

`note`
- table: `notes`
- 顯式欄位:
  - `id`
  - `artifact_type`
  - `schema_version`
  - `status`
  - `version`
  - `title`
  - `summary`
  - `created_at`
  - `updated_at`
- 關聯表:
  - `note_source_specs`

`requirement`
- table: `requirements`
- 顯式欄位:
  - `id`
  - `artifact_type`
  - `schema_version`
  - `status`
  - `version`
  - `title`
  - `statement`
  - `asil`
  - `cal`
  - `graph_node_id`
  - `variant_scope`
  - `audit_rationale_id`
  - `created_at`
  - `updated_at`
- JSON 欄位:
  - `classes_json`
- 關聯表:
  - `requirement_source_specs`
  - `requirement_source_notes`

`test_requirement`
- table: `test_requirements`
- 顯式欄位:
  - `id`
  - `artifact_type`
  - `schema_version`
  - `status`
  - `version`
  - `statement`
  - `audit_rationale_id`
  - `created_at`
  - `updated_at`
- JSON 欄位:
  - `acceptance_criteria_json`
- 關聯表:
  - `test_requirement_sources`

`audit_rationale`
- table: `audit_rationales`
- 顯式欄位:
  - `id`
  - `artifact_id`
  - `prompt_version`
  - `model_version`
  - `created_at`
- JSON 欄位:
  - `source_refs_json`
  - `silver_refs_json`

`review_record`
- table: `reviews`
- 顯式欄位:
  - `id`
  - `artifact_id`
  - `decision`
  - `reviewer_id`
  - `review_note`
  - `reviewed_at`
- JSON 欄位:
  - `rejection_tags_json`

### 2. Trace 與 Link Tables

`trace_entry`
- table: `trace_entries`
- 顯式欄位:
  - `artifact_id`
  - `artifact_type`
  - `status`
  - `version`
  - `schema_version`
  - `last_review_id`
  - `audit_rationale_id`
- `upstream_ids` / `downstream_ids` 不直接持久化為欄位，而是在讀取時由 link tables 推導。

ordered link tables:
- `note_source_specs(note_id, spec_id, position)`
- `requirement_source_specs(requirement_id, spec_id, position)`
- `requirement_source_notes(requirement_id, note_id, position)`
- `test_requirement_sources(test_requirement_id, requirement_id, position)`

### 3. 約束基線

- SQLite 連線啟動時必須開啟 `PRAGMA foreign_keys = ON`。
- ordered link tables 目前有 foreign key 約束。
- 這些 link tables 使用 `ON DELETE CASCADE`。
- polymorphic 關聯目前仍由應用層保證，例如 `audit_rationale.artifact_id`。
- parent row 更新不得使用 `INSERT OR REPLACE`，必須使用 `ON CONFLICT DO UPDATE` 類型的 upsert。

### 4. Cleanup 與保留行為

- 刪除 parent artifact 時，相關 link rows 應自動清除。
- 這不代表所有 downstream artifact entity 都會跟著刪除。
- 目前例如刪除 `requirement` 時，`test_requirement_sources` 會被清除，但 `test_requirements` 本體可保留為未連結資料。
- 這是目前 MVP persistence behavior，不代表最終產品 lifecycle policy。
