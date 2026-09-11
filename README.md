# StorySonic Lab

**故事聲音研究室** — Collect podcasts, analyze storytelling and speech, and curate datasets and prompt references for story generation.

研究 Podcast 的故事結構、敘事風格與聲音表現，將可追溯的分析結果整理成故事生成的 prompt 參考與訓練資料候選集。

## 專案方向

| 階段 | 研究與開發範圍 | 預期產物 |
|---|---|---|
| 蒐集 | 節目與單集目錄、RSS、公開音檔、來源與取得時間 | 來源清單、音檔 manifest |
| 轉錄 | 語音轉文字、時間碼、說話者區分與人工校對 | 逐字稿、字幕、校對紀錄 |
| 故事分析 | 開場、案件／衝突、線索、伏筆、角色對話、情緒與結尾 | 故事結構標記、風格分析 |
| 語音分析 | 語速、停頓、韻律、情緒、角色聲線、配樂與音效 | 聲音特徵、時間區段標記 |
| 研究應用 | 比較樣本、整理 prompt 範例、篩選與評估訓練資料 | Prompt 參考、資料集候選清單、評估結果 |

目前提供 **MP3/M4A 下載、WAV 轉檔、逐字稿（TXT/SRT/JSON）與 Google Drive 分類上傳**。可部署到另一台 Apple Silicon Mac，也提供 Docker CPU 版本。故事／聲音分析、說話人分離、人工校對及訓練流程尚未實作。

## 搬到另一台 Apple Silicon Mac

完整安裝、資料搬移、Docker 與 Drive credentials 說明見 [部署指南](docs/deployment/README.md)。

```bash
# 在新的 Mac、專案根目錄執行
brew install uv ffmpeg
bash scripts/setup-mac.sh

# 先測豬探長一集
bash scripts/run-mac.sh download --show detective-pig --limit 1
bash scripts/run-mac.sh transcribe --show detective-pig --limit 1 --language zh --traditional

# 前 10 個節目全部公開單集；建議分別執行並保存日誌
bash scripts/run-mac.sh download --all-shows --all
bash scripts/run-mac.sh transcribe --all-shows --all --traditional

# 另存 16 kHz mono WAV（選配，轉錄可直接讀原始音檔）
bash scripts/run-mac.sh convert --show detective-pig --limit 1
```

`run-mac.sh` 在工作期間使用 caffeinate 防止閒置休眠。既有 `content/` 與模型快取可搬移；每集完成後記錄雜湊，重跑核對後跳過，未完成單集重做。原生 MLX 使用 Apple GPU；Docker 使用 faster-whisper CPU。

```bash
mkdir -p content data outputs
docker compose build
docker compose run --rm worker download --show detective-pig --limit 1
docker compose run --rm worker transcribe --show detective-pig --limit 1 --backend faster-whisper --traditional

# 產生可搬移的程式包，不含音檔、模型與 credentials
.venv/bin/python scripts/package.py
```

程式包位於 `outputs/storysonic-lab-source.tar.gz`。已下載素材需分開複製 `content/`，不要搬 `.venv`；新機重新安裝。實測範圍見 [部署驗證紀錄](docs/research/2026-09-11-portable-validation.md)。

## 下載故事到 content

使用 **Python 3.11–3.13，macOS／Linux**。下載功能只用標準函式庫，不需安裝 Python 套件；以下指令從 repo 根目錄執行。

```bash
# 列出已設定的 10 個節目；這份清單來自研究快照，可自行編輯
python3 -m storysonic list

# 看豬探長最新 3 個 MP3/M4A 條目
python3 -m storysonic list --show detective-pig

# 預覽指定故事；不寫入 content，也不呼叫 Drive
python3 -m storysonic download --show detective-pig --match "袖珍娃娃屋奇案" --all --dry-run

# 下載符合標題的上下集
python3 -m storysonic download --show detective-pig --match "袖珍娃娃屋奇案" --all

# 下載公開 RSS 中全部可取得的 MP3/M4A（包含特別節目／預告）
python3 -m storysonic download --show detective-pig --all
```

預設每個節目最多 3 集，由新到舊；`--limit 10` 指定數量，`--all` 明確選取全部，兩者不能同時使用。`--all-shows` 選取設定檔所有節目，仍須 `--all` 才不限單集數。`--match` 是標題子字串搜尋。`--max-mb 256` 限制單集大小（MiB），預設 256。來源必須是公開 HTTP(S) RSS 2.0 中的 MP3/M4A enclosure。

