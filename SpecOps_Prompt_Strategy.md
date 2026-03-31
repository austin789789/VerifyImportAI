# SpecOps AI 策略 (Prompt Strategy)

> 版本: v4.2  
> 角色: AI 角色定義、CoT 與 安全脫敏

---

## 一、階段性角色定義 (Role-based Strategy)

### 4. Stage 4 (修正者 - Corrector)
- **定位**: 規格精修專家。
- **專注**: 根據人工退回的 `rejection_tags` 與 `human_opinion` 進行精準修正。

---

## 四、自動修正策略 (Self-Fix Loop)

為了減輕人工二次審查的負擔，系統針對退回項目執行自動化修正。

### 1. 修正邏輯
- **Input**: 原始需求 + 規格原文 + `rejection_tags` + `human_opinion`。
- **Action**: LLM 專注於修正標籤指出的錯誤，不應更動已獲得正面回饋的部分。
- **Output**: 狀態變更為 `FIXED`，並附帶修正說明。

---

## 五、大規模規格處理策略 (Large-Scale Spec Handling)
...

---

## 六、幻覺偵測與質量護欄 (Hallucination Guardrails)

1. **數據校驗 (Data Cross-Check)**.
2. **品質預警連動**: 當某區塊頻繁觸發 `REJECTED` 時，Stage 4 角色自動提升生成時的溫度 (Temperature) 或調用更強大的模型進行推理。
