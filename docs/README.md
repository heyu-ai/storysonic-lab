# 文件導覽

StorySonic Lab 的文件以研究、決策與規格分工。這個結構參考 yibi-mvp，內容與工作流程則以本專案需求為準。

| 目錄 | 回答的問題 | 內容與更新時機 |
|---|---|---|
| [research/](research/README.md) | 我們觀察到什麼？證據與限制是什麼？ | Podcast 調查、下載／轉錄實驗、故事與聲音分析、模型評估、研究成果 |
| [adr/](adr/README.md) | 為什麼選這個方案？誰做了決定？ | 跨功能的重要取捨、被考慮的替代方案、代價與未決問題 |
| [openspec/](openspec/README.md) | 系統應該具備什麼行為？這次要改什麼？ | 穩定規格、變更提案、驗收情境、實作任務與歸檔歷史 |

## 文件如何銜接

1. 研究先留下來源、方法、觀察與不確定性。
2. 若研究導向架構或長期選型決定，建立 ADR，引用研究證據。
3. 需要落地的功能透過 Spectra change 定義行為、資料契約、驗收方式與任務。
4. 完成實作與驗證後，由 archive 將差異合併到穩定規格。

單一功能的實作細節可以留在 change 的 `design.md`；不必為每個小改動建立 ADR。

## 維護約定

- 人類閱讀的內容使用繁體中文台灣用語；檔名、slug、識別符及工具要求的欄位保持英文。
- 機器解析的 OpenSpec 標頭與關鍵字保留原樣，例如 `Requirement`、`Scenario`、`SHALL`、`WHEN`、`THEN`。
- 新增或調整文件時，同步更新該區 README 與相對連結。
- 研究快照保留原查核日期；後續新資料以新版本或補充紀錄呈現，不把舊結果寫成即時事實。
- 已接受的 ADR 若被取代，保留歷史並連到後繼決策。

## 目前入口

- [首份研究：台灣兒童故事 Podcast 與豬探長](research/2026-09-10-taiwan-kids-podcasts/README.md)
- [ADR 範本](adr/template.md)
- [Spectra 工作流程](openspec/README.md)

- [部署與搬機](deployment/README.md)：Apple Silicon 原生 MLX、Docker CPU、content 續跑與 Google Drive。
