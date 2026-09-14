# OpenSpec — Spectra 規格管理

本專案使用 **Spectra CLI** 管理 OpenSpec 文件。所有專案規格與變更都放在 **`docs/openspec/`**，由 repo 根目錄的 [`.spectra.yaml`](../../.spectra.yaml) 指定；不要另外建立根目錄 `openspec/`。

## 設定與目錄

| 路徑 | 用途 |
|---|---|
| [../../.spectra.yaml](../../.spectra.yaml) | Spectra 專案設定：`spec_dir`、語系與 AI 工具 |
| [config.yaml](config.yaml) | `spec-driven` workflow schema、專案 context 與 artifact 規則 |
| [specs/](specs/) | 已完成變更歸檔後的穩定規格 |
| [changes/](changes/) | 進行中的 proposal、design、delta specs 與 tasks |
| [changes/archive/](changes/archive/) | 已完成的變更歷史 |

使用 Spectra 內建的 `spec-driven` schema。yibi-mvp 的 `spec-driven-yibi` 含該專案的額外流程，本專案目前採用內建 schema；若之後需要自訂，再經研究與 ADR 決定。

## 開始操作

於 **repo 根目錄**執行：

```bash
spectra --version
spectra schemas
spectra list
spectra list --specs
spectra list --parked
spectra validate --all --strict
```

初始化以 Spectra 2.3.1 驗證。目前穩定規格包含 [Podcast 下載](specs/podcast-download/spec.md) 與 [Drive 上傳](specs/podcast-drive-upload/spec.md)，對應 [2026-09-11 變更歸檔](changes/archive/2026-09-11-add-podcast-download-drive/proposal.md)。實作與真實環境驗證結果見 [下載器驗證紀錄](../research/2026-09-11-downloader-validation.md)。

## 生命週期

```text
discuss（選用）→ propose → apply ⇄ ingest → archive
```

| 階段 | 主要工作 |
|---|---|
| discuss | 收斂問題、研究證據與範圍 |
| propose | 建立提案、delta specs、設計與驗收任務 |
| apply | 按任務實作與驗證 |
| ingest | 將中途變動的需求或新證據回填到提案 |
| archive | 完成驗證後，將規格差異合併到 `specs/` 並歸檔 change |

Claude 使用 `/spectra-*` skills，Codex 使用 `$spectra-*` skills。不要直接修改 CLI 管理的 `SPECTRA:START`／`SPECTRA:END` 區塊；專案補充約定放在管理區塊外。

手動操作範例（以下名稱只是示範，尚未建立這項功能）：

```bash
spectra new change add-podcast-catalog --description "Define podcast catalogue ingestion"
spectra status --change add-podcast-catalog
spectra instructions proposal --change add-podcast-catalog
# 完成提案、設計、規格差異與任務後：
spectra validate add-podcast-catalog --strict
# 實作及驗收完成後：
spectra archive add-podcast-catalog
```

Change 與 capability 使用描述性的英文 kebab-case 名稱。新功能、資料格式契約與跨模組變更透過 change 管理；一般研究筆記、純文件調整與初始化可直接更新文件。

## 穩定規格與 parked changes

- `specs/` 保存已落地行為，新增或修改功能時先在 `changes/<name>/specs/` 寫差異，完成後由 archive 合併。
- `spectra park <name>` 會將變更移到本機 `.spectra/`。本 repo 忽略該目錄，parked 成果不會隨 Git clone 分享。
- 要把提案交給其他人或提交版本控制，先 `spectra unpark <name>`，再確認 change 檔案出現在 `git status`。
- 更新 CLI 後可執行 `spectra update`，檢查設定與 skills 的 diff；目前不使用額外的 `spectra:` slash-command 別名。

## 與其他文件的關係

[Research](../research/README.md) 提供證據；[ADR](../adr/README.md) 記錄長期取捨；OpenSpec 描述可驗收的行為與當次變更。研究中的候選模型、推測與未驗證能力不會自動成為 stable spec。

已加入 [逐字稿與轉檔](specs/podcast-transcription/spec.md)、[可攜部署](specs/portable-deployment/spec.md) 規格，對應 [部署變更歸檔](changes/archive/2026-09-11-add-batch-collection-transcripts/proposal.md)。原生 Mac、Docker 與搬機操作見 [部署指南](../deployment/README.md)。
