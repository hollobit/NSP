#!/usr/bin/env python3
"""
Budget trajectory extractor for the 6th National Standards Master Plan.

Reads: data/raw/master_plan.pages.json (page 30, VII. 재정투자 계획)
Maps:  Agency names → A01-A18 IDs from data/processed/agencies.v1.json
Emits: data/processed/budget_trajectory.v1.json

The budget table contains 2026-2030 annual budgets (백만원) for 18 ministries.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

YEARS = ["2026", "2027", "2028", "2029", "2030"]
SOURCE_FILE = "제6차 국가표준기본계획(2026-2030).pdf"
SOURCE_PAGE = 30


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON file with error handling."""
    if not path.exists():
        print(f"ERROR: {path} not found", file=sys.stderr)
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_agency_lookup(agencies_data: dict[str, Any]) -> dict[str, str]:
    """Build a fuzzy lookup: normalised name fragment → agency_id.

    PDF names may differ slightly from agencies.v1.json (e.g. truncation,
    spacing). We normalise by stripping whitespace and use substring matching.
    """
    lookup: dict[str, str] = {}
    for agency in agencies_data["agencies"]:
        aid = agency["id"]
        name = agency["name"]
        short = agency.get("short", "")
        # Store multiple variants for matching
        normalised = re.sub(r"\s+", "", name)
        lookup[normalised] = aid
        if short:
            lookup[re.sub(r"\s+", "", short)] = aid
    return lookup


def match_agency_id(
    name_raw: str,
    lookup: dict[str, str],
) -> str | None:
    """Match a PDF agency name to an agency ID via normalised substring."""
    normalised = re.sub(r"\s+", "", name_raw)
    # Direct match
    if normalised in lookup:
        return lookup[normalised]
    # Substring match (PDF name contained in registry or vice versa)
    for key, aid in lookup.items():
        if key in normalised or normalised in key:
            return aid
    return None


def parse_number(raw: str) -> int | None:
    """Parse a Korean-style number string: remove commas, handle '-' as zero."""
    s = raw.strip()
    if s in ("-", "–", "—", ""):
        return 0
    s = s.replace(",", "").replace(" ", "")
    try:
        return int(s)
    except ValueError:
        return None


def extract_budget_from_text(page_text: str) -> list[dict[str, Any]]:
    """Extract budget rows by parsing the structured text on page 30.

    Each row looks like:
      1. 과학기술정보통신부 127,599 134,410 138,385 142,368 146,361 689,123 46.2
    """
    rows: list[dict[str, Any]] = []

    # Pattern: optional number-dot prefix, agency name, then 7 numeric fields
    # (5 yearly + total + percentage)
    line_pattern = re.compile(
        r"(\d+)\.\s+"                     # row number
        r"(.+?)\s+"                       # agency name (non-greedy)
        r"([\d,]+|[-–—])\s+"             # '26
        r"([\d,]+|[-–—])\s+"             # '27
        r"([\d,]+|[-–—])\s+"             # '28
        r"([\d,]+|[-–—])\s+"             # '29
        r"([\d,]+|[-–—])\s+"             # '30
        r"([\d,]+)\s+"                    # total
        r"([\d.]+)"                       # share %
    )

    for match in line_pattern.finditer(page_text):
        row_no = int(match.group(1))
        name = match.group(2).strip()
        yearly_raw = [match.group(i) for i in range(3, 8)]
        total_raw = match.group(8)
        share_raw = match.group(9)

        yearly = {}
        for year, raw_val in zip(YEARS, yearly_raw):
            val = parse_number(raw_val)
            if val is None:
                print(f"  WARN: Could not parse '{raw_val}' for {name} year {year}", file=sys.stderr)
                val = 0
            yearly[year] = val

        total = parse_number(total_raw)
        share_pct = float(share_raw)

        rows.append({
            "row_no": row_no,
            "name_raw": name,
            "yearly": yearly,
            "total": total if total is not None else sum(yearly.values()),
            "share_pct": share_pct,
        })

    return rows


