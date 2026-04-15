#!/usr/bin/env python3
"""
Per-agency metadata extractor for 2026 시행계획:

  - legal_basis[]                : 법적 근거 (3 추출 모드 — 표 / bullet / 브래킷)
  - contact                      : 담당부서·담당자·전화·이메일 (p.5-형 테이블)
  - performance_indicators[]     : 4대 분야 × 지표명 × 2026~2030 계획/실적

Output (MERGED into existing agencies.v1.json).
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

# ── Regex ───────────────────────────────────────────────────────────────────
RE_LAW_BRACKETS = re.compile(r"『([^『』]+?)』|「([^「」]+?)」|｢([^｢｣]+?)｣")
RE_ARTICLE = re.compile(r"제\s*\d+\s*조(?:의\s*\d+)?(?:\s*\([^)]+\))?")
RE_LAW_PLAIN = re.compile(
    r"(?:ㅇ\s*)?([가-힣]+(?:법|규정|훈령|고시|지침|령))\s+(제\s*\d+\s*조(?:의\s*\d+)?\s*\([^)]+\))"
)

# 평문 법률 리스트 항목: "ㅇ 국가를 당사자로 하는 계약에 관한 법률, 시행령, 시행규칙"
# bracket/article 없이 법률명만 나열되는 형태
RE_LAW_PLAIN_LIST = re.compile(
    r"^ㅇ\s*([가-힣A-Za-z0-9·\s]+?(?:법|법률|규정|훈령|고시|지침))"
    r"(?:\s*,\s*(시행령|시행규칙|고시|지침|운영규정)[^.\n]*)*"
    r"\s*$", re.MULTILINE
)
RE_FISCAL_YEAR = re.compile(r"^20\d{2}$")


def build_agency_ranges(agencies: list[dict], total_pages: int) -> list[tuple[int, int, str]]:
    sorted_ag = sorted(agencies, key=lambda a: a["toc_start_page"])
    ranges: list[tuple[int, int, str]] = []
    OFFSET = 2
    for i, a in enumerate(sorted_ag):
        start = a["toc_start_page"] + OFFSET
        if i + 1 < len(sorted_ag):
            end = sorted_ag[i + 1]["toc_start_page"] + OFFSET - 1
        else:
            end = total_pages
        ranges.append((start, end, a["id"]))
    return ranges


# ── Mode 1: table-based legal basis (law in col-0, articles in col-1) ───────
def legal_from_tables(page: dict) -> list[dict]:
    basis: list[dict] = []
    for table in page.get("tables") or []:
        if not table or len(table) < 2:
            continue
        header = [(c or "").strip() for c in table[0]]
        # Header must hint at law table
        is_law_table = any("법률" in h or "법명" in h or "관련 조항" in h for h in header)
        if not is_law_table:
            continue
        for row in table[1:]:
            if not row or len(row) < 2:
                continue
            col0 = (row[0] or "").strip().replace("\n", " ")
            col1 = (row[1] or "").strip().replace("\n", " ")
            # law name usually in col0 with brackets
            laws = [m.group(1) or m.group(2) or m.group(3) for m in RE_LAW_BRACKETS.finditer(col0)]
            if not laws:
                # perhaps bare law name
                m = re.search(r"([가-힣]+법|[가-힣]+에 관한 법률|[가-힣]+규정|[가-힣]+훈령)", col0)
                if m:
                    laws = [m.group(1)]
            articles = RE_ARTICLE.findall(col1 + " " + col0)
            if not laws:
                continue
            for law in laws:
                basis.append({
                    "law": law.strip(),
                    "articles": articles,
                    "source_page": page["page"],
                    "extraction_mode": "table",
                })
    return basis


# ── Mode 3: plain-text law list (no brackets, bullet-only; e.g., 조달청) ───
def legal_from_plain_list(page: dict) -> list[dict]:
    """Extract '국가를 당사자로 하는 계약에 관한 법률, 시행령, 시행규칙' style lines."""
    text = page["text"] or ""
    if "법적근거" not in text:
        return []
    idx = text.find("법적근거")
    section = text[idx:idx + 2000]
    # Stop at next section marker
    for marker in ("연도별 추진", "고유성과지표", "III 12대", "중점 추진과제"):
        m = section.find(marker)
        if m > 0:
            section = section[:m]
    out: list[dict] = []
    for line in section.splitlines():
        s = line.strip()
        if not s.startswith("ㅇ"):
            continue
        body = s.lstrip("ㅇ ").strip()
        # Skip lines that already have brackets (handled by bracket mode)
        if "「" in body or "『" in body or "｢" in body:
            continue
        # Skip lines containing explicit 제N조 (plain article mode handles those)
        if re.search(r"제\s*\d+\s*조", body):
            continue
        # Split by comma to get base + attached docs
        parts = [p.strip() for p in body.split(",")]
        if not parts:
            continue
        main = parts[0]
        # Must end with a law-form suffix to avoid false positives
        if not re.search(r"(법|법률|규정|훈령|고시|지침)$", main):
            continue
        # Minimum length check
        if len(main) < 4:
            continue
        attached = parts[1:] if len(parts) > 1 else []
        out.append({
            "law": main,
            "articles": attached,   # sub-docs treated as "articles" column
            "source_page": page["page"],
            "extraction_mode": "plain_list",
        })
    return out


# ── Mode 2: bullet / bracket / plain text ───────────────────────────────────
def legal_from_text(pages_in_section: list[dict]) -> list[dict]:
    basis: list[dict] = []
    for p in pages_in_section:
        text = p["text"] or ""
        if "법적근거" in text:
            idx = text.find("법적근거")
            text = text[idx:]
        for line in text.splitlines():
            s = line.strip()
            if not s or s in ("법적근거", "3. 법적근거", "4. 법적근거"):
                continue
            # Skip article body text
            if re.match(r"^[①②③④⑤⑥⑦⑧⑨⑩]", s):
                continue
            s_clean = s.lstrip("ㅇ□*- ").strip()

            # Bracketed law
            laws = [m.group(1) or m.group(2) or m.group(3) for m in RE_LAW_BRACKETS.finditer(s_clean)]
            if laws:
                articles = RE_ARTICLE.findall(s_clean)
                for law in laws:
                    basis.append({
                        "law": law.strip(),
                        "articles": articles,
                        "source_page": p["page"],
                        "extraction_mode": "bracket" if "「" in s or "『" in s or "｢" in s else "plain",
                    })
                continue

            # Plain text pattern: "법률명 제N조(...)"
            for m in RE_LAW_PLAIN.finditer(s_clean):
                basis.append({
                    "law": m.group(1).strip(),
                    "articles": [m.group(2).strip()],
                    "source_page": p["page"],
                    "extraction_mode": "plain",
                })
    return basis


def extract_legal_basis_for_agency(pages: list[dict], start: int, end: int) -> list[dict]:
    # Find the page carrying "법적근거" + collect subsequent pages in the block
    in_section = False
    collected: list[dict] = []
    for p in pages:
        if not (start <= p["page"] <= end):
            continue
        text = p["text"] or ""
        if "법적근거" in text and not in_section:
            in_section = True
            collected.append(p)
            continue
        if in_section:
            if any(m in text for m in
                   ["연도별 추진실적", "12대 중점추진과제별",
                    "중점 추진과제별", "고유성과지표", "III 12대"]):
                break
            collected.append(p)
            if len(collected) > 10:
                break

    if not collected:
        return []

    # Explicit "해당 없음" detection
    for p in collected:
        if re.search(r"법적\s*근거\s*[:：]\s*해당\s*없음", p["text"] or ""):
            return [{
                "law": "(해당 없음 — 원문 명시)",
                "articles": [],
                "source_page": p["page"],
                "extraction_mode": "declared_none",
            }]

    basis = legal_from_text(collected)
    # Add table-based extractions from the same pages
    for p in collected:
        basis.extend(legal_from_tables(p))
    # Add plain-text law list (no brackets, no articles — e.g., 조달청 스타일)
    for p in collected:
        basis.extend(legal_from_plain_list(p))

    # Dedup by (law, articles-set)
    merged: dict[str, dict] = {}
    for b in basis:
        key = b["law"]
        if key in merged:
            for a in b["articles"]:
                if a not in merged[key]["articles"]:
                    merged[key]["articles"].append(a)
        else:
            merged[key] = {**b, "articles": list(b["articles"])}
    return list(merged.values())


# ── Contact (담당자) extraction from tables ─────────────────────────────────
CONTACT_KEYS = {
    "담당부서": "department",
    "담 당 자": "officer",
    "담당자":   "officer",
    "전화번호": "phone",
    "전화":     "phone",
    "이메일":   "email",
    "E-mail":   "email",
}


def _split_officer(officer: str) -> dict:
    """Split '윤성봉 사무관' into {name: '윤성봉', rank: '사무관'}.
    Known ranks: 사무관·주무관·서기관·과장·팀장·연구관·연구사·전문관 등."""
    if not officer:
        return {"name": None, "rank": None}
    RANK_WORDS = ("사무관", "주무관", "서기관", "과장", "팀장", "연구관",
                   "연구사", "전문관", "부이사관", "이사관", "국장", "실장",
                   "부장", "차장", "대리", "주임", "연구원", "행정사무관")
    s = officer.strip()
    for rank in sorted(RANK_WORDS, key=len, reverse=True):
        if s.endswith(rank):
            name = s[:-len(rank)].strip()
            return {"name": name or None, "rank": rank, "raw": officer}
        # Also check if rank is a prefix (e.g., "서기관 이형")
        if s.startswith(rank):
            name = s[len(rank):].strip()
            return {"name": name or None, "rank": rank, "raw": officer}
    # No known rank — return as-is
    return {"name": s, "rank": None, "raw": officer}


def extract_contact_for_agency(pages: list[dict], start: int, end: int) -> dict | None:
    for p in pages:
        if not (start <= p["page"] <= min(start + 8, end)):
            continue
        for table in p.get("tables") or []:
            if not table:
                continue
            got: dict[str, str] = {"source_page": str(p["page"])}
            for row in table:
                if not row or len(row) < 2:
                    continue
                k = (row[0] or "").strip()
                v = (row[1] or "").strip().replace("\n", " ")
                if not k or not v:
                    continue
                slot = CONTACT_KEYS.get(k)
                if slot:
                    got[slot] = v
            if any(k in got for k in ("department", "officer", "phone", "email")):
                got["source_page"] = int(got["source_page"])
                # Split officer into name + rank
                if "officer" in got:
                    got["officer_parsed"] = _split_officer(got["officer"])
                return got
    return None


# ── Performance indicators (고유성과지표) ──────────────────────────────────
PI_DOMAIN_HINTS = [
    "미래 핵심", "미래\n핵심", "미래핵심",
    "국민 체감", "국민\n체감", "국민체감",
    "기술규제", "기술\n규제", "기술 규제",
    "혁신적 표준", "혁신적\n표준", "혁신적표준",
]
PI_DOMAIN_CODES = {
    "미래 핵심": "D1",
    "국민 체감": "D2",
    "국민체감": "D2",
    "기술규제": "D3",
    "기술 규제": "D3",
    "혁신적 표준": "D4",
    "혁신적표준": "D4",
}
RE_VALUE_UNIT = re.compile(
    r"^(\d+(?:,\d{3})*(?:\.\d+)?)\s*(개|건|명|회|개사|개월|종|호|%|회차|누적)?$"
)
YEARS = [2026, 2027, 2028, 2029, 2030]


def _parse_plan_value(raw: str) -> dict:
    """Parse a plan cell value into {value, unit, raw, is_numeric}.
    Handles: '335개', '10건', '5,700', '법안 마련', '(제안)', '-', ''."""
    s = raw.strip()
    if not s or s == "-" or s == "_":
        return {"value": None, "unit": None, "raw": None, "is_numeric": False}
    # Remove surrounding parentheses for display: (누적) → 누적
    s_clean = s.strip("()")
    m = RE_VALUE_UNIT.match(s_clean)
    if m:
        num_str, unit = m.groups()
        return {
            "value": float(num_str.replace(",", "")),
            "unit": unit,
            "raw": s,
            "is_numeric": True,
        }
    # Try bare number
    num_only = s_clean.replace(",", "")
    try:
        return {"value": float(num_only), "unit": None, "raw": s, "is_numeric": True}
    except ValueError:
        pass
    # Text value (e.g., "법안 마련", "(제안)")
    return {"value": None, "unit": None, "raw": s, "is_numeric": False}


def _domain_code(domain_text: str | None) -> str | None:
    if not domain_text:
        return None
    for hint, code in PI_DOMAIN_CODES.items():
        if hint in domain_text:
            return code
    return None


def _split_merged_cells(names_cell: str, value_cells: list[str]) -> list[tuple[str, list[str]]]:
    """Split \n-merged PI cells into individual indicators.
    Only splits when ALL non-empty value cells have the SAME \n count > 1,
    confirming actual cell-merge (not just line-wrapped text).

    When the name has more lines than the value count, consecutive name lines
    are grouped (e.g., 10 name lines + 5 value lines → 5 PIs with 2-line names).
    """
    name_lines = [n.strip() for n in names_cell.split("\n") if n.strip()]
    if len(name_lines) <= 1:
        return [(names_cell.replace("\n", " ").strip(), value_cells)]

    # Find consistent value line count across all non-empty value cells
    value_line_counts: list[int] = []
    for vc in value_cells:
        if vc and vc.strip() and vc.strip() != "-":
            vlines = [v.strip() for v in vc.split("\n") if v.strip()]
            value_line_counts.append(len(vlines))

    if not value_line_counts:
        # No non-empty values — treat as single wrapped name
        return [(names_cell.replace("\n", " ").strip(), value_cells)]

    # All non-empty value cells must have the same count
    consistent_count = value_line_counts[0]
    if consistent_count <= 1 or not all(c == consistent_count for c in value_line_counts):
        return [(names_cell.replace("\n", " ").strip(), value_cells)]

    n_pis = consistent_count
    # Group name lines into n_pis groups
    lines_per_pi = len(name_lines) / n_pis
    grouped_names: list[str] = []
    if lines_per_pi == int(lines_per_pi):
        # Even split
        step = int(lines_per_pi)
        for i in range(0, len(name_lines), step):
            grouped_names.append(" ".join(name_lines[i:i + step]))
    else:
        # Uneven — best effort: assign extra lines to earlier groups
        base = len(name_lines) // n_pis
        extra = len(name_lines) % n_pis
        idx = 0
        for g in range(n_pis):
            take = base + (1 if g < extra else 0)
            grouped_names.append(" ".join(name_lines[idx:idx + take]))
            idx += take

    # Ensure we have exactly n_pis names
    while len(grouped_names) < n_pis:
        grouped_names.append("")
    grouped_names = grouped_names[:n_pis]

    # Split values
    split_values: list[list[str]] = []
    for vc in value_cells:
        lines = [v.strip() for v in vc.split("\n")]
        while len(lines) < n_pis:
            lines.append("")
        split_values.append(lines[:n_pis])

    result: list[tuple[str, list[str]]] = []
    for i in range(n_pis):
        vals = [sv[i] for sv in split_values]
        result.append((grouped_names[i], vals))
    return result


def extract_pi_from_text(pages: list[dict], start: int, end: int) -> list[dict]:
    """Fallback: extract 고유성과지표 from raw text using ①~⑳ markers.
    Used when table has no data rows (e.g., 중기부 A11)."""
    CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"
    UNITS = r"(개|건|명|회|개사|개월|종|호|%|회차|누적)"
    out: list[dict] = []
    for p in pages:
        if not (start <= p["page"] <= end):
            continue
        text = p["text"] or ""
        if "고유성과지표" not in text:
            continue
        idx = text.find("고유성과지표")
        section = text[idx:idx + 6000]
        # Stop at next major section
        for marker in ("12대 중점", "III 12", "□ 당해연도"):
            m_idx = section.find(marker)
            if m_idx > 100:
                section = section[:m_idx]
                break
        # Track current domain
        current_domain = None
        # Split by circled numbers
        blocks = re.split(r"(?=[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳])", section)
        for block in blocks:
            block = block.strip()
            if not block or block[0] not in CIRCLED:
                # Check for domain headers in non-circled blocks
                for hint in PI_DOMAIN_HINTS:
                    if hint in block:
                        current_domain = block.strip()
                        break
                continue
            # Collapse whitespace
            flat = " ".join(block.split())
            # Pattern: ① name value unit - value unit - ...
            m = re.match(
                rf"([{CIRCLED}])\s*(.+?)\s+(\d+(?:,\d{{3}})*(?:\.\d+)?)\s*{UNITS}?\s+(.*)",
                flat,
            )
            if not m:
                # Try text-only values (e.g., "(제안)")
                m2 = re.match(rf"([{CIRCLED}])\s*(.+?)$", flat)
                if m2:
                    out.append({
                        "domain": current_domain,
                        "domain_code": _domain_code(current_domain),
                        "name": m2.group(2).strip(),
                        "yearly": [{"year": y, "plan": None, "actual": None} for y in YEARS],
                        "source_page": p["page"],
                        "extraction_mode": "text_fallback",
                    })
                continue
            _, name, first_val, unit, tail = m.groups()
            name = name.strip()
            unit = unit or ""
            # Extract all numeric values from tail
            val_pattern = rf"(\d+(?:,\d{{3}})*(?:\.\d+)?)\s*{UNITS}?"
            tail_vals = re.findall(val_pattern, tail)
            all_vals = [first_val] + [v for v, _ in tail_vals]
            # Build yearly (take first 5 as plan values for 2026-2030)
            yearly: list[dict] = []
            for i, yr in enumerate(YEARS):
                pv = all_vals[i] if i < len(all_vals) else None
                parsed = _parse_plan_value(f"{pv}{unit}" if pv else "")
                yearly.append({
                    "year": yr,
                    "plan": parsed["value"],
                    "plan_raw": parsed["raw"],
                    "plan_unit": parsed["unit"] or unit or None,
                    "actual": None,
                })
            out.append({
                "domain": current_domain,
                "domain_code": _domain_code(current_domain),
                "name": name,
                "yearly": yearly,
                "source_page": p["page"],
                "extraction_mode": "text_fallback",
            })
    return out


def extract_performance_indicators(pages: list[dict], start: int, end: int) -> list[dict]:
    """
    Parse 고유성과지표 tables (12-col standard layout).
    Handles cell-merge contamination by splitting \n-joined values.
    """
    out: list[dict] = []
    for p in pages:
        if not (start <= p["page"] <= end):
            continue
        for table in p.get("tables") or []:
            if not table or len(table) < 3:
                continue
            header_text = " ".join((c or "") for row in table[:3] for c in row)
            if "성과지표" not in header_text:
                continue
            if not re.search(r"20\d{2}", header_text):
                continue
            if "계획" not in header_text or "실적" not in header_text:
                continue

            # Identify year columns from header row
            header_row = [(c or "").strip() for c in table[0]]
            year_cols: list[tuple[int, int]] = []
            for idx, cell in enumerate(header_row):
                m = RE_FISCAL_YEAR.match(cell)
                if m:
                    year_cols.append((int(cell), idx))

            # Data rows: skip first 2 header rows
            current_domain = None
            for row in table[2:]:
                if not row:
                    continue
                cells = [(c or "").strip() for c in row]
                if not any(cells):
                    continue

                # Detect domain column (col 0) — domain names have \n but are NOT PIs
                domain_cell_raw = cells[0]
                domain_text = domain_cell_raw.replace("\n", " ").strip()
                # Also check without any whitespace for fuzzy matching
                domain_no_ws = re.sub(r"\s+", "", domain_cell_raw)
                if (any(h in domain_text for h in PI_DOMAIN_HINTS)
                        or any(re.sub(r"\s+", "", h) in domain_no_ws
                               for h in PI_DOMAIN_HINTS)):
                    current_domain = domain_text
                    name_cell = cells[1] if len(cells) > 1 else ""
                elif not domain_cell_raw.strip():
                    # Empty col 0 — PI name might be in col 1
                    name_cell = cells[1] if len(cells) > 1 else ""
                else:
                    # col 0 might itself be the PI name (no domain in this row)
                    name_cell = domain_cell_raw

                if not name_cell or name_cell.replace("\n", " ").strip() == "성과지표":
                    continue

                # Collect raw value cells (plan + actual for each year)
                plan_cells_raw: list[str] = []
                actual_cells_raw: list[str] = []
                for _, col_idx in year_cols:
                    plan_cells_raw.append(cells[col_idx] if col_idx < len(cells) else "")
                    actual_cells_raw.append(cells[col_idx + 1] if col_idx + 1 < len(cells) else "")

                # Split \n-merged cells (multiple PIs packed in one row)
                split_items = _split_merged_cells(name_cell, plan_cells_raw)
                # Also split actual cells
                _, actual_split = zip(*_split_merged_cells(name_cell, actual_cells_raw)) if split_items else ([], [])
                actual_split = list(actual_split) if actual_split else []

                for idx_s, (pi_name, pi_plan_vals) in enumerate(split_items):
                    pi_name = pi_name.strip()
                    if not pi_name:
                        continue
                    pi_actual_vals = actual_split[idx_s] if idx_s < len(actual_split) else [""] * len(YEARS)

                    yearly: list[dict] = []
                    for i, (yr, _) in enumerate(year_cols):
                        plan_raw = pi_plan_vals[i] if i < len(pi_plan_vals) else ""
                        actual_raw = pi_actual_vals[i] if i < len(pi_actual_vals) else ""
                        p_parsed = _parse_plan_value(plan_raw)
                        a_parsed = _parse_plan_value(actual_raw)
                        yearly.append({
                            "year": yr,
                            "plan": p_parsed["value"],
                            "plan_raw": p_parsed["raw"],
                            "plan_unit": p_parsed["unit"],
                            "actual": a_parsed["value"],
                            "actual_raw": a_parsed["raw"],
                        })
                    # Pad to 5 years
                    existing_years = {y["year"] for y in yearly}
                    for yr in YEARS:
                        if yr not in existing_years:
                            yearly.append({"year": yr, "plan": None, "plan_raw": None,
                                           "plan_unit": None, "actual": None, "actual_raw": None})
                    yearly.sort(key=lambda y: y["year"])
                    out.append({
                        "domain": current_domain,
                        "domain_code": _domain_code(current_domain),
                        "name": pi_name,
                        "yearly": yearly,
                        "source_page": p["page"],
                        "extraction_mode": "table",
                    })
    return out


# ── Main ────────────────────────────────────────────────────────────────────
# ── Hand-encoded overrides for agencies whose PDFs embed 법률 조문 in-line
#     rather than a dedicated 법적근거 section (manual review result).
MANUAL_LEGAL_BASIS_OVERRIDES = {
    # 중기부 A11 — p.140 본문에 「스마트제조혁신 촉진법」과 「중소기업협동조합법」 조항이 직접 인용됨
    # (법적근거 섹션 헤더는 부재하지만 실제 근거 법률은 명확)
    "A11": [
        {"law": "스마트제조혁신 촉진법",
         "articles": ["제11조(스마트공장 수준 확인)", "제12조(제조데이터 활용 지원)",
                      "제17조(표준 보급·확산)", "제23조(국제협력)"],
         "source_page": 140, "extraction_mode": "manual_encoded"},
        {"law": "중소기업협동조합법",
         "articles": ["제37조(단체표준 및 품질인증)", "제38조(단체표준의 검사 등)"],
         "source_page": 140, "extraction_mode": "manual_encoded"},
        {"law": "산업표준화법",
         "articles": ["제27조제1항 (단체표준 제정 근거)"],
         "source_page": 140, "extraction_mode": "manual_encoded"},
    ],
}


def main() -> int:
    pages_doc = json.loads((RAW / "impl_plan.pages.json").read_text(encoding="utf-8"))
    agencies_doc = json.loads((PROCESSED / "agencies.v1.json").read_text(encoding="utf-8"))

    ranges = build_agency_ranges(agencies_doc["agencies"], pages_doc["page_count"])
    range_map = {aid: (s, e) for s, e, aid in ranges}
    pages = pages_doc["pages"]

    totals = {"laws": 0, "contacts": 0, "pi_rows": 0}
    for a in agencies_doc["agencies"]:
        s, e = range_map[a["id"]]
        a["page_range"] = [s, e]
        extracted = extract_legal_basis_for_agency(pages, s, e)
        # Apply manual override when extraction is empty AND override exists
        if not extracted and a["id"] in MANUAL_LEGAL_BASIS_OVERRIDES:
            extracted = MANUAL_LEGAL_BASIS_OVERRIDES[a["id"]]
        a["legal_basis"] = extracted
        a["contact"] = extract_contact_for_agency(pages, s, e)
        pis = extract_performance_indicators(pages, s, e)
        if not pis:
            pis = extract_pi_from_text(pages, s, e)
        a["performance_indicators"] = pis
        totals["laws"] += len(a["legal_basis"])
        totals["contacts"] += 1 if a["contact"] else 0
        totals["pi_rows"] += len(a["performance_indicators"])

    agencies_doc["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (PROCESSED / "agencies.v1.json").write_text(
        json.dumps(agencies_doc, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    with_laws = sum(1 for a in agencies_doc["agencies"] if a["legal_basis"])
    with_pi = sum(1 for a in agencies_doc["agencies"] if a["performance_indicators"])
    print(f"[impl_plan] 18 agencies | "
          f"laws: {totals['laws']} ({with_laws}/18 agencies) | "
          f"contacts: {totals['contacts']}/18 | "
          f"perf_indicators: {totals['pi_rows']} rows ({with_pi}/18 agencies)")
    for a in agencies_doc["agencies"]:
        print(f"  {a['short']:6s} laws={len(a['legal_basis']):2d}  "
              f"contact={'✓' if a['contact'] else '·'}  "
              f"PI={len(a['performance_indicators']):2d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
