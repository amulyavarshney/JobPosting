#!/usr/bin/env bash
# Generate Jinja drafts for a job.
# Usage: generate-drafts.sh <job_id> <template_id>[,<template_id>...]
set -euo pipefail
if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <job_id> <template_id>[,...]" >&2
  exit 1
fi
JOB_ID="$1"
TPLS="$2"
BASE="${JOBPOSTING_API:-http://127.0.0.1:8000/api}"
KEY="${JOBPOSTING_API_KEY:-}"
HDR=(-H "Content-Type: application/json")
[[ -n "$KEY" ]] && HDR+=(-H "X-API-Key: $KEY")
IDS=$(python3 -c "import json; print(json.dumps([int(x) for x in '${TPLS}'.split(',') if x.strip()]))")
curl -sS "${HDR[@]}" -X POST "$BASE/drafts/generate" \
  -d "{\"job_id\": ${JOB_ID}, \"template_ids\": ${IDS}}" | python3 -m json.tool
