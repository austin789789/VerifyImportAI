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
