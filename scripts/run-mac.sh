#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
if [[ ! -x .venv/bin/storysonic ]]; then
  echo '請先執行 bash scripts/setup-mac.sh' >&2
  exit 1
fi
if [[ $# -eq 0 ]]; then
  set -- --help
fi
exec caffeinate -i .venv/bin/storysonic "$@"
