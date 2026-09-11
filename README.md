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

目前完成文件與 Spectra 工作流程初始化，並收錄首份台灣兒童故事 Podcast 研究。下載、轉錄、分析與訓練流程尚未實作成正式工具；技術棧與模型選型將由後續研究及 ADR 決定。

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
├── .spectra.yaml               # Spectra 設定，spec_dir: docs/openspec
├── .agents/skills/             # Spectra 產生的 Codex skills
├── .claude/skills/             # Spectra 產生的 Claude skills
└── docs/
    ├── README.md               # 文件導覽
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
- `specs/` 初始為空，代表尚無完成歸檔的功能規格；CLI 正常顯示空清單不代表初始化失敗。

完整命令、change 命名與 parked 狀態說明見 [OpenSpec 指南](docs/openspec/README.md)。

## 研究資料與版本管理

- `docs/research/` 收錄可分享報告、必要的目錄資料與驗證摘要；每份研究應標示查核日期、來源、方法與限制。
- 原始音檔、完整轉錄工作集與大型中間產物放在本機 `data/`、`outputs/`；這些目錄已加入 `.gitignore`，按需建立。
- 保留來源 URL、GUID、取得時間、檔案雜湊、轉錄模型版本與人工修正紀錄，以便重現結果。
- 公開可下載與可用於再發布、商業改編或模型訓練是不同條件；訓練資料候選集應記錄用途與授權狀態，不將未知狀態當作已授權。
- 分開記錄事實、分析推論與尚未驗證的假設；研究建議不會自動成為已接受的架構決策或正式規格。
