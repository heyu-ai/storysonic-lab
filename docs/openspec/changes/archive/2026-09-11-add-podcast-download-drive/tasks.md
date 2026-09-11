## 1. 目錄與下載

- [x] 1.1 實作 Python CLI 與 RSS 設定，交付 Select podcast episodes 的排序、GUID 去重、標題／數量選取，先以 tests/test_catalog.py 驗證日期、空值與無效 feed。
- [x] 1.2 實作原子下載與 manifest，交付 Download complete MP3 files 及 Preserve download provenance and idempotency；以 tests/test_download.py 驗證中斷、大小、非音訊、重跑、路徑越界與鎖。
- [x] 1.3 交付 Preview and exclude local media from Git 的 CLI 與 content 忽略規則；以 tests/test_cli.py、dry-run 和 git check-ignore 驗證不寫入與 MP3 不受追蹤。

## 2. Drive 整合

- [x] 2.1 實作 gws 上傳與遠端核對，交付 Route uploads by podcaster、Verify uploads and avoid duplicates 及 Explicit upload and observable failures；以 tests/test_drive.py 驗證共用硬碟、分頁、衝突、重跑與認證錯誤。
- [x] 2.2 將 download --upload 與獨立 upload 串接 CLI，更新 README 與專案 context；以 tests/test_cli.py 和 help 驗證設定覆寫、未知 manifest 与非零狀態。

## 3. 驗證與研究紀錄

- [x] 3.1 完成豬探長一集真實下載、解碼、重跑與 Git 排除驗證；執行完整 unittest，將結果和 Drive CLI 的已驗證／未驗證範圍記錄於研究文件並驗證 Spectra artifacts。

- [x] 3.2 使用者完成 gws 重新登入後，真實執行豬探長單集 upload，確認遠端分類、MD5／大小與 manifest ID；第二次 upload 回報 upload_skipped=1 且沒有新增重複檔案。已核對：相同 file ID、upload_skipped=1、遠端單集數為 1；驗證時間 2026-09-11T12:26:38Z。
