#!/usr/bin/env bash
# Build static SPA for GitHub Pages (demo mode, no FastAPI).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${ROOT}/_site"
BASE_PATH="${BASE_PATH:-/job-posting}"
# Normalize base path
BASE_PATH="/${BASE_PATH#/}"
BASE_PATH="${BASE_PATH%/}"

rm -rf "${OUT}"
mkdir -p "${OUT}"

cd "${ROOT}/frontend"
if [[ ! -d node_modules/.bin/tsc ]]; then
  npm ci || npm install
fi
VITE_DEMO_MODE=true VITE_BASE_PATH="${BASE_PATH}/" npm run build

cp -R dist/. "${OUT}/"
touch "${OUT}/.nojekyll"

echo "Built ${OUT} (base=${BASE_PATH}/, demoMode=true)"
echo "Open: https://amulyavarshney.github.io${BASE_PATH}/"
