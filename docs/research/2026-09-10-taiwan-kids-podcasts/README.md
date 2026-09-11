# 台灣兒童故事 Podcast 與豬探長資料取得研究

- **資料查核**：2026-09-10 23:43（Asia/Taipei）。
- **HTML 分享版**：2026-09-11。
- **收錄狀態**：既有研究快照；此次 repo 初始化未重新查榜或下載音檔。

## 閱讀入口

- [研究報告](report.md)：排名、取得方式、豬探長規模、驗證方法與限制。
- [可分享 HTML](taiwan-kids-podcast-research.html)：下載後以瀏覽器開啟。內嵌三份 CSV，可離線閱讀、搜尋故事與匯出資料；外部來源連結需要網路。

## 資料與證據

| 檔案 | 內容 |
|---|---|
| [top10.csv](top10.csv) | 前十名節目、製作人、Apple ID、RSS 與條目數 |
| [all-episodes.csv](all-episodes.csv) | 2,684 個公開 RSS 條目及音訊連結 |
| [pig-stories.csv](pig-stories.csv) | 豬探長 67 個故事題名與上下集配對 |
| [episodes-1559480667.csv](episodes-1559480667.csv) | 豬探長 144 個故事／特別節目條目 |
| [apple-chart-raw.json](apple-chart-raw.json) | 查核當時 Apple 排行榜原始回應 |
| [probe-results.json](probe-results.json) | RSS 數量與 HTTP HEAD 查核紀錄 |
| [sample-download.json](sample-download.json) | EP.131 完整下載、SHA-256 與解碼驗證摘要 |

## 已知限制

- 條目包含預告、試聽與特別節目，不等於 2,684 個完整故事。
- 10 個音檔連結的 HEAD 抽查成功，不代表全部音檔已完整下載。
- 豬探長 EP.131 的完整 MP3 在原研究工作區通過下載與解碼；本目錄收錄其驗證摘要，**不包含音檔本體**。驗證摘要中的作者本機路徑已移除。
- 尚未完成全系列轉錄、故事結構或聲音品質評分，也未驗證付費逐字稿匯出。
- 報告全文的「本次交付檔案」保留原研究紀錄，包含當時工作區的 XML、程式等項目；本 repo 實際收錄清單以上表為準。
- HTML 內嵌資料是本次快照；未來新增研究應保留查核版本，避免只更新外部 CSV 而讓 HTML 與報告不同步。
