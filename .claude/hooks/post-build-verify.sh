#!/usr/bin/env bash
# Post-build sanity check. Invoked after `bash scripts/build.sh`.
# Validates payload size and key getter presence.

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/Users/jonghongjeon/git/nsb}"
DIST="$PROJECT_ROOT/dist/index.html"
MAX_KB=2048  # 2MB limit

if [ ! -f "$DIST" ]; then
  echo "❌ $DIST not found" >&2
  exit 1
fi

SIZE_KB=$(( $(wc -c < "$DIST") / 1024 ))
echo "📦 dist/index.html: ${SIZE_KB} KB"

if [ "$SIZE_KB" -gt "$MAX_KB" ]; then
  echo "⚠️  Payload exceeds ${MAX_KB} KB — consider externalizing data" >&2
fi

# Check key getter markers
REQUIRED_KEYS=(
  "top10BudgetProjects"
  "coreTaskDonutSvg"
  "aiDirectBudgetTotal"
  "aiSpokeEdgesSvg"
  "budgetStatusDonutSvg"
  "trackDonutSvg"
  "aiIndirectTop5"
  "dataCoverage"
)

MISSING=()
for key in "${REQUIRED_KEYS[@]}"; do
  if ! grep -q "$key" "$DIST"; then
    MISSING+=("$key")
  fi
done

if [ "${#MISSING[@]}" -gt 0 ]; then
  echo "❌ Missing getters in dist/: ${MISSING[*]}" >&2
  exit 2
fi

echo "✅ All required getters present. Build OK."
