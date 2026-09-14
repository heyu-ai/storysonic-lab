## Context

2026-09-11 的 10 個 RSS 共找到 2,687 個 MP3/M4A enclosure，包含 73 個 M4A，總時長約 588 小時。這是當日公開 RSS 範圍，不保證包含已下架或付費集數。使用者指定另一台 Apple Silicon Mac；目前 Mac 的下載程序已停止，既有 content 保留。

## Goals / Non-Goals

**Goals:** 可安裝程式與 Docker、全部節目下載、音訊轉 WAV、逐字稿、依 podcaster 上傳與搬機續跑。

**Non-Goals:** 本機跑完全部 588 小時、付費 ASR、雲端部署費用、GPU Docker on macOS、說話人分離、角色模仿、訓練及授權判定、逐字人工校訂、RSS 之外的付費集數。

## Decisions

使用原生 MLX 作為 Apple Silicon 的操作預設，Docker 使用 faster-whisper CPU。明確指定 backend，不做靜默切換。依賴 extras 固定直接版本；模型檔案雜湊納入 recipe，搬移相同模型仍得到相同識別。模型預設從 Hugging Face 下載到可搬移 cache，也可指定本地模型目錄。

所有 content 路徑均相對於選定 root，CLI 設定預設從當前目錄讀取。選取 `--all-shows` 後 limit 為每個節目，全部單集仍需 `--all`。失敗輸出 JSON error 並繼續其餘節目，最後非零結束；進度以每集開始與完成事件呈現。Ctrl-C/SIGTERM 釋放鎖，不標記半成品成功。

續跑粒度採單集：一集所有產物及 hash manifest 原子寫入後才算完成，重跑先核對。不同音檔 SHA、模型內容、backend 版本或語言設定有不同 recipe 目錄。中斷單集重跑，已完成單集跳過。這讓跨機續跑不依賴額外資料庫。所有來源音檔保留，衍生物置於 `derived/<episode-key>/<recipe-id>/`，不混入既有音檔 manifest 掃描。

轉錄輸出原始識別文字與可選繁體轉換，JSON 保留逐段時間、語言、模型、音檔 SHA、`reviewed=false` 及產生時間。固定 task=transcribe，英文不翻譯；自動語言仍可能誤判台語或中英混合。

Drive 逐字稿置於節目下 `transcripts/<episode-key>/<recipe-id>/`，用 artifact identity 及大小/MD5 readback 防重複，避免跟既有 MP3 appProperties 查詢互相干擾。credentials 只在執行時以唯讀檔案掛載，映像建置採檔案白名單。

## Implementation Contract

`download|upload|transcribe|convert` 接受 `--show ID` 或 `--all-shows`、`--limit N|--all`、`--content-dir`、`--dry-run`。`transcribe` 接受 `--backend mlx|faster-whisper`、`--model`、`--model-dir`、`--cache-dir`、`--language auto|CODE`、`--traditional`；`upload --include-transcripts` 明確上傳完成的逐字稿。`convert` 只建立 WAV16k mono，不覆寫 MP3/M4A。

缺依賴、錯誤平台、無效音訊、非有限時間碼、hash 不符、無空間均須顯示 error。模型 API stdout 導向 stderr，CLI stdout 維持 NDJSON。測試覆蓋 M4A/v1 相容、搬移 content 後 skip、輸出破損重建、失敗不產生完成狀態、兩個 backend adapter、跨節目故障隔離、Drive 重跑防重複。原生實測限一集；Docker 若 daemon 無法啟動，明確保留未驗證標記。

## Risks / Trade-offs

- ASR 可能錯認角色名稱與台語 → raw text 留存且標記未校訂，繁簡轉換不等於校正。
- 約 588 小時需要長時間運算與數十 GB 音檔 → 預設每節目三集、全量需顯式選取；執行前預留磁碟空間，低於保留量即停止。
- Docker on Mac 的 CPU 轉錄較慢 → 主要文件引導原生 MLX；Docker 供下載及可攜 CPU fallback。
- 中斷會重做當前單集 → 採可驗證的每集完成狀態，避免部分文字被當作全文。

## Migration Plan

複製程式、`podcasts.toml`、`content/` 與可選模型快取到新 Mac，重新建立 venv；不搬 `.venv` 或加密 keyring。Drive 在新 Mac 登入，或 Docker 使用明確匯出的 credentials。先 dry-run，再一集驗證，再全量。保留原始檔與舊 manifest，可回到舊下載 CLI 讀取 MP3。

來源：[MLX Whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper)、[faster-whisper](https://github.com/SYSTRAN/faster-whisper)、[gws auth](https://github.com/googleworkspace/cli#authentication)。
