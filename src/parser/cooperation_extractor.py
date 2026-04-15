#!/usr/bin/env python3
"""
Cooperation relationship extractor for 2026 시행계획.

Extracts cooperation relationships (MOU, MRA, bilateral/multilateral agreements,
joint standardization, benchmarking) from agency page ranges.

Each cooperation record links to the nearest project (or agency) and includes
partner classification, cooperation mode, and evidence.

Output: data/processed/cooperations.v1.json
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"


# ── Cooperation keyword patterns ───────────────────────────────────────────

# Country/region bilateral patterns → (regex, partner_name)
BILATERAL_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"한[- ·]미|한미\b|미국|NIST|ANSI|美"), "미국"),
    (re.compile(r"한[- ·]독|한독\b|독일|DIN|DKE|獨|BMWK"), "독일"),
    (re.compile(r"한[- ·]중|한중\b|중국|SAC|中"), "중국"),
    (re.compile(r"한[- ·]일|한일\b|일본|JISC|日"), "일본"),
    (re.compile(r"한[- ·]EU|EU\b|유럽"), "EU"),
    (re.compile(r"영국|英|BSI"), "영국"),
    (re.compile(r"프랑스|佛|AFNOR"), "프랑스"),
    (re.compile(r"캐나다|SCC"), "캐나다"),
    (re.compile(r"호주|SA\b|Standards Australia"), "호주"),
    (re.compile(r"체코|UNMZ"), "체코"),
    (re.compile(r"이태리|이탈리아|UNI\b"), "이탈리아"),
    (re.compile(r"인도\b"), "인도"),
    (re.compile(r"사우디"), "사우디아라비아"),
    (re.compile(r"인니|인도네시아"), "인도네시아"),
]

# Multilateral / international body patterns → partner_name
MULTILATERAL_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"APEC\s*SCSC|APEC"), "APEC"),
    (re.compile(r"아세안|ASEAN|AKSCN"), "ASEAN"),
    (re.compile(r"동북아\s*표준|한[·\s]*중[·\s]*일\s*표준"), "동북아(한중일)"),
    (re.compile(r"ILAC"), "ILAC"),
    (re.compile(r"IAF\b"), "IAF"),
    (re.compile(r"GAC[I]?|글로벌인정협의체"), "GACI"),
    (re.compile(r"IACS|국제선급협회"), "IACS"),
    (re.compile(r"세계표준협력회의"), "세계표준협력회의"),
    (re.compile(r"글로벌\s*사우스"), "글로벌 사우스"),
]

# Cooperation mode detection keywords → mode
MODE_KEYWORDS: dict[str, list[str]] = {
    "mou": ["MOU", "양해각서", "업무협약", "협력협정", "협약 체결", "협약체결", "MOU 체결", "MOU 재체결"],
    "mutual_recognition": ["MRA", "상호인정", "MLA", "mutual recognition"],
    "joint_rd": ["공동 개발", "공동개발", "공동 연구", "공동연구", "공동 표준", "공동표준", "joint"],
    "co_standardization": [
        "공동 대응", "공동대응", "합동", "공동 작업", "공동작업",
        "포럼 개최", "세미나 개최", "워크숍 개최", "교류",
        "국제표준 공동", "표준화 협의체",
    ],
    "benchmarking": ["벤치마킹", "benchmarking", "선진사례", "Best Practice"],
}

# Partner type classification keywords
DOMESTIC_AGENCY_HINTS = [
    "부처간", "부처 간", "다부처", "관계부처", "해수부", "산업부",
    "과기부", "국토부", "고용부", "기후부", "기품원", "정출연",
]
INDUSTRY_HINTS = ["기업", "산업계", "산·학·연", "산학연", "민간", "포럼"]
ACADEMIA_HINTS = ["대학", "연구기관", "연구원", "학회", "학술"]

# Trigger keywords — at least one must match to consider a sentence
TRIGGER_KEYWORDS = [
    "MOU", "MRA", "MLA", "양해각서", "상호인정",
    "국제협력", "협력 추진", "협력추진", "협력 강화", "협력강화",
    "공동 개발", "공동개발", "공동 연구", "공동연구",
    "양자협력", "다자협력", "양자·다자", "양자 협력", "다자 협력",
    "Fast-Track", "Fast Track", "Dual-logo", "Dual logo",
    "한-미", "한-독", "한-중", "한-일", "한-EU",
    "한미", "한독", "한중", "한일",
    "APEC", "ASEAN", "아세안",
    "ILAC", "IAF", "GACI", "글로벌인정협의체",
    "협력협정", "업무협약",
    "세미나 개최", "워크숍 개최", "포럼 개최",
    "공동 표준", "공동표준", "표준 협력", "표준협력",
    "네트워크 강화", "파트너십",
]

# Context window: how many chars around the match to extract as snippet
SNIPPET_RADIUS = 200


def _classify_partner_type(text: str) -> str:
    """Classify partner_type from context text."""
    if any(kw in text for kw in DOMESTIC_AGENCY_HINTS):
        return "domestic_agency"
    for _, name in MULTILATERAL_PATTERNS:
        if name != "GACI":  # GACI is intl_body
            continue
    # Check for foreign NSB / international body
    for pat, _ in BILATERAL_PATTERNS:
        if pat.search(text):
            return "foreign_nsb"
    for pat, _ in MULTILATERAL_PATTERNS:
        if pat.search(text):
            return "intl_body"
    if any(kw in text for kw in ACADEMIA_HINTS):
        return "academia"
    if any(kw in text for kw in INDUSTRY_HINTS):
        return "industry"
    return "intl_body"  # default for cooperation context


def _classify_mode(text: str) -> str:
    """Classify cooperation mode from context text."""
    for mode, keywords in MODE_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return mode
    return "co_standardization"  # default


def _extract_partner_name(text: str) -> str | None:
    """Extract the most specific partner name from text."""
    # Try bilateral first
    for pat, name in BILATERAL_PATTERNS:
        if pat.search(text):
            return name
    # Try multilateral
    for pat, name in MULTILATERAL_PATTERNS:
        if pat.search(text):
            return name
    # Try to find a specific organization name (domestic or known body)
    # Only match longer acronyms to avoid false positives like "MRA", "KS"
    ORG_NAMES = [
        "기품원", "정출연", "국표원", "과학원", "KOLAS", "KRISS",
        "LI4.0", "LNI4.0",
    ]
    for org in ORG_NAMES:
        if org in text:
            return org
    return None


def _find_nearest_project(
    page: int,
    agency_id: str,
    projects: list[dict],
) -> str | None:
    """Find the project whose page_range contains or is nearest to the given page."""
    agency_projects = [p for p in projects if p["agency_id"] == agency_id]
    if not agency_projects:
        return None

    # Exact containment
    for p in agency_projects:
        pr = p.get("source", {}).get("page_range", [])
        if pr and pr[0] <= page <= pr[1]:
            return p["id"]

    # Nearest by distance
    best = None
    best_dist = float("inf")
    for p in agency_projects:
        pr = p.get("source", {}).get("page_range", [])
        if not pr:
            continue
        dist = min(abs(page - pr[0]), abs(page - pr[1]))
        if dist < best_dist:
            best_dist = dist
            best = p["id"]
    return best if best_dist <= 5 else None


def _extract_snippet(text: str, pos: int) -> str:
    """Extract a context snippet around position pos."""
    start = max(0, pos - SNIPPET_RADIUS)
    end = min(len(text), pos + SNIPPET_RADIUS)
    snippet = text[start:end].replace("\n", " ").strip()
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet


def _dedup_cooperations(cooperations: list[dict]) -> list[dict]:
    """Remove near-duplicate cooperation records.

    Dedup key: (agency_id, partner_name, mode, page).
    When duplicates exist, keep the one with the longer description.
    """
    seen: dict[tuple[str, str | None, str, int], dict] = {}
    for c in cooperations:
        key = (
            c.get("agency_id", ""),
            c.get("partner_name"),
            c.get("mode"),
            c["evidence"]["page"],
        )
        existing = seen.get(key)
        if existing is None or len(c.get("description", "")) > len(
            existing.get("description", "")
        ):
            seen[key] = c
    return list(seen.values())


def extract_cooperations(
    pages: list[dict],
    agencies: list[dict],
    projects: list[dict],
) -> list[dict]:
    """Main extraction: scan each agency's page range for cooperation patterns."""
    from impl_plan import build_agency_ranges

    total_pages = max(p["page"] for p in pages)
    ranges = build_agency_ranges(agencies, total_pages)
    range_map: dict[str, tuple[int, int]] = {
        aid: (s, e) for s, e, aid in ranges
    }

    cooperations: list[dict] = []
    coop_id = 0

    for agency in agencies:
        aid = agency["id"]
        start, end = range_map.get(aid, (0, 0))

        for page_data in pages:
            pg = page_data["page"]
            if not (start <= pg <= end):
                continue

            text = page_data.get("text") or ""
            if not text:
                continue

            # Check if page has any trigger keyword
            if not any(kw in text for kw in TRIGGER_KEYWORDS):
                continue

            # Process line by line for finer granularity
            lines = text.split("\n")
            for line_idx, line in enumerate(lines):
                line_clean = line.strip()
                if len(line_clean) < 10:
                    continue

                # Skip table header/data rows that just list "(MRA)" etc.
                if re.match(r"^[\s(MRA)(MLA)기관수\d\s]+$", line_clean):
                    continue

                # Check trigger
                matched_triggers = [
                    kw for kw in TRIGGER_KEYWORDS if kw in line_clean
                ]
                if not matched_triggers:
                    # Also check a window of surrounding lines for context
                    context_window = " ".join(
                        lines[max(0, line_idx - 1) : line_idx + 2]
                    )
                    matched_triggers = [
                        kw for kw in TRIGGER_KEYWORDS if kw in context_window
                    ]
                    if not matched_triggers:
                        continue
                    line_clean = context_window.replace("\n", " ")

                # Build a wider context for classification
                context_start = max(0, line_idx - 2)
                context_end = min(len(lines), line_idx + 3)
                context_block = " ".join(lines[context_start:context_end])

                partner_name = _extract_partner_name(context_block)
                partner_type = _classify_partner_type(context_block)
                mode = _classify_mode(context_block)

                # Skip very generic "협력" mentions without specific partner
                if (
                    partner_name is None
                    and mode == "co_standardization"
                    and not any(
                        kw in line_clean
                        for kw in [
                            "MOU", "MRA", "MLA", "양해각서", "상호인정",
                            "Fast-Track", "Dual-logo", "협력협정", "업무협약",
                        ]
                    )
                ):
                    continue

                project_id = _find_nearest_project(pg, aid, projects)

                # Extract snippet around the first trigger
                first_trigger = matched_triggers[0]
                trigger_pos = line_clean.find(first_trigger)
                snippet = _extract_snippet(
                    line_clean,
                    trigger_pos if trigger_pos >= 0 else len(line_clean) // 2,
                )

                coop_id += 1
                cooperations.append({
                    "id": f"COOP-{coop_id:04d}",
                    "project_id": project_id,
                    "agency_id": aid,
                    "partner_type": partner_type,
                    "partner_name": partner_name,
                    "mode": mode,
                    "description": line_clean[:500],
                    "evidence": {
                        "page": pg,
                        "snippet": snippet[:400],
                    },
                })

    # Dedup
    cooperations = _dedup_cooperations(cooperations)
    # Re-number after dedup
    for i, c in enumerate(cooperations, 1):
        c["id"] = f"COOP-{i:04d}"

    return cooperations


