#!/usr/bin/env python3
"""
Extract atomic Projects from 2026 시행계획 PDF pages JSON.

Strategy
--------
1. Load agencies.v1.json → map each page to an agency by TOC start page ranges.
2. Load core_tasks.v1.json → match the in-document "1-① 미래 핵심산업 표준화"
   heading to a CoreTask id (the ①/② glyph often gets lost in extraction, so
   we match by substring on the task name).
3. Scan every page line-by-line:
     - header `N-<name>` (domain-task) updates the current CoreTask context
     - header `사업M <name>` starts a new Project
     - `□ 사업 내용`, `□ 당해연도 사업 추진계획`, `□ 성과지표`,
       `□ 당해연도 예산 현황` switch the current section
4. Emit Project records with:
     - id, agency_id, linked_core_task_id, sequence_no, name
     - description[], subtasks[], kpis[] (raw text lines under each □ header)
     - budget.line_items[] (`<항목>  <금액 백만원>`)
     - source.page_range

This is a **best-effort MVP**: the budget regex is conservative, a few
projects may have missing sections; a follow-up pass will refine.

Output: data/processed/projects.v1.json
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

# ── Regex ───────────────────────────────────────────────────────────────────

# "사업1 제목...", "사업 12 제목..." (with optional space).  Single-line form.
RE_PROJECT_HEADER = re.compile(r"^사업\s*(\d{1,2})\s+(.+?)$")

# Bare "사업N" on its own line (2-line title pattern): the name spans
# surrounding lines. Seen in 행안부 p.34, 식약처 p.162, 조달청 p.173.
RE_PROJECT_HEADER_BARE = re.compile(r"^사업\s*(\d{1,2})\s*$")

# Core-task heading (e.g., "4-① 전략적 표준외교 강화") — used to stop
# backward search for title_part_1.
_CT_HEADER_PREFIX = re.compile(r"^[1-4]\s*[-–]\s*(?:[①-⑨]\s*)?")

# "1-① 미래 핵심산업 표준화"  — the ① often drops out, leaving "1- 제목"
# We match the domain number and then look up by task-name substring.
RE_CT_HEADER = re.compile(r"^([1-4])\s*[-–]\s*(?:[①-⑨]\s*)?(.+?)$")

# Section markers
SEC_DESCRIPTION = "사업 내용"
SEC_SUBTASKS = "당해연도 사업 추진계획"
SEC_KPIS = "성과지표"
SEC_BUDGET = "당해연도 예산 현황"
SEC_MARKERS = {
    SEC_DESCRIPTION: "description",
    SEC_SUBTASKS: "subtasks",
    SEC_KPIS: "kpis",
    SEC_BUDGET: "budget",
}

# Budget line: "<text ...> <amount>" where amount is the trailing number
# (possibly comma-separated thousands, e.g., "5,830" or "12,345").
# Use a single-space-or-more separator and anchor on the trailing number.
RE_BUDGET_LINE = re.compile(r"^(.*?\S)\s+([\d,]{1,13})\s*$")


# ── Helpers ─────────────────────────────────────────────────────────────────

def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_agency_ranges(agencies: list[dict], total_pages: int) -> list[tuple[int, int, str]]:
    """Return [(start_page, end_page, agency_id), ...] sorted."""
    sorted_ag = sorted(agencies, key=lambda a: a["toc_start_page"])
    ranges: list[tuple[int, int, str]] = []
    # Actual PDF pages are TOC-number + offset. The first agency starts at
    # page 3 of the PDF (cover) and its TOC number is 1. Offset = 2.
    # We conservatively add offset=2 so "toc_start_page + 2" ≈ actual PDF page.
    OFFSET = 2
    for i, a in enumerate(sorted_ag):
        start = a["toc_start_page"] + OFFSET
        if i + 1 < len(sorted_ag):
            end = sorted_ag[i + 1]["toc_start_page"] + OFFSET - 1
        else:
            end = total_pages
        ranges.append((start, end, a["id"]))
    return ranges


def agency_for_page(page: int, ranges: list[tuple[int, int, str]]) -> str | None:
    for s, e, aid in ranges:
        if s <= page <= e:
            return aid
    return None


def build_coretask_matcher(tasks: list[dict]) -> list[tuple[str, int, str]]:
    """Return [(ct_id, domain_no, canonical_name), ...] for substring lookup."""
    out = []
    for t in tasks:
        dom_no = int(t["domain_id"][1:])  # "D1" -> 1
        out.append((t["id"], dom_no, t["name"]))
    return out


def match_coretask(line: str, current_dom: int | None,
                   matcher: list[tuple[str, int, str]]) -> str | None:
    m = RE_CT_HEADER.match(line.strip())
    if not m:
        return None
    dom = int(m.group(1))
    label = m.group(2).strip()
    # Try exact/substring match within same domain
    for ct_id, d, name in matcher:
        if d == dom and (name in label or label in name or name[:8] in label):
            return ct_id
    return None


# ── Main extraction ─────────────────────────────────────────────────────────

@dataclass
class Project:
    id: str
    agency_id: str | None
    linked_core_task_id: str | None
    sequence_no: int
    name: str
    start_page: int
    end_page: int = 0
    description: list[str] = field(default_factory=list)
    subtasks: list[str] = field(default_factory=list)
    kpis_raw: list[str] = field(default_factory=list)
    kpis: list[dict] = field(default_factory=list)   # [{name, count, detail, source}]
    budget_lines: list[dict] = field(default_factory=list)
    budget_status: str = "unknown"   # declared|declared_none|unavailable|unknown

    def as_dict(self) -> dict:
        total = sum(b["amount_mil_krw"] for b in self.budget_lines)
        return {
            "id": self.id,
            "agency_id": self.agency_id,
            "linked_core_task_id": self.linked_core_task_id,
            "sequence_no": self.sequence_no,
            "name": self.name,
            "description": self.description,
            "subtasks": self.subtasks,
            "kpis": self.kpis,
            "kpis_raw": self.kpis_raw,
            "budget": {
                "year": 2026,
                "total_mil_krw": total,
                "line_items": self.budget_lines,
                "line_item_count": len(self.budget_lines),
                "status": self.budget_status,
            },
            "source": {
                "file": "2026 시행계획.pdf",
                "page_range": [self.start_page, self.end_page or self.start_page],
            },
        }


def parse_budget_line(line: str) -> dict | None:
    """Parse a single line of the budget table into {name, amount_mil_krw}."""
    # Skip section/header/footer rows
    bad_contains = ["예산(백만원)", "합계", "총계", "(단위", "- "]
    if any(b in line for b in bad_contains):
        return None
    if line.strip().startswith(("구분", "ㅇ", "*", "-")):
        return None
    m = RE_BUDGET_LINE.match(line)
    if not m:
        return None
    name = m.group(1).strip().rstrip("…·․,")
    amount_s = m.group(2).replace(",", "")
    if not amount_s.isdigit():
        return None
    amount = int(amount_s)
    # Sanity: 1 백만원 ≤ amount ≤ 10조 백만원
    if amount < 1 or amount > 10_000_000:
        return None
    # Name should contain Korean/English, not only punctuation
    if len(name) < 3 or not re.search(r"[가-힣A-Za-z]", name):
        return None
    return {"name": name, "amount_mil_krw": amount}


def merge_kpi_tables(pages_doc: dict) -> dict[int, list[dict]]:
    """
    Extract project-level KPI tables: [성과지표 | 건수 | 세부내용] 3-column.

    Returns: page_no → list of {name, count, count_unit, detail, raw}
    """
    out: dict[int, list[dict]] = {}
    for page in pages_doc["pages"]:
        items: list[dict] = []
        for table in page.get("tables") or []:
            if not table or len(table) < 2:
                continue
            header = [(c or "").strip() for c in table[0]]
            # Must be 3-column KPI table
            if len(header) < 3:
                continue
            if "성과지표" not in header[0] or "건수" not in header[1] or "세부내용" not in header[2]:
                continue
            for row in table[1:]:
                if not row or len(row) < 3:
                    continue
                name = (row[0] or "").strip().replace("\n", " ")
                count_raw = (row[1] or "").strip().replace("\n", " ")
                detail = (row[2] or "").strip().replace("\n", " ")
                # Filter stray rows
                if not name or name == "성과지표":
                    continue
                # Parse count into value + unit (e.g., "100개" → 100 + 개)
                m = re.match(r"(\d[\d,]*)\s*([가-힣%]+)?", count_raw)
                count_value = None
                count_unit = None
                if m:
                    try:
                        count_value = int(m.group(1).replace(",", ""))
                    except ValueError:
                        pass
                    count_unit = m.group(2) or None
                items.append({
                    "name": name,
                    "count_value": count_value,
                    "count_unit": count_unit,
                    "count_raw": count_raw,
                    "detail": detail,
                    "source_page": page["page"],
                })
        if items:
            out[page["page"]] = items
    return out


def merge_budget_tables(pages_doc: dict) -> dict[int, list[dict]]:
    """
    For each page, return budget line items extracted from pdfplumber tables
    whose header row is ['구분', '예산(백만원)']. Multi-line cell values are
    flattened (newlines → spaces) so item names stay intact.
    """
    out: dict[int, list[dict]] = {}
    for page in pages_doc["pages"]:
        items: list[dict] = []
        for table in page.get("tables") or []:
            if not table or len(table) < 2:
                continue
            header = [(c or "").strip() for c in table[0]]
            is_budget = (len(header) >= 2
                         and "구분" in header[0]
                         and "예산" in header[1])
            if not is_budget:
                continue
            for row in table[1:]:
                if not row or len(row) < 2:
                    continue
                name = (row[0] or "").strip().replace("\n", " ").replace("  ", " ")
                amt_raw = (row[1] or "").strip().replace(",", "")
                if name in ("구분", "합계", "총계", ""):
                    continue
                # "-" 또는 숫자 아님 → unavailable
                if not amt_raw or not amt_raw.isdigit():
                    continue
                amt = int(amt_raw)
                if amt < 1 or amt > 10_000_000:
                    continue
                items.append({"name": name, "amount_mil_krw": amt})
        if items:
            out[page["page"]] = items
    return out


def extract_projects(pages_doc: dict, agencies: list[dict],
                     core_tasks: list[dict]) -> list[Project]:
    ranges = build_agency_ranges(agencies, pages_doc["page_count"])
    matcher = build_coretask_matcher(core_tasks)
    table_budgets = merge_budget_tables(pages_doc)
    table_kpis = merge_kpi_tables(pages_doc)

    projects: list[Project] = []
    current: Project | None = None
    current_section: str | None = None
    current_ct: str | None = None
    current_domain: int | None = None

    def finalize(p: Project, last_page: int) -> None:
        p.end_page = last_page

    for page in pages_doc["pages"]:
        page_no = page["page"]
        raw_text = page["text"] or ""
        lines = [ln.rstrip() for ln in raw_text.splitlines() if ln.strip()]

        # Detect "예산 현황 : 해당 없음" pattern for the CURRENT project on this page
        declared_none = "해당 없음" in raw_text and "예산 현황" in raw_text
        # Dash budget: "예산(백만원) ... <name> - " (end-of-line or surrounded by spaces)
        has_dash_budget = bool(
            re.search(r"예산\(백만원\).{0,200}?\s-\s", raw_text, re.S)
            or re.search(r"예산\(백만원\).{0,200}?\s-\s*\n", raw_text, re.S)
            or re.search(r"미반영|미편성", raw_text)
        )

        for line_idx, line in enumerate(lines):
            stripped = line.strip()

            # CoreTask heading? (update context only; doesn't finalize project)
            ct_match = match_coretask(stripped, current_domain, matcher)
            if ct_match:
                current_ct = ct_match
                current_domain = int(ct_match.split("-")[1])
                continue

            # Project header — single-line form
            m = RE_PROJECT_HEADER.match(stripped)
            if m:
                if current is not None:
                    finalize(current, page_no - 1 if page_no > current.start_page else page_no)
                seq = int(m.group(1))
                name = m.group(2).strip()
                aid = agency_for_page(page_no, ranges)
                pid = f"P-{aid or 'UNK'}-p{page_no}-s{seq}"
                current = Project(
                    id=pid,
                    agency_id=aid,
                    linked_core_task_id=current_ct,
                    sequence_no=seq,
                    name=name,
                    start_page=page_no,
                )
                current_section = None
                projects.append(current)
                continue

            # Project header — bare form (2-line title)
            mb = RE_PROJECT_HEADER_BARE.match(stripped)
            if mb:
                if current is not None:
                    finalize(current, page_no - 1 if page_no > current.start_page else page_no)
                seq = int(mb.group(1))
                # Reconstruct name from surrounding lines
                title_before = ""
                # Walk backward to find the last non-empty content line that isn't
                # a CT header, section marker, or 사업 keyword itself.
                for j in range(line_idx - 1, max(-1, line_idx - 4), -1):
                    prev = lines[j].strip()
                    if not prev:
                        continue
                    if _CT_HEADER_PREFIX.match(prev) or prev.startswith("□"):
                        break
                    if re.match(r"^사업\s*\d", prev):
                        break
                    title_before = prev
                    break
                # Walk forward until hitting section marker
                title_after_parts = []
                for j in range(line_idx + 1, min(len(lines), line_idx + 5)):
                    nxt = lines[j].strip()
                    if not nxt:
                        continue
                    if nxt.startswith("□") or _CT_HEADER_PREFIX.match(nxt):
                        break
                    title_after_parts.append(nxt)
                    if len(title_after_parts) >= 2:
                        break
                title_after = " ".join(title_after_parts).strip()
                full_name = (title_before + " " + title_after).strip() if title_before else title_after
                if not full_name:
                    continue
                aid = agency_for_page(page_no, ranges)
                pid = f"P-{aid or 'UNK'}-p{page_no}-s{seq}"
                current = Project(
                    id=pid,
                    agency_id=aid,
                    linked_core_task_id=current_ct,
                    sequence_no=seq,
                    name=full_name,
                    start_page=page_no,
                )
                current_section = None
                projects.append(current)
                continue

            # Section marker?
            if stripped.startswith("□"):
                body = stripped.lstrip("□ ").strip()
                matched_section = None
                for key, slot in SEC_MARKERS.items():
                    if body.startswith(key):
                        matched_section = slot
                        break
                current_section = matched_section
                continue

            # Body line (only if inside a project)
            if current is None or current_section is None:
                continue

            if current_section == "description":
                if stripped.startswith(("ㅇ", "*")) or stripped[0] == "-":
                    current.description.append(stripped.lstrip("ㅇ*- ").strip())
                elif current.description:
                    current.description[-1] += " " + stripped
            elif current_section == "subtasks":
                if stripped.startswith(("ㅇ", "*")) or stripped[0] == "-":
                    current.subtasks.append(stripped.lstrip("ㅇ*- ").strip())
                elif current.subtasks:
                    current.subtasks[-1] += " " + stripped
            elif current_section == "kpis":
                current.kpis_raw.append(stripped)
            elif current_section == "budget":
                parsed = parse_budget_line(stripped)
                if parsed:
                    current.budget_lines.append(parsed)

        # Table-based budget merge: prefer tables when present, supplement text results.
        if current is not None:
            if page_no in table_budgets:
                existing = {(b["name"], b["amount_mil_krw"]) for b in current.budget_lines}
                for item in table_budgets[page_no]:
                    key = (item["name"], item["amount_mil_krw"])
                    if key not in existing:
                        current.budget_lines.append(item)
                        existing.add(key)
            # KPI table merge (per-project structured indicators)
            if page_no in table_kpis:
                existing_kpi = {(k["name"], k["count_raw"]) for k in current.kpis}
                for item in table_kpis[page_no]:
                    key = (item["name"], item["count_raw"])
                    if key not in existing_kpi:
                        current.kpis.append(item)
                        existing_kpi.add(key)
            # Track budget declaration status for this page (if within budget section)
            if declared_none and not current.budget_lines:
                current.budget_status = "declared_none"
            elif has_dash_budget and not current.budget_lines:
                current.budget_status = "unavailable"
            elif current.budget_lines and current.budget_status in ("unknown", ""):
                current.budget_status = "declared"
            finalize(current, page_no)

    return projects


def main() -> int:
    pages_doc = load_json(RAW / "impl_plan.pages.json")
    agencies = load_json(PROCESSED / "agencies.v1.json")["agencies"]
    core_tasks = load_json(PROCESSED / "core_tasks.v1.json")["tasks"]

    projects = extract_projects(pages_doc, agencies, core_tasks)

    # Summary stats
    by_agency: dict[str, int] = {}
    with_budget = 0
    total_budget = 0
    with_kpi = 0
    total_kpi = 0
    for p in projects:
        by_agency[p.agency_id or "UNK"] = by_agency.get(p.agency_id or "UNK", 0) + 1
        if p.budget_lines:
            with_budget += 1
            total_budget += sum(b["amount_mil_krw"] for b in p.budget_lines)
        if p.kpis:
            with_kpi += 1
            total_kpi += len(p.kpis)

    out = {
        "schema_version": "0.1",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": {"file": "2026 시행계획.pdf", "extraction": "project_extractor.py MVP"},
        "stats": {
            "project_count": len(projects),
            "projects_with_budget": with_budget,
            "total_budget_mil_krw": total_budget,
            "projects_with_kpi": with_kpi,
            "total_kpi_indicators": total_kpi,
            "by_agency": by_agency,
        },
        "projects": [p.as_dict() for p in projects],
    }
    (PROCESSED / "projects.v1.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[projects] {len(projects)} projects "
          f"({with_budget} with budget, total {total_budget:,} 백만원)")
    print(f"  KPIs: {with_kpi} projects with {total_kpi} indicators")
    print(f"  by agency: {dict(sorted(by_agency.items()))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
