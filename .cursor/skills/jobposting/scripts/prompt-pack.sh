#!/usr/bin/env bash
# Build a copy-paste AI prompt pack for a draft.
# Usage: prompt-pack.sh <draft_id> ["custom requirement"]
set -euo pipefail
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <draft_id> [requirement]" >&2
  exit 1
fi
DRAFT_ID="$1"
REQ="${2:-}"
BASE="${JOBPOSTING_API:-http://127.0.0.1:8000/api}"
KEY="${JOBPOSTING_API_KEY:-}"
HDR=(-H "Content-Type: application/json")
[[ -n "$KEY" ]] && HDR+=(-H "X-API-Key: $KEY")
BODY=$(python3 -c "import json; print(json.dumps({'requirement': '''${REQ}'''}))")
curl -sS "${HDR[@]}" -X POST "$BASE/drafts/${DRAFT_ID}/prompt-pack" -d "$BODY" | python3 -m json.tool
