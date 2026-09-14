# 本機故事音檔

此目錄保留 README；下載產物、逐字稿及 MP3/M4A/WAV 不進 Git。CLI 預設依 podcaster ID／show ID 分類：

```text
content/
├── README.md
├── .storysonic.lock
└── ifkids/
    └── detective-pig/
        ├── <episode-key>.mp3
        └── <episode-key>.json
```

JSON manifest 保存故事標題、GUID、RSS／音檔 URL、下載時間、大小、SHA-256、MD5，以及按 Drive 根目錄 ID 索引的上傳核對紀錄。episode key 由節目 ID 與 GUID 產生，不受標題改名影響。看標題請用 list 或 manifest；Drive 音檔名稱包含故事標題。

下載使用 .part 暫存，完整後才保存為 .mp3 或 .m4a。程序中斷後可重跑相同命令；本版從整檔重新傳輸，沒有 byte-range 續傳。同一 content 根目錄只允許一個寫入程序。

CSV／HTML 研究快照仍放在 [docs/research](../docs/research/README.md)，本機大型分析產物可放在 outputs。更多命令見 [README](../README.md)。

## 衍生物與搬機

轉錄與 WAV 產物在 `derived/<episode-key>/<recipe-id>/`；逐字稿包含 TXT、SRT 與 JSON，`complete.json` 在所有產物完成後才寫入。它記錄來源 SHA、模型/處理設定與檔案雜湊；不同 recipe 分開保存。

搬機時先停止 writer，再複製整個 content 目錄；manifest 不依賴舊機絕對路徑。重新執行相同命令會驗證並跳過完整檔案，當前未完成單集重做。模型 cache 在 data/models，.venv 在新機重建。詳見 [部署指南](../docs/deployment/README.md)。
