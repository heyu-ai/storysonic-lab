## 1. 來源與批次

- [x] 1.1 完成 Collect M4A enclosures；以 M4A header、錯誤 MIME、舊 MP3 manifest 與下載重跑測試驗證。
- [x] 1.2 完成 Run observable resumable batches；以 all-shows、單一來源失敗、dry-run 無寫入、空間不足與停止測試驗證。

## 2. 轉錄與衍生物

- [x] 2.1 完成 Generate traceable transcripts；測試兩個 backend adapter、繁體/raw text、非法時間碼與 JSON/SRT/TXT 契約。
- [x] 2.2 完成 Resume portable derived artifacts 與 Convert without replacing source audio；測試搬移後 skip、損壞重建、decoder 失敗無完成狀態。
- [x] 2.3 完成 Upload verified transcript companions；測試重跑 skip、remote MD5 衝突與缺少逐字稿錯誤。

## 3. 部署與交付

- [x] 3.1 完成 Deploy on Apple Silicon and Docker；驗證安裝 CLI、Mac 腳本、Compose、image 建置與基本指令，source archive 無素材或憑證。
- [x] 3.2 執行原生一集轉錄/轉檔與搬移續跑驗證，記錄測試結果、Docker 限制及未執行的全量工作。
- [x] 3.3 更新 README、部署文件與規格狀態；執行完整 unittest、文件連結、git diff --check 與 Spectra 驗證。