def main() -> int:
    pages_doc = json.loads(
        (RAW / "impl_plan.pages.json").read_text(encoding="utf-8")
    )
    agencies_doc = json.loads(
        (PROCESSED / "agencies.v1.json").read_text(encoding="utf-8")
    )
    projects_doc = json.loads(
        (PROCESSED / "projects.v1.json").read_text(encoding="utf-8")
    )

    cooperations = extract_cooperations(
        pages_doc["pages"],
        agencies_doc["agencies"],
        projects_doc["projects"],
    )

    # Build output
    output = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": {
            "file": "2026 시행계획.pdf",
            "extraction": "cooperation_extractor.py",
        },
        "stats": _build_stats(cooperations),
        "cooperations": cooperations,
    }

    out_path = PROCESSED / "cooperations.v1.json"
    out_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Print summary
    stats = output["stats"]
    print(f"[cooperation_extractor] Total: {stats['total']} cooperation records")
    print(f"  By mode:")
    for mode, count in sorted(stats["by_mode"].items(), key=lambda x: -x[1]):
        print(f"    {mode:25s} {count:3d}")
    print(f"  By partner_type:")
    for pt, count in sorted(
        stats["by_partner_type"].items(), key=lambda x: -x[1]
    ):
        print(f"    {pt:25s} {count:3d}")
    print(f"  By agency (top 10):")
    agency_counts = sorted(
        stats["by_agency"].items(), key=lambda x: -x[1]
    )[:10]
    for aid, count in agency_counts:
        print(f"    {aid:6s} {count:3d}")
    print(f"  With project_id:  {stats['with_project_id']}")
    print(f"  Without project:  {stats['total'] - stats['with_project_id']}")
    print(f"  Unique partners:  {stats['unique_partners']}")
    print(f"\n  Output → {out_path.relative_to(ROOT)}")
    return 0


def _build_stats(cooperations: list[dict]) -> dict:
    """Build summary statistics."""
    by_mode: dict[str, int] = {}
    by_partner_type: dict[str, int] = {}
    by_agency: dict[str, int] = {}
    partners: set[str] = set()
    with_project = 0

    for c in cooperations:
        mode = c["mode"]
        by_mode[mode] = by_mode.get(mode, 0) + 1

        pt = c["partner_type"]
        by_partner_type[pt] = by_partner_type.get(pt, 0) + 1

        aid = c["agency_id"]
        by_agency[aid] = by_agency.get(aid, 0) + 1

        if c.get("partner_name"):
            partners.add(c["partner_name"])

        if c.get("project_id"):
            with_project += 1

    return {
        "total": len(cooperations),
        "by_mode": by_mode,
        "by_partner_type": by_partner_type,
        "by_agency": by_agency,
        "with_project_id": with_project,
        "unique_partners": len(partners),
    }


if __name__ == "__main__":
    raise SystemExit(main())
