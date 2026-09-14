#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
if [[ "$(uname -s)" != Darwin || "$(uname -m)" != arm64 ]]; then
  echo '此腳本適用 Apple Silicon Mac；其他平台請用 Docker。' >&2
  exit 1
fi
for tool in uv ffmpeg; do
  if ! command -v "$tool" >/dev/null; then
    echo "缺少 $tool；請先執行 brew install uv ffmpeg" >&2
    exit 1
  fi
done
uv sync --python 3.13 --extra mac --frozen
mkdir -p content data/models outputs
.venv/bin/storysonic list
printf '\n安裝完成。先測一集：bash scripts/run-mac.sh download --show detective-pig --limit 1\n'
