## Context

Repo 現有成果是日期固定的研究與文件骨架。RSS 的 GUID 和 enclosure 可支援單集識別與下載；同一 podcaster 可能有多個節目。使用者指定將本機內容放在 content，Drive 根目錄為 1gae0A1FcXlkWdGZeFrE4SEs6X-cMXlmj，已經 metadata 查核為共用雲端硬碟內的 Podcast 資料夾。

## Goals / Non-Goals

**Goals:** CLI 可先預覽、限量下載、斷線後重跑、核對本機檔案，並按 podcaster／節目上傳到指定 Drive 目錄。來源、下載與上傳紀錄可由 manifest 追溯。

**Non-Goals:** 付費內容或 DRM、音訊轉錄／轉碼、排程、模型訓練、遠端刪除／同步覆蓋、跨機器同時上傳的分散式鎖。此次實測以豬探長一集為範圍，不自動下載全榜或全系列。

## Decisions

### Python CLI 與 RSS 設定

採 Python 3.11+ 標準函式庫，減少安裝成本。入口為 python -m storysonic；podcasts.toml 指定 show ID、顯示名、podcaster ID／顯示名及 RSS。前十名配置取自既有研究而非宣稱即時排名。RSS 僅接受 HTTP(S)、限制 20 MiB、拒絕 DTD／entity；GUID 缺失時以 enclosure URL 作為來源鍵。來源 GUID 先去重，以日期新到舊排序後套用標題子字串及數量。缺日期排最後。預設最多 3 集，--all 明確表示全部，--limit 與 --all 互斥，零或負值拒絕。

### 原子下載與 manifest

本機路徑採 content／podcaster ID／show ID／episode key.mp3 與同名 .json；episode key 是 show ID 加 GUID 的 SHA-256 前 24 字元。ID 限小寫 ASCII、數字與連字號；標題不進本機檔案路徑。只接受 MP3 enclosure。串流下載至 .part，預設單集上限 256 MiB，HTTP timeout 30 秒，最多三次 GET 嘗試，失敗時清除暫存而不寫成功 manifest。已知 Content-Length 必須與實際一致；RSS enclosure length 僅記錄不強制，因為公開 feed 經常寫 0。拒絕 HTML／非音訊回應並檢查 MP3 ID3／frame 標頭。完成後原子 rename，再寫 schema_version=1 manifest。重跑核對實際大小與 SHA-256；完整則跳過，損壞則重新下載。單集失敗不阻止其他已選單集，整批最後回傳非零。content 根目錄以檔案鎖避免本機並行寫入。

### gws 上傳與遠端核對

使用 gws drive files 的 JSON 介面，不自行讀取 token 或將憑證存 repo。相比 rclone，gws 已安裝且可直接以 Drive ID 處理共用雲端硬碟；目前本機登入需更新，connector 可讀目的地。呼叫 subprocess 使用參數陣列、不經 shell。根目錄先核對 MIME type、canAddChildren 與 driveId；所有操作帶 supportsAllDrives，查詢分頁且限定父目錄及非垃圾桶項目。分類名稱為「顯示名 [穩定 ID]」。同名資料夾多筆時停止，不擅自選擇。

音檔的 appProperties 存 storysonic_episode 與 storysonic_sha256。相同 episode key 的檔案存在時，讀回 size 與 md5Checksum 核對；一致则 skipped，不一致或多筆则 conflict，不覆寫或刪除。新檔用 gws --upload，完成後 files.get 讀回並核對 MD5／大小，才將 Drive ID、根目錄、URL 和 verified_at 寫入本機 manifest。上傳逾時不自動重送 create；使用者重跑先查遠端，可復原「遠端成功但本機未記錄」的狀態。單次 gws 呼叫 timeout 300 秒。權限、認證、容量與 checksum 錯誤保持可診斷，未知狀態不記成成功。

## Implementation Contract

In scope：list、download、upload 三個命令，--show 選配置節目，--match 篩選標題，--limit／--all、--dry-run。download 只有加 --upload 才執行上傳；upload 僅處理已下載且通過本機雜湊的 manifest。--drive-folder 可覆寫設定根目錄，接受 Google Drive folder URL 或原始 ID。--config、--content-dir 可指定設定／儲存位置。無符合單集、未知 show、無效 manifest 或目的地回傳非零且有說明。dry-run 只列計畫，不寫 content、不呼叫 Drive。

Manifest 包含 schema_version、episode_key、show_id／show_name、podcaster_id／podcaster_name、feed_url、guid、title、published、enclosure_url、declared_bytes、downloaded_at、bytes、sha256、md5、local_file（僅檔名）與 uploads（依根目錄 ID 索引）。manifest 為本機資料，不上傳憑證或 metadata 工作集。上傳前檢查 local_file 不越界、不是 symlink，依 manifest show／podcaster ID 確認分類。

驗收：unittest 以受控 HTTP 回應與 fake gws process 驗證排序／去重、路徑隔離、網路中斷不留成功檔、內容長度與 hash、重跑、Drive 分頁／共用硬碟／衝突與讀回核對；CLI subprocess 檢查 dry-run、非法旗標与非零錯誤。真實豬探長單集完整下載、ffmpeg 解碼、重跑 skipped；若本機認證可用，執行同一 CLI 的真實 Drive 上傳與第二次 skipped，否則明確記錄未驗證步驟，不以 mock 或 connector 成功替代 CLI 實測。

## Risks / Trade-offs

- [RSS 內容與音檔動態變更] → 同一 GUID 的已完成本機版本保留；手動移走檔案與 manifest 後才能重新取得不同版本。
- [gws 介面仍在演進、multipart 需記憶體] → 記錄已測版本、限制單集大小；本版失敗後從整檔重試，不宣稱 byte-range resume 或 resumable upload。
- [兩台機器同時 create 仍可能競態] → 本版限定單一 writer；重跑若發現重複遠端 ID 直接報 conflict。
- [共用硬碟權限依帳號而異] → 實際 canAddChildren 與 API 錯誤為準，不變更分享或成員。
- [音檔可下載不代表其他用途已授權] → 本工具只整理來源與自用研究工作集，授權狀態留待資料集研究。

## Sources

- https://podcasters.apple.com/support/823-podcast-requirements
- https://github.com/googleworkspace/cli
- https://developers.google.com/workspace/drive/api/guides/manage-uploads
- https://developers.google.com/workspace/drive/api/guides/search-files
