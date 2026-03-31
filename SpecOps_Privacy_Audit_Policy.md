# SpecOps 隱私與稽核政策 (Privacy Audit Policy)

> 版本: v1.0  
> 角色: 定義脫敏、保存、可見性與稽核留存政策

---

## 一、資料分類

- **GLOBAL**: 通用知識，可跨專案使用。
- **BRAND**: 限特定 OEM / brand。
- **PROJECT**: 限單一專案，禁止跨專案注入。

---

## 二、脫敏原則

1. 先以規則型遮罩處理識別碼、專案代號、客戶名稱等高敏感資訊。
2. 再以語義型 scrubber 補強上下文敏感內容。
3. 未通過脫敏檢查的內容不得送往雲端模型。

---

## 三、審計留存原則

- 保留 prompt version、model version、review record、fix rationale、integration log。
- 原始輸入輸出若含高敏感資訊，需保存遮罩版或保存於受限區域。
- 稽核資料必須可回溯到 artifact 與時間點，但不代表所有人都能查看原文。

---

## 四、存取控制

- Editor 僅能看見其有權限的 project / brand 範圍。
- Reviewer 可查看審查所需依據，但不得跨 visibility 越權瀏覽。
- Architect / Admin 可執行受控稽核查閱。

---

## 五、Silver Dataset 注入限制

- `PROJECT` 條目禁止跨專案注入。
- `BRAND` 條目禁止跨品牌注入。
- 注入流程必須記錄使用了哪些 Silver entry。
