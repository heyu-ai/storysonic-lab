## Why

既有研究已確認公開 RSS 音檔可取得，但 repo 尚無可重跑的下載與分類上傳工具。使用者需要將故事保存在 repo 的 content 目錄，再按 podcaster 上傳至指定 Google Drive「Podcast」資料夾，供後續故事與聲音分析。

## What Changes

- 新增 Python CLI，從可配置的 Podcast RSS 列出與篩選單集，串流下載至本機 content，以單集 manifest 保存來源、大小、SHA-256 與取得時間。
- 保留前十名節目的可編輯設定；支援單集標題篩選、數量限制、明確選取全部，以及 dry-run。
- 新增選用的 Google Drive 上傳，使用本機 gws 認證，指定資料夾 ID 或網址，在根目錄下按 podcaster／節目建立子資料夾；核對遠端檔案並避免重複上傳。
- MP3 與 content 產物不進 Git；更新 README、專案 context 與測試指令，記錄實際驗證結果。

## Capabilities

### New Capabilities

- `podcast-download`: RSS 單集選取、完整音檔下載、可追溯 manifest 與本機重跑。
- `podcast-drive-upload`: 指定 Drive 目的地、podcaster 分類、檔案驗證與重複處理。

### Modified Capabilities

無既有功能規格。

## Impact

- Affected specs: podcast-download、podcast-drive-upload。
- Affected code:
  - New: `storysonic/__init__.py`, `storysonic/__main__.py`, `storysonic/catalog.py`, `storysonic/download.py`, `storysonic/drive.py`, `tests/test_catalog.py`, `tests/test_download.py`, `tests/test_drive.py`, `tests/test_cli.py`, `podcasts.toml`, `pyproject.toml`, `Makefile`, `content/README.md`, `docs/research/2026-09-11-downloader-validation.md`。
  - Modified: `README.md`, `AGENTS.md`, `.gitignore`, `docs/openspec/config.yaml`, `docs/research/README.md`。
- 使用 Python 3.11+ 標準函式庫；Drive 整合需外部 gws CLI 及使用者授權。來源依據為 `docs/research/2026-09-10-taiwan-kids-podcasts/report.md`。
