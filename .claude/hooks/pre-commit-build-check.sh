#!/usr/bin/env bash
# Ensures dist/index.html is built from current sources before any git commit
# that includes template.html or parser scripts.
#
# Wire via settings.json PreToolUse hook for Bash(git:commit:*).

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/Users/jonghongjeon/git/nsb}"
TEMPLATE="$PROJECT_ROOT/src/web/template.html"
DIST="$PROJECT_ROOT/dist/index.html"

if [ ! -f "$DIST" ]; then
  echo "⚠️  dist/index.html 없음 — bash scripts/build.sh 먼저 실행하세요" >&2
  exit 2
fi

# If template is newer than dist, warn
if [ "$TEMPLATE" -nt "$DIST" ]; then
  echo "⚠️  template.html이 dist/index.html보다 새로움 — 빌드 누락 가능" >&2
  echo "   해결: bash scripts/build.sh" >&2
  exit 2
fi

# If any parser or data file is newer than dist
for p in "$PROJECT_ROOT/src/parser"/*.py "$PROJECT_ROOT/data/processed"/*.json; do
  if [ -f "$p" ] && [ "$p" -nt "$DIST" ]; then
    echo "⚠️  $p가 dist/index.html보다 새로움 — 재빌드 필요" >&2
    exit 2
  fi
done

exit 0
