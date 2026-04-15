#!/usr/bin/env python3
"""
Strategic gap analysis report generator.

For each (기술 T01~T18 × 전략 S-DOM/S-CAB/S-HR/S-INT × 트랙 formal/de_facto/hybrid)
cube cell, compute project count + budget. Flag cells as gaps when:
  - count == 0 (absolute gap)
  - count > 0 but budget < 10% of strategy-area average (under-invested)
  - single-agency dependency (fragile coverage)

Output: docs/insights/gaps.md — Markdown report consumed by humans.
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
INSIGHTS = ROOT / "docs" / "insights"

STRATEGIES = [
    ("S-DOM", "국내표준 (KS)"),
    ("S-CAB", "시험·인증 (적합성평가)"),
    ("S-HR",  "표준 전문인력"),
    ("S-INT", "국제표준 연계"),
]

TRACKS = [
    ("formal",   "공적 (ISO/IEC/ITU)"),
    ("de_facto", "사실상 (IEEE/ASTM…)"),
    ("hybrid",   "혼합 (Fast-Track)"),
]


def main() -> int:
    projects = json.loads(
        (PROCESSED / "projects.v1.json").read_text(encoding="utf-8")
    )["projects"]
    taxonomy = json.loads(
        (PROCESSED / "tech_categories.v1.json").read_text(encoding="utf-8")
    )["categories"]

    # Build 3D cube: (tech, strategy, track) → {count, budget, agencies}
    cube: dict[tuple[str, str, str], dict] = defaultdict(lambda: {
        "count": 0, "budget": 0, "agencies": set(), "projects": []
    })

    for p in projects:
        techs = p.get("tech_category_ids") or []
        strategies = p.get("strategy_areas") or []
        track = p.get("track_type") or "none"
        budget = (p.get("budget") or {}).get("total_mil_krw") or 0
        aid = p.get("agency_id")
        for t in techs:
            for s in strategies:
                key = (t, s, track)
                cube[key]["count"] += 1
                cube[key]["budget"] += budget
                if aid:
                    cube[key]["agencies"].add(aid)
                cube[key]["projects"].append(p["id"])

    # Compute per-strategy averages for under-investment detection
    strategy_totals: dict[str, int] = defaultdict(int)
    strategy_cells: dict[str, int] = defaultdict(int)
    for (t, s, tr), v in cube.items():
        if v["count"]:
            strategy_totals[s] += v["budget"]
            strategy_cells[s] += 1
    strategy_avg = {s: (strategy_totals[s] / strategy_cells[s] if strategy_cells[s] else 0)
                    for s in strategy_totals}

    # Classify each cell
    gaps_absent: list[dict] = []
    gaps_under: list[dict] = []
    gaps_fragile: list[dict] = []

    tech_ids = [t["id"] for t in taxonomy]
    tech_names = {t["id"]: t["name_ko"] for t in taxonomy}

    for tid in tech_ids:
        for sid, _ in STRATEGIES:
            for trid, _ in TRACKS:
                key = (tid, sid, trid)
                v = cube.get(key, {"count": 0, "budget": 0, "agencies": set(), "projects": []})
                if v["count"] == 0:
                    gaps_absent.append({"tech": tid, "strategy": sid, "track": trid})
                elif v["budget"] < (strategy_avg.get(sid, 0) * 0.10):
                    gaps_under.append({
                        "tech": tid, "strategy": sid, "track": trid,
                        "count": v["count"], "budget": v["budget"],
                        "avg_strategy_cell": int(strategy_avg[sid]),
                    })
                elif len(v["agencies"]) == 1:
                    gaps_fragile.append({
                        "tech": tid, "strategy": sid, "track": trid,
                        "count": v["count"], "budget": v["budget"],
                        "single_agency": next(iter(v["agencies"])),
                    })

    # Report structure
    INSIGHTS.mkdir(parents=True, exist_ok=True)
    out = INSIGHTS / "gaps.md"

    lines = []
    lines.append("# 전략 공백 자동 리포트 (gaps.md)\n")
    lines.append(f"생성: {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    lines.append(f"\n기반 데이터: 92 사업 × 18 기술 × 4 전략 × 3 트랙 = "
                 f"{18*4*3} 셀 중 실제 데이터 존재 "
                 f"{sum(1 for v in cube.values() if v['count']>0)} 셀")
    lines.append("")
    lines.append("## 집계 기준")
    lines.append("- **absent (🔴 공백)**: 사업 0건 — 해당 조합의 표준화 활동 부재")
    lines.append("- **under (🟡 저투자)**: 사업은 있으나 전략 영역 셀 평균 예산의 10% 미만")
    lines.append("- **fragile (🟠 단일 부처 의존)**: 1개 부처만 참여 — 리스크")
    lines.append("")

    # AI-focused top priority
    ai_gaps = [g for g in gaps_absent if g["tech"] == "T01"]
    ai_under = [g for g in gaps_under if g["tech"] == "T01"]
    lines.append("## 🎯 AI 우선 분석 (T01)")
    lines.append("")
    lines.append(f"- AI 공백 셀: **{len(ai_gaps)}/12 조합** (전체 AI 셀의 "
                 f"{len(ai_gaps)/12*100:.0f}%)")
    lines.append(f"- AI 저투자 셀: {len(ai_under)}")
    lines.append("")
    if ai_gaps:
        lines.append("### AI 전략 공백 (우선 투자 대상)\n")
        lines.append("| 전략 | 트랙 | 해석 |")
        lines.append("|---|---|---|")
        interp = {
            ("S-DOM","formal"):   "KS AI 표준 제정 미참여",
            ("S-DOM","de_facto"): "국내 민간 AI 단체표준 없음",
            ("S-DOM","hybrid"):   "국내 표준 hybrid 경로 무활동",
            ("S-CAB","formal"):   "공적 AI 적합성평가 (KOLAS AI) 부재",
            ("S-CAB","de_facto"): "사실상 AI 인증 (IEEE/ML 벤치마크 등) 미참여",
            ("S-CAB","hybrid"):   "AI 인증 상호인정 미구축",
            ("S-HR", "formal"):   "ISO/IEC SC42 의장·에디터 양성 부재",
            ("S-HR", "de_facto"): "IEEE P7xxx AI 에디터 양성 없음",
            ("S-HR", "hybrid"):   "AI 국제 명장 멘토링 무활동",
            ("S-INT","formal"):   "ISO/IEC/ITU AI 표준 제안 없음 (이상)",
            ("S-INT","de_facto"): "IEEE/MPAI/AI Alliance 참여 없음",
            ("S-INT","hybrid"):   "AI Fast-Track·Dual-logo 미활용",
        }
        for g in ai_gaps:
            i = interp.get((g["strategy"], g["track"]), "(해석 미작성)")
            lines.append(f"| {g['strategy']} | {g['track']} | {i} |")
        lines.append("")

    # Overall absent distribution
    lines.append("## 🔴 전체 공백 분포 (기술별)\n")
    lines.append("| 기술 | 공백 셀 / 12 | 비율 |")
    lines.append("|---|---|---|")
    tech_absent_count: dict[str, int] = defaultdict(int)
    for g in gaps_absent:
        tech_absent_count[g["tech"]] += 1
    for tid in tech_ids:
        n = tech_absent_count.get(tid, 0)
        ratio = n / 12 * 100
        lines.append(f"| {tid} {tech_names[tid]} | {n} | {ratio:.0f}% |")
    lines.append("")

    # Top under-invested cells
    lines.append("## 🟡 저투자 Top-10 (비-AI 포함)\n")
    lines.append("| 기술 | 전략 | 트랙 | 사업수 | 예산(백만) | 영역 평균 대비 |")
    lines.append("|---|---|---|---|---|---|")
    top_under = sorted(gaps_under, key=lambda x: x["budget"])[:10]
    for g in top_under:
        ratio = g["budget"] / g["avg_strategy_cell"] * 100 if g["avg_strategy_cell"] else 0
        lines.append(f"| {g['tech']} {tech_names[g['tech']]} | {g['strategy']} | {g['track']} "
                     f"| {g['count']} | {g['budget']:,} | {ratio:.1f}% |")
    lines.append("")

    # Fragile cells
    lines.append(f"## 🟠 단일 부처 의존 셀 ({len(gaps_fragile)}개)\n")
    if gaps_fragile:
        lines.append("| 기술 | 전략 | 트랙 | 사업수 | 예산(백만) | 단독 부처 |")
        lines.append("|---|---|---|---|---|---|")
        top_fragile = sorted(gaps_fragile, key=lambda x: -x["budget"])[:15]
        for g in top_fragile:
            lines.append(f"| {g['tech']} {tech_names[g['tech']]} | {g['strategy']} | {g['track']} "
                         f"| {g['count']} | {g['budget']:,} | {g['single_agency']} |")
        lines.append("")

    # Summary
    lines.append("## 📊 요약")
    lines.append(f"- 전체 공백 셀: **{len(gaps_absent)}/{18*4*3}** "
                 f"({len(gaps_absent)/(18*4*3)*100:.1f}%)")
    lines.append(f"- 저투자 셀: {len(gaps_under)}")
    lines.append(f"- 단일 부처 의존: {len(gaps_fragile)}")
    lines.append(f"- 전략 영역 평균 예산:")
    for sid, sname in STRATEGIES:
        avg = strategy_avg.get(sid, 0)
        lines.append(f"  - {sid} {sname}: {int(avg):,} 백만/셀")
    lines.append("")
    lines.append("---")
    lines.append("*이 리포트는 `src/parser/gap_report.py`가 자동 생성합니다. "
                 "재실행: `python3 src/parser/gap_report.py`*")

    out.write_text("\n".join(lines), encoding="utf-8")

    # Also export machine-readable JSON summary for future UI widget
    summary = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total_cells": 18*4*3,
        "occupied_cells": sum(1 for v in cube.values() if v["count"]>0),
        "absent_count": len(gaps_absent),
        "under_count": len(gaps_under),
        "fragile_count": len(gaps_fragile),
        "ai_absent": len(ai_gaps),
        "strategy_avg_mil_krw": {s: int(strategy_avg.get(s, 0)) for s, _ in STRATEGIES},
    }
    (PROCESSED / "strategy_gaps.v1.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"[gap_report] wrote {out.relative_to(ROOT)}")
    print(f"  absent: {len(gaps_absent)} / under: {len(gaps_under)} / fragile: {len(gaps_fragile)}")
    print(f"  AI(T01) gaps: {len(ai_gaps)}/12 strategy-track cells")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
