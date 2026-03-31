# SpecOps 評估與 KPI 規格 (Evaluation KPI)

> 版本: v1.0  
> 角色: 定義可驗證的品質、成本與營運指標

---

## 一、品質指標

- **Requirement Extraction Precision**
- **Requirement Extraction Recall**
- **Constraint Fidelity Score**
- **Testability Pass Rate**
- **Cross-section Conflict Precision**
- **Signal-Sync Exact Match Rate**
- **Auto-Fix Approval Rate**
- **Safety/Security False Negative Rate**

---

## 二、營運指標

- **Median Review Cycle Time**
- **Manual Recovery Queue Size**
- **Lock Contention Rate**
- **Edge Request Timeout Rate**
- **Per Section Token Cost**
- **Per Stage Latency**

---

## 三、最低門檻建議

- Requirement extraction recall >= 0.90
- Requirement extraction precision >= 0.85
- Auto-fix approval rate >= 0.70
- Safety/security false negative rate <= 0.02
- Edge request timeout rate <= 0.05

---

## 四、回歸檢查觸發條件

以下變更必須重新跑 Golden Test Suite：

- Prompt 版本更新
- 模型切換
- schema 變更
- parser 規則變更
- signal-sync 規則變更