音檔保存於 `content/<podcaster-id>/<show-id>/<episode-key>.mp3` 或 `.m4a`，同名 JSON 保存故事名稱、來源、GUID、時間、大小、SHA-256、MD5 與上傳紀錄。重跑會先核對本機檔案，完整檔案顯示 `skipped`；損壞或不完整檔案會重新下載。中斷後從整檔重新傳輸，並非 byte-range 續傳。詳見 [content 說明](content/README.md)。

工作命令以 JSON Lines 輸出事件，最後附處理數量摘要；有任一單集失敗就回傳非零狀態。不要只依檔案存在判斷成功，應看 manifest 核對與命令結果。

## 依 podcaster 上傳 Google Drive

Drive 整合使用 [Google Workspace CLI（gws）](https://github.com/googleworkspace/cli) 的檔案 API。安裝 gws 並完成 OAuth 設定後，執行：

```bash
gws auth login -s drive

# 預览已下載單集的上傳計畫
python3 -m storysonic upload --show detective-pig --all --dry-run

# 上傳已下載單集至 podcasts.toml 的預設目的地
python3 -m storysonic upload --show detective-pig --all

# 已完成轉錄後，加上 TXT/SRT/JSON 逐字稿
python3 -m storysonic upload --show detective-pig --all --include-transcripts

# 也可指定不同 Drive 根目錄（ID 或資料夾網址）
python3 -m storysonic upload --show detective-pig --all \
  --drive-folder "https://drive.google.com/drive/folders/1gae0A1FcXlkWdGZeFrE4SEs6X-cMXlmj"

# 一次完成下載與上傳；未加 --upload 時只下載
python3 -m storysonic download --show detective-pig --limit 3 --upload
```

[podcasts.toml](podcasts.toml) 已設定指定的 [Podcast 根目錄](https://drive.google.com/drive/folders/1gae0A1FcXlkWdGZeFrE4SEs6X-cMXlmj)。上傳使用 gws 登入帳號，需能寫入此資料夾；Codex Drive connector 與本機 gws 的登入彼此獨立。本機登入過期時，重新執行上述 auth login 即可，下載檔案會保留。

Drive 分類範例：

```text
Podcast/
└── 如果兒童劇團 [ifkids]/
    ├── 豬探長推理故事集 [detective-pig]/
    │   └── EP.131 袖珍娃娃屋奇案(上集)--<episode-key>.mp3
    └── 強哥為你說故事 [strong-stories]/
```

分類由設定檔的 podcaster／show ID 決定；同一製作人的不同節目會放在同一 podcaster 目錄下。上傳後讀回 Drive 檔案大小與 MD5，核對成功才寫入 manifest。重跑會先查遠端；相同單集且內容一致則 `upload_skipped`，內容衝突或重複目錄則報錯。工具不刪除、覆寫遠端檔案，也不調整分享權限。請用單一 writer 執行，避免多台電腦同時建立同一單集。

新增節目可在 podcasts.toml 增加一個 `[[shows]]`，填入 `id`、`name`、`podcaster_id`、`podcaster_name`、`feed_url`。穩定 ID 使用小寫英文、數字與連字號；已有內容後勿任意改 ID 或分類名稱。各命令可加 `--config /path/podcasts.toml`、`--content-dir /path/content`，憑證留在 gws 的本機設定中。

## 開發與驗證

```bash
make test
make check
```

測試使用標準函式庫 unittest，覆蓋 RSS 選取、下載完整性、重跑、路徑／鎖、Drive 分類、分頁、衝突與錯誤。Drive 測試以受控的 gws 回應驗證；真實連線結果另記錄於 [下載器驗證紀錄](docs/research/2026-09-11-downloader-validation.md)，不將模擬上傳等同真實 Drive 上傳。

## 先看研究成果

[台灣兒童故事 Podcast 前十名與豬探長資料取得研究](docs/research/2026-09-10-taiwan-kids-podcasts/README.md)（資料查核日：2026-09-10）。

- [研究報告](docs/research/2026-09-10-taiwan-kids-podcasts/report.md)：排行榜、音檔下載驗證、文字稿取得途徑與限制。
- [可分享 HTML](docs/research/2026-09-10-taiwan-kids-podcasts/taiwan-kids-podcast-research.html)：下載後用瀏覽器開啟，包含故事搜尋與 CSV 匯出；GitHub 檔案頁不會直接執行 HTML。
- [公開單集目錄](docs/research/2026-09-10-taiwan-kids-podcasts/all-episodes.csv)：2,684 個 RSS 條目，包含試聽、預告與特別節目。
- [豬探長故事配對](docs/research/2026-09-10-taiwan-kids-podcasts/pig-stories.csv)：67 個故事題名，查核時 66 組上下集齊全。

這份研究已驗證一集豬探長完整 MP3 下載與解碼，尚未完成全系列轉錄或故事品質評分。排名、集數與來源可用性均為查核日快照。

## 文件結構

沿用 yibi-mvp 的文件分工，將研究、決策與規格放在不同目錄。

```text
storysonic-lab/
├── README.md
├── AGENTS.md                   # Codex 指引與專案工作約定
├── CLAUDE.md                   # Claude 指引
├── storysonic/                 # Python CLI：下載、轉錄、轉檔與 Drive 上傳
├── podcasts.toml               # 節目／podcaster 與預設 Drive 目的地
├── content/                    # 本機音檔與 manifest；只有 README 進 Git
├── tests/                      # 標準函式庫 unittest
├── .spectra.yaml               # Spectra 設定，spec_dir: docs/openspec
├── .agents/skills/             # Spectra 產生的 Codex skills
├── .claude/skills/             # Spectra 產生的 Claude skills
└── docs/
    ├── README.md               # 文件導覽
    ├── deployment/             # 原生 Mac、Docker 與搬機指南
    ├── adr/                    # 架構決策、選項、取捨與決策紀錄
    ├── research/               # 調查、實驗、研究報告與可分享成果
    └── openspec/
        ├── README.md           # 規格管理與操作方式
        ├── config.yaml         # spec-driven schema 與專案 context
        ├── specs/              # 穩定規格
        └── changes/            # 變更提案與規格差異
            └── archive/        # 已完成的變更歷史
```

[文件導覽](docs/README.md) · [ADR](docs/adr/README.md) · [Research](docs/research/README.md) · [OpenSpec](docs/openspec/README.md)

## 使用 OpenSpectra / Spectra

本專案使用 **Spectra CLI** 管理 OpenSpec 格式的文件，唯一規格根目錄為 **`docs/openspec`**。初始化已以 Spectra **2.3.1** 驗證。

先安裝可執行 `spectra` 的 [Spectra 工具](https://github.com/spectra-app/spectra)，再於 repo 根目錄執行：

```bash
spectra --version
spectra schemas
spectra list
spectra list --specs
spectra validate --all --strict
```

新 clone 已包含設定與 skills，不需要重新初始化。更新工具版本後，可執行 `spectra update` 更新產生檔，再檢查 diff。

初始化使用的指令如下，供重建時參考：

```bash
spectra init . --dir docs/openspec --tools claude,codex
```

功能開發流程：

```text
discuss（選用）→ propose → apply ⇄ ingest → archive
```

- Claude 使用 `/spectra-propose`、`/spectra-apply` 等 skills。
- Codex 使用 `$spectra-propose`、`$spectra-apply` 等 skills。
- 新功能、資料格式契約與跨模組改動先建 change；實作完成並驗證後，再 archive 合併規格差異。
- 一般研究筆記、文件整理與工具初始化可直接更新相關文件，不需建立虛構的功能 change。
- `specs/` 已收錄 [Podcast 下載](docs/openspec/specs/podcast-download/spec.md) 與 [Drive 上傳](docs/openspec/specs/podcast-drive-upload/spec.md) 規格；並加入 [逐字稿與轉檔](docs/openspec/specs/podcast-transcription/spec.md)、[可攜部署](docs/openspec/specs/portable-deployment/spec.md)；完成歸檔的 change 保存在 archive。

完整命令、change 命名與 parked 狀態說明見 [OpenSpec 指南](docs/openspec/README.md)。

## 研究資料與版本管理

- `docs/research/` 收錄可分享報告、必要的目錄資料與驗證摘要；每份研究應標示查核日期、來源、方法與限制。
- 下載音檔與 manifest 放在本機 `content/`；其他工作集與大型中間產物放在 `data/`、`outputs/`。這些產物已加入 `.gitignore`，且 repo 各處的 MP3、M4A 與 WAV 都排除追蹤。
- 保留來源 URL、GUID、取得時間、檔案雜湊、轉錄模型版本與人工修正紀錄，以便重現結果。
- 公開可下載與可用於再發布、商業改編或模型訓練是不同條件；訓練資料候選集應記錄用途與授權狀態，不將未知狀態當作已授權。
- 分開記錄事實、分析推論與尚未驗證的假設；研究建議不會自動成為已接受的架構決策或正式規格。
