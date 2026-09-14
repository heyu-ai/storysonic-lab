# 可攜部署與轉錄驗證（2026-09-11）

## 結果與範圍

使用者將全榜公開單集下載/逐字稿工作改為部署到另一台 Apple Silicon Mac。原生 MLX 與 Docker CPU 版本均已實作並做樣本驗證；**沒有在本機完成全榜下載或轉錄**。原生主要平台為 Apple M4 Pro、24 GiB、Python 3.13.3；Docker 實測 Linux arm64 / Python 3.13。Dockerfile 同時列出 amd64 的 gws 安裝校驗碼，但此回合未實測 amd64。

## 已執行

| 驗證 | 結果 |
|---|---|
| 原生安裝腳本 | `bash scripts/setup-mac.sh` exit 0，以 uv.lock 安裝並列出 10 個節目 |
| 自動測試 | 42 個 unittest 通過，含 M4A、舊 manifest、故障隔離、SIGTERM、搬移、輸出雜湊與 Drive companions |
| Docker | `docker compose config --quiet`、映像建置、list 及 gws 0.8.0 均成功 |
| Linux 批次回歸 | 容器內 `test_portable.py` 的 5 個測試通過 |
| 完整逐字稿 | 豬探長 EP.134 急凍剋星的極光之旅（下集），1,154.742857 秒；MLX large-v3-turbo / zh / traditional，503 段、4,477 個 TXT 字元 |
| 續跑 | 同路徑及複製到另一個 content 根目錄後均 transcript_skipped；測試也斷言 engine 不被呼叫 |
| WAV | 同一集成功解碼成 pcm_s16le、16,000 Hz、單聲道；來源 MP3 保留 |
| M4A | 從前從前「不要想東想西，專心聽！」真實下載 10,835,989 bytes，另存 WAV 成功 |
| Docker ASR | 取 EP131 前 30 秒，另建明確標記 validation/excerpt 的 manifest；faster-whisper tiny / CPU 成功產生三種逐字稿 |
| Drive | EP134 音檔已存在；TXT/SRT/JSON 各上傳一份，readback 大小/MD5 一致；重跑三份均 skipped、ID 不變 |

TXT 字數不是辨識正確率。全文尚未人工校訂，`reviewed=false`；自動轉繁體不會修正角色名、台語、多人重疊等識別錯誤。CPU 樣本用 tiny 縮短驗證時間，不等同 small 預設模型或 large-v3 的品質與速度評估。

真實 Drive 逐字稿範例：[TXT](https://drive.google.com/file/d/1eJFFiHdy2LE6bcIWhbd9Oj5buXNR1d2z/view)、[SRT](https://drive.google.com/file/d/1KJK7HSBm6WJxJLa1MGGYQz1V5Mom2_WP/view)、[JSON](https://drive.google.com/file/d/1pdLMkaQX4D6GwIAPeAzOdk8X1847ecHN/view)。分享權限未改動。逐字稿資料夾為 `1iRlk-tGU9nRvIbTvlwSldCqPqbbWJbI_`。

## 停止與保存狀態

先前由本任務啟動的 `download --show detective-pig --all --upload` 已送 SIGINT 停止並確認鎖釋放；停止時保留 67 份來源音檔 manifest、66 份已核對的 Drive 上傳紀錄，無 `.part` 殘留。中斷時尚未記錄的 Drive 結果可由下次 upload 查詢補核對，不能直接推定不存在。

後續只進行以上有界驗證，未啟動全部 2,687 集的工作，沒有建立自動監控或排程。現有本機素材保持在 content，不包含於可搬移程式包。

## Feed 格式覆蓋

重新解析 2026-09-11 已保存的公開 RSS XML，使用本版 parser，得到以下數量。此處不更改 2026-09-10 研究的歷史 CSV；當前 RSS 與歷史快照可以不同。

| show ID | MP3 + M4A | M4A |
|---|---:|---:|
| detective-pig | 145 | 0 |
| once-upon-a-time | 357 | 2 |
| english-stories | 229 | 0 |
| otter-mom | 371 | 43 |
| story-together | 202 | 0 |
| story-steam | 81 | 0 |
| jiajia-stories | 169 | 0 |
| mom-dad-stories | 393 | 0 |
| our-bedtime-stories | 405 | 28 |
| strong-stories | 335 | 0 |

合計 2,687 集，其中 73 集為 M4A。RSS duration 加總約 588.38 小時；這是候選規模，不是已下載或轉錄數量。當日 10 份 feed 未發現 podcast:transcript 連結，因此本版以 ASR 產生逐字稿，沒有把節目簡介當作全文。

## 重現與限制

- 操作、搬機與憑證說明見 [部署指南](../deployment/README.md)。模型版本追蹤採檔案內容 SHA，原生此樣本模型指紋為 `3d81eb5f7f419aff01ad91e4293ebc30cc2322b98d210f64820ac432ac4eed7f`。
- 鎖定相依版本在 uv.lock；Docker CPU 使用含雜湊的 requirements-cpu.lock。gws 0.8.0 tarball 以發佈 SHA-256 驗證；映像使用非 root 使用者。
- Docker 實測未掛載真實 Drive credentials；Drive 音訊與 companion 真實驗證使用 host gws。Docker credentials 掛載與匯出流程依 gws 官方 repo 文件提供，未宣稱容器 OAuth 已驗證。
- 搬移測試是在同一台 Mac 的不同路徑驗證，未聲稱已在使用者另一台實體 Mac 執行。來源包包含打包時的程式，解壓後不依賴 Git 分支；本次部署驗證完成時尚未推送功能，後續發布狀態以 GitHub PR 為準。
- 再次遇到 Spectra 2.3.1 對 stable specs 的 `validate --all` 回傳空清單限制時，不將空結果視為 spec 解析通過；歸檔前驗證 active change，歸檔後逐條比較新增 requirement。
- 本機完整日誌在 Git 忽略的 outputs：portable-tests.log、docker-build.log、docker-portable-tests.log、transcription-native.jsonl、migration-smoke.jsonl、m4a-convert.jsonl、transcript-drive-validation.jsonl、transcript-drive-rerun.jsonl。

技術依據：[MLX Whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper)、[faster-whisper](https://github.com/SYSTRAN/faster-whisper)、[gws](https://github.com/googleworkspace/cli#authentication)。

## 最終交付檢查

`make check PYTHON=.venv/bin/python` 通過；66 個本機 Markdown 連結無缺檔。歸檔前 active change strict validate 通過，歸檔後 7 個新增 requirement 與 delta 逐條一致。來源包已解壓並成功執行 list（10 個節目），採白名單打包且不含音檔、模型或憑證。
