#!/usr/bin/env bash
# Trigger scrape for a source.
# Usage: scrape-source.sh <source_id>
set -euo pipefail
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <source_id>" >&2
  exit 1
fi
SOURCE_ID="$1"
BASE="${JOBPOSTING_API:-http://127.0.0.1:8000/api}"
KEY="${JOBPOSTING_API_KEY:-}"
HDR=()
[[ -n "$KEY" ]] && HDR=(-H "X-API-Key: $KEY")
curl -sS "${HDR[@]}" -X POST "$BASE/sources/${SOURCE_ID}/scrape" | python3 -m json.tool
