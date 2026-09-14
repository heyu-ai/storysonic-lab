## Why

使用者將排行榜前 10 個節目全部公開單集的下載與逐字稿工作，改為搬到另一台 Apple Silicon Mac 執行。目前程式依賴 checkout 路徑、只收 MP3，且沒有正式轉錄與部署入口。

## What Changes

- 原生 macOS 安裝腳本使用 MLX；提供 CPU Docker 映像與 Compose，模型、content 與 credentials 分開保存。
- 支援 MP3 與 M4A enclosure，保留原始格式；所有工作命令接受 `--all-shows`。
- 新增 `transcribe` 輸出 TXT、SRT、JSON，記錄音檔及模型指紋與未校訂狀態；同參數重跑核對後跳過已完成單集。
- 新增 `convert` 將音檔轉成 16 kHz mono PCM WAV，保留原檔；提供逐字稿 Drive 上傳。
- 提供搬機、續跑、停止、磁碟空間與驗證說明；本機不繼續全量執行。

## Capabilities

### New Capabilities

- `podcast-transcription`: 可追溯、可重跑的逐字稿與 WAV 產物。
- `portable-deployment`: 原生 Mac 與 Docker 部署、可搬移資料與批次控制。

### Modified Capabilities

- `podcast-download`: 加入 M4A、全部節目選取與媒體忽略規則。
- `podcast-drive-upload`: 在節目子目錄上傳已驗證逐字稿並防止重複。

## Impact

影響 `storysonic/`、`tests/`、`pyproject.toml`、`.gitignore`、README；新增 `Dockerfile`、`compose.yaml`、`.dockerignore`、`scripts/` 與部署指南。新增選配 MLX/faster-whisper/OpenCC 模組，ffmpeg 用於解碼。現有 v1 MP3 manifest 與 Drive ID 保留。背景見 [下載驗證](../../../../research/2026-09-11-downloader-validation.md)。
