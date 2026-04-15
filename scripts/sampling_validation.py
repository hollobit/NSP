#!/usr/bin/env python3
"""
Phase 8.2 / 8.3 — AI·기술 태깅 샘플링 검증 리포트.

Seed-based deterministic random sampling 으로 24건 AI explicit 중 10건,
47건 tech_tagged 중 10건을 추출하여 파서 판정의 근거 스니펫을 제시.
수동 검토를 위한 MD 리포트 생성 (docs/insights/validation.md).

정밀도 계산은 사람의 확인을 전제로 하나, 본 스크립트는 샘플 선정 + 근거 제시까지 수행.
"""
from __future__ import annotations

import json
import random
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
INSIGHTS = ROOT / "docs" / "insights"

SEED = 20260415
SAMPLE_SIZE = 10

AI_EXPLICIT_KEYWORDS = [
    "AI", "인공지능", "생성형", "LLM", "거대언어", "초거대AI",
    "머신러닝", "딥러닝", "피지컬 AI", "에이전틱", "AX",
]


def find_ai_evidence(p: dict) -> list[str]:
    """Return text snippets that triggered the AI explicit tag."""
    haystack = [p.get("name", "")]
    haystack.extend(p.get("description") or [])
    haystack.extend(p.get("subtasks") or [])
    evidence = []
    for line in haystack:
        for kw in AI_EXPLICIT_KEYWORDS:
            if (kw.startswith("AI ") or "AI" not in kw):
                if kw.lower() in line.lower():
                    evidence.append(f"[{kw}] {line[:140]}")
                    break
            elif kw in line:
                evidence.append(f"[{kw}] {line[:140]}")
                break
    return evidence[:3]


def find_tech_evidence(p: dict, tid: str, taxonomy: list[dict]) -> list[str]:
    """Return snippets matching tech aliases."""
    tcat = next((t for t in taxonomy if t["id"] == tid), None)
    if not tcat:
        return []
    aliases = tcat.get("aliases") or []
    haystack = [p.get("name", "")] + (p.get("description") or []) + (p.get("subtasks") or [])
    evidence = []
    lower_aliases = [(a, a.lower()) for a in aliases]
    for line in haystack:
        ll = line.lower()
        for orig, low in lower_aliases:
            if low in ll:
                evidence.append(f"[{orig}] {line[:140]}")
                break
    return evidence[:2]


def main() -> int:
    random.seed(SEED)
    projects = json.loads(
        (PROCESSED / "projects.v1.json").read_text(encoding="utf-8")
    )["projects"]
    taxonomy = json.loads(
        (PROCESSED / "tech_categories.v1.json").read_text(encoding="utf-8")
    )["categories"]

    ai_pool = [p for p in projects if p.get("ai_relevance") == "explicit"]
    tech_pool = [p for p in projects if (p.get("tech_category_ids") or [])]

    ai_sample = random.sample(ai_pool, min(SAMPLE_SIZE, len(ai_pool)))
    tech_sample = random.sample(tech_pool, min(SAMPLE_SIZE, len(tech_pool)))

    INSIGHTS.mkdir(parents=True, exist_ok=True)
    out = INSIGHTS / "validation.md"

    lines = []
    lines.append("# 태깅 검증 샘플링 리포트 (Phase 8.2 / 8.3)\n")
    lines.append(f"생성: {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    lines.append(f"seed: {SEED} (재현 가능)")
    lines.append("")
    lines.append("## 검증 절차")
    lines.append("1. **AI explicit** (24건 모집단) 중 10건 랜덤 추출 → 근거 스니펫 3개 이하 표시")
    lines.append("2. **기술 태깅** (47건 모집단) 중 10건 랜덤 추출 → 각 태그별 매칭 alias + 문맥")
    lines.append("3. 사람이 각 행에 `✓ 정확 / ~ 애매 / ✗ 오탐` 판정 후 정밀도 계산")
    lines.append("")
    lines.append("## 목표 정밀도")
    lines.append("- AI explicit: **≥ 90%**  (10건 중 9건 이상 정확)")
    lines.append("- 기술 태깅:   **≥ 85%**  (태그당 정밀도)")
    lines.append("")
    lines.append("---\n")

    # ── AI explicit sample
    lines.append(f"## ① AI explicit 샘플 ({len(ai_sample)}/{len(ai_pool)})\n")
    lines.append("| # | 판정 | Project ID | 부처 | 사업명 | 근거 스니펫 |")
    lines.append("|---|---|---|---|---|---|")
    for i, p in enumerate(ai_sample, 1):
        evidence = find_ai_evidence(p)
        ev_str = "<br>".join(evidence).replace("|", "\\|") if evidence else "(근거 미발견)"
        name = p.get("name", "")[:35].replace("|", "\\|")
        lines.append(f"| {i} | ☐ | `{p['id']}` | {p.get('agency_id')} | {name} | {ev_str} |")
    lines.append("")

    # ── Tech tagging sample
    lines.append(f"## ② 기술 태깅 샘플 ({len(tech_sample)}/{len(tech_pool)})\n")
    lines.append("| # | Project ID | 부처 | 사업명 | 태그 | 근거 |")
    lines.append("|---|---|---|---|---|---|")
    tnames = {t["id"]: t["name_ko"] for t in taxonomy}
    for i, p in enumerate(tech_sample, 1):
        name = p.get("name", "")[:35].replace("|", "\\|")
        tags = p.get("tech_category_ids") or []
        for tid in tags[:5]:
            ev = find_tech_evidence(p, tid, taxonomy)
            ev_str = "<br>".join(ev).replace("|", "\\|") if ev else "(근거 미발견)"
            lines.append(f"| {i}.{tid} | `{p['id']}` | {p.get('agency_id')} | {name} | "
                         f"{tid} {tnames.get(tid, '')} | {ev_str} |")
    lines.append("")

    # Precision scoring template
    lines.append("## 정밀도 계산 (검토 후)\n")
    lines.append("```")
    lines.append("AI explicit 정밀도 = ✓ 판정 수 / 10")
    lines.append("기술 태깅 정밀도 = (각 태그별 ✓ 판정 수 / 총 태그 수)")
    lines.append("```")
    lines.append("")
    lines.append("## 회귀 방지")
    lines.append("- 이 리포트는 매 주요 파서 변경 후 재실행 권장")
    lines.append("- seed 고정으로 동일 샘플 추출 → diff 가능")
    lines.append("- 실행: `python3 scripts/sampling_validation.py`")
    lines.append("")
    lines.append("---")
    lines.append(f"*Pool: AI explicit {len(ai_pool)} · 기술태깅 {len(tech_pool)}*")

    out.write_text("\n".join(lines), encoding="utf-8")

    # Summary JSON for programmatic use
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed": SEED,
        "ai_explicit_pool": len(ai_pool),
        "ai_explicit_sample_count": len(ai_sample),
        "tech_tagged_pool": len(tech_pool),
        "tech_sample_count": len(tech_sample),
        "samples": {
            "ai_explicit": [{"id": p["id"], "agency_id": p.get("agency_id"),
                             "name": p.get("name")} for p in ai_sample],
            "tech_tagged": [{"id": p["id"], "agency_id": p.get("agency_id"),
                             "name": p.get("name"),
                             "tags": p.get("tech_category_ids")} for p in tech_sample],
        }
    }
    (PROCESSED / "sampling_validation.v1.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"[sampling_validation] wrote {out.relative_to(ROOT)}")
    print(f"  AI explicit: sampled {len(ai_sample)} / pool {len(ai_pool)}")
    print(f"  tech tagged: sampled {len(tech_sample)} / pool {len(tech_pool)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
