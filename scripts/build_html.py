#!/usr/bin/env python3
"""
Merge processed JSON into a single dataset and inject into the HTML template,
producing a fully self-contained `dist/index.html`.

Pipeline:
  src/web/template.html  +  data/processed/*.json  ─▶  dist/index.html

The template has exactly one placeholder: `{{DATA}}` inside the
`<script type="application/json" id="nsb-data">` block.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "src" / "web" / "template.html"
PROCESSED = ROOT / "data" / "processed"
DIST = ROOT / "dist"
OUT = DIST / "index.html"

PLACEHOLDER = "{{DATA}}"


def load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def safe_inline(payload: dict) -> str:
    """
    JSON-encode and defuse the only sequence that can break out of
    <script type="application/json">: the literal </script .
    """
    s = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return s.replace("</", "<\\/")


def build_dataset() -> dict:
    taxonomy = load_json(PROCESSED / "tech_categories.v1.json") or {"categories": []}
    core_tasks_doc = load_json(PROCESSED / "core_tasks.v1.json") or {}
    agencies_doc = load_json(PROCESSED / "agencies.v1.json") or {}
    projects_doc = load_json(PROCESSED / "projects.v1.json") or {}
    std_bodies_doc = load_json(PROCESSED / "std_bodies.v1.json") or {}
    linkages_doc = load_json(PROCESSED / "ai_linkage.v1.json") or {}
    aggregates = load_json(PROCESSED / "aggregates.v1.json")
    history_doc = load_json(PROCESSED / "history_5th.v1.json") or {}
    trajectory_doc = load_json(PROCESSED / "goal_trajectory.v1.json") or {}
    mapping_doc = load_json(PROCESSED / "task_mapping_5_to_6.v1.json") or {}
    budget_traj = load_json(PROCESSED / "budget_trajectory.v1.json") or {}
    perf_ind = load_json(PROCESSED / "performance_indicators.v1.json") or {}
    task_timeline = load_json(PROCESSED / "task_timeline.v1.json") or {}
    yearly_summary = load_json(PROCESSED / "yearly_summary.v1.json") or {}
    kpi_pi_links = load_json(PROCESSED / "kpi_pi_links.v1.json") or {}
    strategy_gaps_doc = load_json(PROCESSED / "strategy_gaps.v1.json") or {}
    agency_coop = load_json(PROCESSED / "agency_cooperation_matrix.v1.json") or {}
    cooperations = load_json(PROCESSED / "cooperations.v1.json") or {}

    return {
        "meta": {
            "schema_version": "0.5",
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
        "taxonomy": taxonomy,
        "domains": core_tasks_doc.get("domains", []),
        "core_tasks": core_tasks_doc.get("tasks", []),
        "core_tasks_history": core_tasks_doc.get("history", {}),
        "agencies": agencies_doc.get("agencies", []),
        "projects": projects_doc.get("projects", []),
        "project_stats": projects_doc.get("stats", {}),
        "std_bodies": std_bodies_doc.get("bodies", []),
        "ai_linkage": {
            "edges": linkages_doc.get("ai_edges", []),
            "matrix": linkages_doc.get("matrix", []),
            "stats": linkages_doc.get("stats", {}),
            "method": linkages_doc.get("method", ""),
        },
        "aggregates": aggregates or {},
        "fifth_plan": history_doc,
        "trajectories": trajectory_doc.get("trajectories", []),
        "task_mappings": mapping_doc.get("mappings", []),
        "budget_trajectory": budget_traj.get("agencies", []),
        "budget_totals": budget_traj.get("totals", {}),
        "performance_indicators": perf_ind.get("indicators", []),
        "pi_stats": perf_ind.get("stats", {}),
        "task_timeline": task_timeline.get("tasks", []),
        "yearly_summary": yearly_summary,
        "kpi_pi_links": kpi_pi_links.get("links", []),
        "strategy_gaps": strategy_gaps_doc,
        "agency_cooperation": agency_coop,
        "cooperations": cooperations.get("cooperations", []),
    }


def main() -> int:
    if not TEMPLATE.exists():
        print(f"[ERROR] template not found: {TEMPLATE}", file=sys.stderr)
        return 1
    template = TEMPLATE.read_text(encoding="utf-8")
    if PLACEHOLDER not in template:
        print(f"[ERROR] placeholder {PLACEHOLDER} missing in template", file=sys.stderr)
        return 1

    dataset = build_dataset()
    inlined = safe_inline(dataset)
    html = template.replace(PLACEHOLDER, inlined)

    DIST.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")

    size_kb = OUT.stat().st_size / 1024
    data_kb = len(inlined.encode("utf-8")) / 1024
    print(f"[build_html] wrote {OUT.relative_to(ROOT)}  "
          f"(html {size_kb:.1f} KB, data {data_kb:.1f} KB)")

    if data_kb > 2048:
        print("[warn] embedded data > 2MB — consider externalizing to dist/data.json",
              file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
