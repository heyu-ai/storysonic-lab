# 架構決策紀錄（ADR）

記錄會影響多個功能、長期資料格式或技術方向的決策，例如音檔與逐字稿儲存方式、ASR 選型、故事標記 schema、聲音分析方法及評估策略。

## 建立方式

1. 先查本目錄及進行中的 PR，確認是否已有相同決策或預留編號。
2. 從 [template.md](template.md) 複製成 `NNNN-kebab-name.md`，使用四位遞增編號。
3. 引用相關研究、OpenSpec change 或穩定規格，記錄替代方案與代價。
4. 草稿使用 `status: proposed`、`deciders: []`；確認實際裁決者與結論後才改為 `accepted`。
5. 更新下方索引。若被取代，保留原檔並設為 `superseded-by-NNNN`，連到後繼 ADR。

ADR 與 OpenSpec change 使用獨立命名，不以 ADR 編號推導 change 名稱。尚未確認的技術選型維持 proposed，不因研究報告推薦就自動接受。

## 索引

目前尚無正式 ADR；已提供範本。文件目錄配置直接依專案初始化需求建立，未代為決定程式架構、模型或資料儲存技術。

| ID | 決策 | 狀態 | 關聯 |
|---|---|---|---|
