# Podcast 下載器與 Drive 整合驗證

查核日期：2026-09-11（Asia/Taipei）。實作規劃見 [add-podcast-download-drive](../openspec/changes/archive/2026-09-11-add-podcast-download-drive/proposal.md)，操作方式見 [README](../../README.md)。

## 已驗證

- Python 3.13.3 執行 26 個 unittest，全部通過。測試涵蓋 RSS 日期排序／GUID 去重、標題及數量篩選、XML 宣告拒絕、下載中斷、固定／未知 Content-Length 大小限制、重跑與損壞檔修復、manifest 路徑與 symlink、並行寫入鎖、CLI dry-run／非零錯誤、Drive 分類／分頁／重複與衝突，以及 download --upload 與獨立 upload 的串接。
- Live RSS 列出並選取豬探長 EP.131「袖珍娃娃屋奇案(上集)」。dry-run 只列計畫，正式下載成功，第二次相同指令回報 downloaded=0、skipped=1、failed=0。
- 以 ffmpeg 完整解碼 MP3，exit 0。ffprobe 顯示 mp3、44,100 Hz、雙聲道，長度 1,248.6878 秒。
- Git 忽略實際 MP3 與 manifest；repo 其他路徑的大小寫 MP3 副檔名也被忽略。content 只有 README 屬於可提交檔案。
- 透過 Drive connector 讀取指定根目錄：名稱 Podcast，MIME type 為資料夾，位於共用雲端硬碟。本機 gws 重新登入後亦已完成下述真實上傳與讀回驗證。
- 本機 gws 0.8.0 的 drive.files.create discovery schema 可讀，支援 supportsAllDrives。Drive adapter 已完成真實 Google API 寫入與重跑驗證，見下節。

## 下載樣本

| 欄位 | 值 |
|---|---|
| 節目 | 豬探長推理故事集 |
| Podcaster | 如果兒童劇團（ifkids） |
| 標題 | EP.131 袖珍娃娃屋奇案(上集) |
| GUID | cms6gbyon1f1m01y1el807zgw |
| Episode key | a51cbc0a214e605a6ad33361 |
| 檔案大小 | 19,980,254 bytes |
| SHA-256 | 620456c005f5fff94df6d6e8083d1cfe87c5a059ead49b2f25c920aa91ef8108 |
| MD5（傳輸核對） | 515cbee3b5af7616e46d6d2ae87ccaa4 |
| 下載時間 | 2026-09-11T10:42:54.508709+00:00 |
| 本機路徑（相對 repo） | content/ifkids/detective-pig/a51cbc0a214e605a6ad33361.mp3 |

音檔與完整 manifest 只在本機，不包含於 Git commit。本文件保存驗證摘要，未重新分析故事品質、語音風格或轉錄內容。

## Drive CLI 真實上傳與重跑驗證

先前測試遇到 gws invalid_grant，CLI 正確回傳 exit 1 並保留本機音檔。使用者重新登入後，於 2026-09-11T12:25:28.037550+00:00 完成真實上傳：uploaded=1、upload_skipped=0、failed=0。

Agent 隨後重跑同一單集上傳，於 2026-09-11T12:26:38.004315+00:00 回報 uploaded=0、upload_skipped=1、failed=0，沿用相同 file ID。另以 gws 讀回音檔、父資料夾、podcaster 資料夾，以及節目資料夾清單，確認：

| 核對項目 | 結果 |
|---|---|
| 根目錄 | Podcast（1gae0A1FcXlkWdGZeFrE4SEs6X-cMXlmj） |
| Podcaster | 如果兒童劇團 [ifkids]（1OwcJlbf5UTEWhc51CSM__lUKYRbj3S8-） |
| 節目 | 豬探長推理故事集 [detective-pig]（18qGghL2x5jCJIrJJpfhKuTlWp-sUjDwi） |
| 音檔 | [EP.131 袖珍娃娃屋奇案(上集)](https://drive.google.com/file/d/154lMggvln27lWAy6Kg8OHtc_ON6cvVuP/view?usp=drivesdk) |
| 檔案大小 | 19,980,254 bytes，與本機一致 |
| MD5 | 515cbee3b5af7616e46d6d2ae87ccaa4，與本機一致 |
| 重複檢查 | 同一 episode key 僅 1 筆；節目資料夾共 1 個檔案 |
| 本機 manifest | uploads 中的 file ID 與遠端一致，已保存 verified_at |

重現指令：

```bash
python3 -m storysonic upload --show detective-pig --match "EP.131 " --limit 1
```

本次真實驗證涵蓋一集 MP3 的完整下載、分類上傳、metadata 讀回與重跑去重。全榜／全系列批次上傳、遠端衝突、網路故障等其他情境仍依自動測試覆蓋，未宣稱已完成全部真實環境測試。

## Spectra 歸檔核對

7/7 任務完成後，Spectra 已將變更歸檔為 2026-09-11-add-podcast-download-drive，並同步 podcast-download 與 podcast-drive-upload 共 7 個 requirements。逐項比較歸檔 delta 與穩定規格，排除 CLI 產生的 trace 註解與分隔線後內容一致，每個 requirement 均保留規範用語與 scenario；55 個本機文件連結有效。

本機 Spectra 2.3.1 在歸檔後執行 validate --specs --all --strict --json 回傳空陣列，而指定 capability 名稱會回報 Change not found；因此不將這個空結果當成兩份穩定規格已被 CLI 嚴格驗證的證據。歸檔前的 change 驗證已通過，歸檔後另外做上述內容一致性核對。

## 限制與來源

本版使用整檔下載重試與 gws multipart 上傳，尚無 byte-range 續傳、resumable upload 或跨電腦的分散式鎖。預設一次 3 集、單集上限 256 MiB；大量處理需由使用者明確選擇 --all。Gws 是外部工具，版本更新後應重跑整合驗證。

- [Apple RSS requirements](https://podcasters.apple.com/support/823-podcast-requirements)：GUID 與 enclosure 的來源契約。
- [Google Workspace CLI](https://github.com/googleworkspace/cli)：認證及 JSON／media upload 介面。
- [Drive upload guide](https://developers.google.com/workspace/drive/api/guides/manage-uploads)：上傳模式與檔案建立。
- [Drive search guide](https://developers.google.com/workspace/drive/api/guides/search-files)：父目錄、appProperties 與查詢語法。
