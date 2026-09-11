# 部署與搬機：Apple Silicon Mac

建議用原生 MLX 轉逐字稿；Docker 提供下載、WAV 轉檔與 CPU 轉錄。模型直接在自己的電腦運算，不使用付費 ASR API。全量指令會處理 `podcasts.toml` 的 10 個節目；排名是 2026-09-10 的研究快照，不會自動改榜。

## 1. 在另一台 Mac 安裝

程式可由 Git checkout 或 `storysonic-lab-source.tar.gz` 取得。若拿到壓縮包：

```bash
mkdir -p ~/Workspace
cd ~/Workspace
tar -xzf ~/Downloads/storysonic-lab-source.tar.gz
cd storysonic-lab
brew install uv ffmpeg
bash scripts/setup-mac.sh
```

使用 Python 3.13、`uv.lock` 固定相依版本。腳本只建立此專案 `.venv`，不複製舊電腦的虛擬環境。`run-mac.sh` 包上 `caffeinate -i`，執行期間阻止閒置休眠；合蓋仍可能讓筆電睡眠，長工作請接電且保持開蓋。

## 2. 先測一集

```bash
bash scripts/run-mac.sh download --show detective-pig --limit 1
bash scripts/run-mac.sh transcribe --show detective-pig --limit 1 --language zh --traditional
bash scripts/run-mac.sh convert --show detective-pig --limit 1
```

MLX 預設模型為 `mlx-community/whisper-large-v3-turbo`。首次轉錄會將模型下載至 `data/models/`；重跑使用快取。轉錄會直接读取 MP3/M4A，所以 `convert` 是另存 WAV 的選配步驟。

可用 `--model-dir /Volumes/Podcast/models/whisper-large-v3-turbo` 指定完整本地模型；MLX 目錄需含 config 及 safetensors/npz 權重。不要將 faster-whisper 的 CTranslate2 模型交給 MLX。中文專題用 `--language zh`；包含英文的全榜批次保留 auto。

## 3. 執行排行榜 10 個節目全部公開單集

```bash
# 預覽全集範圍，不下載或寫檔
bash scripts/run-mac.sh download --all-shows --all --dry-run

# 執行並保存完整日誌；命令結束可用 echo $? 讀 exit code
bash scripts/run-mac.sh download --all-shows --all > outputs/download.jsonl 2> outputs/download.stderr
bash scripts/run-mac.sh transcribe --all-shows --all --traditional > outputs/transcribe.jsonl 2> outputs/transcribe.stderr

# 確實需要 WAV 時才執行，會增加磁碟用量
bash scripts/run-mac.sh convert --all-shows --all > outputs/convert.jsonl 2> outputs/convert.stderr
```

每個命令各自執行，上一個失敗可先修復再重跑，也可對已完成下载的單集進行下一階段。`--all-shows` 只改節目範圍，未加 `--all` 仍是每個節目最多 3 集；`--limit 1` 可做每節目一集驗證。RSS 可能隨時間變動，範圍限當次 feed 可取得的 MP3/M4A，包含預告、特別節目；付費或已下架音訊不在內。

下載上限預設每集 256 MiB，以 `--max-mb` 調整。每集開始前檢查至少保留 5 GiB，`--reserve-gb 20` 可提高。2026-09-11 feed 檢查約 2,687 集、588 小時，應預留數十 GB 給來源音檔，若全量另存 WAV 還需約 63 GiB。這是容量估算，不是完成數量。程序鎖只防同一 content root 的多個 writer；不要讓兩台機器同時上傳相同 Drive 目錄。

## 4. 搬移現有資料並續跑

先 Ctrl-C 停止舊機程序，待命令退出再複製。搬這些：

| 路徑 | 用途 | 是否需要 |
|---|---|---|
| 程式與 `podcasts.toml` | 相同 ID、分類與指令 | 需要 |
| `content/` 全目錄 | 音檔、來源 manifest、逐字稿與完成紀錄 | 要接續舊進度時需要 |
| `data/models/` | 模型權重快取 | 可選，可在新機下載 |
| `outputs/` | 執行日誌與驗證資料 | 可選 |
| `.venv/` | 本機安裝產物 | 新機重新安裝 |

例如舊 Mac 把資料複製到外接硬碟，再在新 Mac 複製回專案：

```bash
# 在舊機執行；不加 --delete
rsync -a content/ /Volumes/PodcastTransfer/storysonic-content/
rsync -a data/models/ /Volumes/PodcastTransfer/storysonic-models/

# 在新機的專案根目錄執行
rsync -a /Volumes/PodcastTransfer/storysonic-content/ content/
rsync -a /Volumes/PodcastTransfer/storysonic-models/ data/models/
```

也可直接用外接硬碟：每個命令加 `--content-dir /Volumes/Podcast/content`，轉錄加 `--cache-dir /Volumes/Podcast/models`。相對路徑以 CLI 的目前目錄解析；`run-mac.sh` 會先切到 repo 根目錄，建議外接位置一律用絕對路徑。

