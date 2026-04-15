#!/usr/bin/env python3
"""
Build AI-centric linkage graph with dual weighting.

For each pair (AI=T01, other=Tk):
  count   = # projects where both T01 and Tk are tagged
  budget  = Σ project.budget.total_mil_krw for those projects
  weight  = count × log10(1 + budget)     ← 공출현 빈도 + 예산 규모 균형

Also computes symmetric 18×18 technology co-occurrence matrix so the UI
can render both the AI spoke (AI 행/열) and full matrix view.

Output:
  data/processed/ai_linkage.v1.json
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"

ANCHOR = "T01"


def main() -> int:
    projects = json.loads(
        (PROCESSED / "projects.v1.json").read_text(encoding="utf-8")
    )["projects"]
    taxonomy = json.loads(
        (PROCESSED / "tech_categories.v1.json").read_text(encoding="utf-8")
    )["categories"]
    tech_ids = [t["id"] for t in taxonomy]

    # pair counts + budget aggregation
    pair_count: dict[tuple[str, str], int] = defaultdict(int)
    pair_budget: dict[tuple[str, str], int] = defaultdict(int)
    pair_projects: dict[tuple[str, str], list[str]] = defaultdict(list)

    for p in projects:
        tags = sorted(set(p.get("tech_category_ids") or []))
        if len(tags) < 2:
            continue
        budget = int((p.get("budget") or {}).get("total_mil_krw") or 0)
        pid = p["id"]
        for i in range(len(tags)):
            for j in range(i + 1, len(tags)):
                key = (tags[i], tags[j])
                pair_count[key] += 1
                pair_budget[key] += budget
                pair_projects[key].append(pid)

    # Build full 18x18 matrix
    matrix = []
    for a in tech_ids:
        row = []
        for b in tech_ids:
            if a == b:
                row.append({"count": None, "budget": None, "weight": None})
                continue
            key = (a, b) if a < b else (b, a)
            c = pair_count.get(key, 0)
            bud = pair_budget.get(key, 0)
            w = c * math.log10(1 + bud) if c else 0.0
            row.append({
                "count": c,
                "budget": bud,
                "weight": round(w, 3),
            })
        matrix.append({"tech_id": a, "cells": row})

    # AI-centric edges (anchor = T01)
    edges = []
    for tid in tech_ids:
        if tid == ANCHOR:
            continue
        key = (ANCHOR, tid) if ANCHOR < tid else (tid, ANCHOR)
        c = pair_count.get(key, 0)
        bud = pair_budget.get(key, 0)
        w = c * math.log10(1 + bud) if c else 0.0
        edges.append({
            "source": ANCHOR,
            "target": tid,
            "count": c,
            "budget_mil_krw": bud,
            "weight": round(w, 3),
            "project_ids": pair_projects.get(key, []),
        })

    edges.sort(key=lambda e: -e["weight"])

    payload = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "anchor": ANCHOR,
        "method": "weight = count × log10(1 + budget_mil_krw)",
        "tech_ids": tech_ids,
        "ai_edges": edges,
        "matrix": matrix,
        "stats": {
            "nonzero_ai_edges": sum(1 for e in edges if e["count"] > 0),
            "nonzero_matrix_cells": sum(
                1 for row in matrix for c in row["cells"]
                if c.get("count") and c["count"] > 0
            ),
            "total_ai_linkage_budget": sum(e["budget_mil_krw"] for e in edges),
        },
    }
    (PROCESSED / "ai_linkage.v1.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"[ai_linkage] AI edges: {payload['stats']['nonzero_ai_edges']}/17, "
          f"matrix cells: {payload['stats']['nonzero_matrix_cells']}, "
          f"total AI-linkage budget: {payload['stats']['total_ai_linkage_budget']:,} 백만원")
    print("Top 5 AI linkages (by weight):")
    for e in edges[:5]:
        if e["count"]:
            print(f"  AI↔{e['target']}  count={e['count']}  "
                  f"budget={e['budget_mil_krw']:,}  weight={e['weight']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
