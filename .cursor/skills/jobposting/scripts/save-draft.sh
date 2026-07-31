#!/usr/bin/env bash
# Save polished draft content from a file.
# Usage: save-draft.sh <draft_id> <content-file>
set -euo pipefail
if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <draft_id> <content-file>" >&2
  exit 1
fi
DRAFT_ID="$1"
FILE="$2"
BASE="${JOBPOSTING_API:-http://127.0.0.1:8000/api}"
KEY="${JOBPOSTING_API_KEY:-}"
HDR=(-H "Content-Type: application/json")
[[ -n "$KEY" ]] && HDR+=(-H "X-API-Key: $KEY")
BODY=$(python3 -c "import json, pathlib; print(json.dumps({'content': pathlib.Path('${FILE}').read_text(), 'status': 'reviewed'}))")
curl -sS "${HDR[@]}" -X PATCH "$BASE/drafts/${DRAFT_ID}" -d "$BODY" | python3 -m json.tool