重跑相同指令即可續跑：完整音檔核對大小/SHA/MD5 後跳過；逐字稿核對來源 SHA、模型內容、engine 版本、語言、繁體設定及三個產物雜湊。中斷或破損的單集重做；換模型或參數另存一版。這是單集級續跑，下載沒有 HTTP Range，轉錄沒有句段 checkpoint。模型所在路徑可以不同，但模型檔案內容須相同才會命中同一版本。

## 5. 上傳 Google Drive

在新 Mac 安裝並登入 [gws](https://github.com/googleworkspace/cli#authentication)，不複製舊 Mac 的加密 keyring：

```bash
brew install googleworkspace-cli
gws auth login -s drive
bash scripts/run-mac.sh upload --all-shows --all --include-transcripts
```

若新機尚無 OAuth client 設定，依 gws 文件執行 `gws auth setup`，或配置 Desktop OAuth client 後登入。程式會使用 `podcasts.toml` 的 Drive 根目錄；可加 `--drive-folder FOLDER_ID` 覆寫。只有音檔時省略 `--include-transcripts`；明確要求逐字稿但尚未產生時會報錯。上傳不改分享權限。

分類為 `Podcaster [id]/Show [id]/`，原始音檔在節目目錄，逐字稿在 `transcripts/<episode-key>/<recipe-id>/`。每個檔案查遠端、核對大小/MD5，成功後記錄 Drive ID；中断後重跑可補查已建立但來不及記錄的檔案。

## 6. Docker 選項

Dockerfile 提供 Linux arm64/amd64 安裝對應，此回合實測 arm64。macOS 上的 Docker 版使用 CPU 轉錄；要使用 Apple GPU 請用上述原生版本。容器以非 root 身分執行，資料留在 host 的 bind mount，映像不含音檔、模型、credentials。

```bash
mkdir -p content data outputs
docker compose build
docker compose run --rm worker list
docker compose run --rm worker download --show detective-pig --limit 1
docker compose run --rm worker transcribe --show detective-pig --limit 1 --backend faster-whisper --traditional
docker compose run --rm worker convert --show detective-pig --limit 1

# 全量下載。之後可在同一份 content 上改用原生 MLX 轉錄。
docker compose run --rm worker download --all-shows --all
```

CPU 預設 `Systran/faster-whisper-small`，品質與 MLX large-v3-turbo 不同。可用 `--model Systran/faster-whisper-large-v3`，速度及空間成本會提高。MLX/CTranslate2 模型權重格式不同，不能直接共用；content 來源與 TXT/SRT/JSON 產物可共用。

Docker 上傳需要額外明確掛載 credentials。先在已登入的 host 匯出到 repo 外，請勿貼出檔案內容：

```bash
mkdir -p "$HOME/.config/storysonic"
umask 077
gws auth export --unmasked > "$HOME/.config/storysonic/gws.json"
export GWS_CREDENTIALS_FILE="$HOME/.config/storysonic/gws.json"
docker compose -f compose.yaml -f compose.drive.yaml run --rm worker upload --show detective-pig --all --include-transcripts
```

此檔含 OAuth refresh token；Compose 只讀掛載，主映像不保存。日常原生 Mac 上傳直接用 gws 登入即可，無須匯出。Docker daemon 不在本機或使用 Linux host 時，先確保 bind mount 目錄可由 UID 1000 寫入；不要用 chmod 777。

## 7. 產物與判讀

```text
content/<podcaster>/<show>/
  <episode-key>.mp3 或 .m4a
  <episode-key>.json
  derived/<episode-key>/<recipe-id>/
    transcript.txt + transcript.srt + transcript.json
    complete.json
  derived/<episode-key>/<另一個 recipe-id>/
    audio.wav + complete.json
```

`complete.json` 最後寫入，表示該版輸出完整且附 SHA/MD5。JSON 保留 `raw_text`、繁體顯示 `text`、秒數時間碼、模型指紋與 `reviewed: false`。這是 ASR 逐字稿，角色名、台語、中英夾雜、歌曲與多人重疊仍可能錯認；繁簡轉換不等於校對。說話人分離、故事／韻律分析尚未實作。

命令 stdout 是 JSON Lines；模型進度與其他診斷在 stderr。成功 exit 0，選取或處理有錯 exit 1，參數錯 exit 2，Ctrl-C/SIGTERM exit 130。若用管線保存輸出需啟用 `set -o pipefail`，避免遺失原始 exit status。

## 8. 打包與驗證

```bash
.venv/bin/python scripts/package.py
# 產生 outputs/storysonic-lab-source.tar.gz；不含音檔、模型或憑證
.venv/bin/python -m unittest discover -s tests -v
```

可另存已建好的映像供離線搬機（模型還要分開準備）：

```bash
docker save storysonic-lab:0.2.0 | gzip > outputs/storysonic-lab-image.tar.gz
# 新機：gzip -dc outputs/storysonic-lab-image.tar.gz | docker load
```

依賴來源與操作依據：[MLX Whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper)、[faster-whisper](https://github.com/SYSTRAN/faster-whisper)、[gws authentication](https://github.com/googleworkspace/cli#authentication)。實測證據見 [部署驗證紀錄](../research/2026-09-11-portable-validation.md)。
