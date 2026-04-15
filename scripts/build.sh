#!/usr/bin/env bash
# End-to-end build: PDF → processed JSON → single-file index.html
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PY="${PYTHON:-python3}"

echo "== [1/3] extract raw pages from PDFs =="
"$PY" scripts/extract_raw.py

echo "== [2/5] build ground-truth taxonomy (core tasks + agencies) =="
"$PY" src/parser/core_tasks.py

echo "== [3/5] encode 5차 회고 + 목표 추이 + 과제 매핑 =="
"$PY" src/parser/history_encoder.py

echo "== [4/7] extract projects (사업 atomic) =="
"$PY" src/parser/project_extractor.py

echo "== [5/8] classify projects (AI·tech·std·strategy) =="
"$PY" src/parser/classify.py

echo "== [6/8] extract agency metadata (legal basis + contact + PI) =="
"$PY" src/parser/impl_plan.py

echo "== [7/9] compute AI-centric linkage graph (weight = count × log10(1+budget)) =="
"$PY" src/parser/ai_linkage.py

echo "== [8/9] strategic gap analysis + sampling validation =="
"$PY" src/parser/gap_report.py
"$PY" scripts/sampling_validation.py

echo "== [9/9] render single-file dashboard =="
"$PY" scripts/build_html.py

echo "✓ done. open: dist/index.html"
