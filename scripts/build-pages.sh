#!/usr/bin/env bash
# Build static SPA for GitHub Pages (demo mode, no FastAPI).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${ROOT}/_site"
BASE_PATH="${BASE_PATH:-/JobPosting}"
# Normalize base path
BASE_PATH="/${BASE_PATH#/}"
BASE_PATH="${BASE_PATH%/}"

rm -rf "${OUT}"
mkdir -p "${OUT}"

cd "${ROOT}/frontend"

# Always install in CI; locally reuse node_modules when present.
if [[ "${CI:-}" == "true" || ! -x node_modules/.bin/tsc ]]; then
  npm ci --registry https://registry.npmjs.org/
fi

VITE_DEMO_MODE=true VITE_BASE_PATH="${BASE_PATH}/" npm run build

cp -R dist/. "${OUT}/"
# SPA fallback for deep links on GitHub Pages (no server rewrite)
cp "${OUT}/index.html" "${OUT}/404.html"
touch "${OUT}/.nojekyll"

echo "Built ${OUT} (base=${BASE_PATH}/, demoMode=true)"
echo "Open: https://amulyavarshney.github.io${BASE_PATH}/"