def extract_totals_from_text(page_text: str) -> dict[str, int]:
    """Extract the 총 계 (grand total) row."""
    pattern = re.compile(
        r"총\s*계\s+"
        r"([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+(\d+)"
    )
    m = pattern.search(page_text)
    if not m:
        return {}
    values = [parse_number(m.group(i)) or 0 for i in range(1, 7)]
    return {
        "2026": values[0],
        "2027": values[1],
        "2028": values[2],
        "2029": values[3],
        "2030": values[4],
        "grand_total": values[5],
    }


def run() -> None:
    """Main extraction pipeline."""
    print("=" * 60)
    print("Budget Trajectory Extractor")
    print("=" * 60)

    # Load inputs
    raw_data = load_json(RAW / "master_plan.pages.json")
    agencies_data = load_json(PROCESSED / "agencies.v1.json")
    agency_lookup = build_agency_lookup(agencies_data)

    # Find page 30
    page_obj = None
    for p in raw_data["pages"]:
        if p["page"] == SOURCE_PAGE:
            page_obj = p
            break

    if page_obj is None:
        print(f"ERROR: Page {SOURCE_PAGE} not found in raw data", file=sys.stderr)
        sys.exit(1)

    page_text = page_obj["text"]

    # Verify we have the right section
    if "재정투자" not in page_text:
        print("WARN: '재정투자' not found in page text — may be wrong page", file=sys.stderr)

    # Extract budget rows from text
    budget_rows = extract_budget_from_text(page_text)
    print(f"\nExtracted {len(budget_rows)} agency budget rows")

    if len(budget_rows) != 18:
        print(f"WARN: Expected 18 agencies, got {len(budget_rows)}", file=sys.stderr)

    # Map to agency IDs
    agencies_out: list[dict[str, Any]] = []
    unmatched: list[str] = []

    for row in budget_rows:
        aid = match_agency_id(row["name_raw"], agency_lookup)
        if aid is None:
            unmatched.append(row["name_raw"])
            aid = f"A{row['row_no']:02d}"  # fallback: derive from row number
            print(f"  WARN: '{row['name_raw']}' unmatched, using fallback {aid}", file=sys.stderr)

        agencies_out.append({
            "agency_id": aid,
            "name": row["name_raw"],
            "yearly": row["yearly"],
            "total": row["total"],
            "share_pct": row["share_pct"],
        })

    # Extract totals
    totals = extract_totals_from_text(page_text)
    if not totals:
        # Compute from rows as fallback
        totals = {
            year: sum(a["yearly"][year] for a in agencies_out)
            for year in YEARS
        }
        totals["grand_total"] = sum(totals.values())
        print("  INFO: Totals computed from row sums (no 총 계 row parsed)")

    # Build output
    output = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "file": SOURCE_FILE,
            "page": SOURCE_PAGE,
        },
        "unit": "백만원",
        "totals": totals,
        "agencies": agencies_out,
    }

    # Write output
    PROCESSED.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED / "budget_trajectory.v1.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nOutput written to {out_path}")

    # Summary stats
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Agencies:     {len(agencies_out)}")
    print(f"  Unmatched:    {len(unmatched)}")
    grand = totals.get("grand_total", 0)
    print(f"  Grand total:  {grand:,} 백만원 ({grand / 1_000_000:.2f}조원)")
    print()

    # Year-by-year totals
    print("  Year-by-year totals:")
    for year in YEARS:
        val = totals.get(year, 0)
        print(f"    {year}: {val:>10,} 백만원")
    print()

    # Top-5 by total budget
    sorted_agencies = sorted(agencies_out, key=lambda a: a["total"], reverse=True)
    print("  Top-5 agencies by total budget:")
    for i, a in enumerate(sorted_agencies[:5], 1):
        print(f"    {i}. {a['name']}: {a['total']:>10,} 백만원 ({a['share_pct']}%)")
    print()

    # Validate: sum of agency totals vs grand total
    agency_sum = sum(a["total"] for a in agencies_out)
    if agency_sum != grand:
        print(f"  WARN: Agency sum ({agency_sum:,}) != Grand total ({grand:,})", file=sys.stderr)
        print(f"        Difference: {abs(agency_sum - grand):,} 백만원", file=sys.stderr)
    else:
        print("  Validation: Agency sum matches grand total ✓")


if __name__ == "__main__":
    run()
