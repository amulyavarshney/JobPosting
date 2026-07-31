#!/usr/bin/env bash
# List active jobs from local JobPosting API.
set -euo pipefail
BASE="${JOBPOSTING_API:-http://127.0.0.1:8000/api}"
KEY="${JOBPOSTING_API_KEY:-}"
HDR=()
[[ -n "$KEY" ]] && HDR=(-H "X-API-Key: $KEY")
curl -sS "${HDR[@]}" "$BASE/jobs?page_size=50&status=active" | python3 -m json.tool
