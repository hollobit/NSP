#!/usr/bin/env python3
"""
Ground-truth loader for the 4-domain / 12-task matrix AND the 18-agency list.

Source: 『2026 국가표준시행계획』 p.2 (매트릭스 표) + 목차 (p.2/1)
Rationale: the matrix cell text is split across multiple lines in pdfplumber
output (multi-line table cells with comma-separated ministry lists), making
heuristic parsing brittle. We encode the matrix explicitly with `source.page`
citations so it remains auditable, and write derived JSON for the dashboard.

Outputs:
  data/processed/core_tasks.v1.json  — 13 core tasks under 4 domains
  data/processed/agencies.v1.json    — 18 ministries/agencies with TOC pages
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"

SOURCE = {
    "file": "2026 시행계획.pdf",
    "page": 2,
}

# Canonical agency code map — short tokens that appear in the p.2 matrix.
AGENCIES = [
    # (id, name_full, short, toc_page)
    ("A01", "과학기술정보통신부", "과기부", 1),
    ("A02", "행정안전부",         "행안부", 25),
    ("A03", "문화체육관광부",     "문체부", 35),
    ("A04", "농림축산식품부",     "농림부", 42),
    ("A05", "산업통상부",         "산업부", 51),
    ("A06", "보건복지부",         "복지부", 88),
    ("A07", "기후에너지환경부",   "기후부", 94),
    ("A08", "고용노동부",         "고용부", 112),
    ("A09", "국토교통부",         "국토부", 119),
    ("A10", "해양수산부",         "해수부", 129),
    ("A11", "중소벤처기업부",     "중기부", 135),
    ("A12", "식품의약품안전처",   "식약처", 152),
    ("A13", "지식재산처",         "지재처", 161),
    ("A14", "조달청",             "조달청", 167),
    ("A15", "방위사업청",         "방사청", 173),
    ("A16", "산림청",             "산림청", 187),
    ("A17", "질병관리청",         "질병청", 196),
    ("A18", "기상청",             "기상청", 202),
]

SHORT_TO_ID = {a[2]: a[0] for a in AGENCIES}

DOMAINS = [
    ("D1", "미래 핵심산업 및 AI 기반·융합 표준 선도"),
    ("D2", "국민 체감 표준 인프라 확대"),
    ("D3", "기술규제 대응 및 인증·인정 혁신"),
    ("D4", "혁신적 표준 생태계 조성"),
]

# 4-domain × N-task matrix from p.2.
# sub_no = ①②③④ (as integer)
# agencies = list of SHORT tokens as they appear in the source table
# has_impl_plan: True if the last column shows "O", False if "-"
CORE_TASKS_RAW = [
    # Domain 1 — 4 tasks (①~④)
    ("CT-1-1", "D1", 1, "미래 핵심산업 표준화",
     ["과기부", "산업부", "기후부", "중기부", "방사청"], True),
    ("CT-1-2", "D1", 2, "AI 핵심기반 및 AI 산업융합 표준화",
     ["과기부", "산업부", "기후부", "중기부", "식약처", "방사청"], True),
    ("CT-1-3", "D1", 3, "R&D 성과물의 표준화 확대",
     ["과기부", "산업부", "중기부", "지재처", "방사청"], True),
    ("CT-1-4", "D1", 4, "첨단산업 지원 산업계량 본격화",
     ["산업부"], False),

    # Domain 2 — 3 tasks
    ("CT-2-1", "D2", 1, "안전한 사회 구현을 위한 표준화",
     ["과기부", "산업부", "고용부", "기상청"], True),
    ("CT-2-2", "D2", 2, "국민의 편의와 건강을 위한 표준화",
     ["과기부", "행안부", "문체부", "농림부", "산업부", "복지부",
      "기후부", "국토부", "해수부", "식약처", "조달청", "산림청"], True),
    ("CT-2-3", "D2", 3, "공정한 거래환경 조성을 위한 상거래 확립",
     ["산업부"], False),

    # Domain 3 — 3 tasks
    ("CT-3-1", "D3", 1, "국내외 기술규제 대응체계 구축",
     ["산업부", "기후부", "식약처"], False),
    ("CT-3-2", "D3", 2, "신수요 분야 시험인증서비스 확대",
     ["산업부", "기후부", "중기부"], False),
    ("CT-3-3", "D3", 3, "시험인증 신뢰성 제고 기반 조성",
     ["과기부", "산업부", "기후부", "방사청", "질병청"], True),

    # Domain 4 — 3 tasks
    ("CT-4-1", "D4", 1, "전략적 표준외교 강화",
     ["과기부", "산업부", "식약처"], True),
    ("CT-4-2", "D4", 2, "민간 표준 리더십 활용·확대",
     ["과기부", "산업부", "기후부"], True),
    ("CT-4-3", "D4", 3, "정보·인력 표준 기반 고도화",
     ["과기부", "산업부", "기후부", "중기부"], True),
]


def _is_ai_focus(name: str) -> bool:
    return any(k in name for k in ["AI", "인공지능"])


def build_core_tasks() -> dict:
    tasks = []
    for tid, dom, sub, name, ags, has in CORE_TASKS_RAW:
        tasks.append({
            "id": tid,
            "domain_id": dom,
            "sub_no": sub,
            "name": name,
            "responsible_agency_ids": [
                SHORT_TO_ID[s] for s in ags if s in SHORT_TO_ID
            ],
            "responsible_agency_shorts": ags,
            "has_impl_plan": has,
            "is_ai_focus": _is_ai_focus(name),
            "source": SOURCE,
        })
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": SOURCE,
        "domains": [{"id": d[0], "name": d[1]} for d in DOMAINS],
        "tasks": tasks,
        "stats": {
            "task_count": len(tasks),
            "ai_focus_count": sum(1 for t in tasks if t["is_ai_focus"]),
            "with_impl_plan": sum(1 for t in tasks if t["has_impl_plan"]),
        },
        "note": (
            "제5차 기본계획('21~'25)은 12개 세부과제(기본계획 p.9 회고표 근거), "
            "제6차 기본계획('26~'30)에서 13개로 확대 개편되었다. "
            "다만 시행계획 표제·본문에서는 관행적으로 '12대 중점추진과제' 명칭이 "
            "계속 사용되고 있다. ground truth는 2026 시행계획 p.2 매트릭스."
        ),
        "history": {
            "5th_plan": {"period": "2021-2025", "task_count": 12,
                         "source": "제6차 국가표준기본계획 p.9 제5차 성과 회고"},
            "6th_plan": {"period": "2026-2030", "task_count": 13,
                         "source": "2026 시행계획 p.2 매트릭스"},
            "naming_convention": "'12대'는 5차의 관행이 승계된 표기 — 실제 과제 수와 불일치",
        },
    }


def build_agencies() -> dict:
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": {
            "file": "2026 시행계획.pdf",
            "page": 2,
            "section": "목차",
        },
        "agencies": [
            {
                "id": a_id,
                "name": name,
                "short": short,
                "toc_start_page": toc,
            }
            for a_id, name, short, toc in AGENCIES
        ],
    }


def main() -> int:
    PROCESSED.mkdir(parents=True, exist_ok=True)

    ct = build_core_tasks()
    ag = build_agencies()

    (PROCESSED / "core_tasks.v1.json").write_text(
        json.dumps(ct, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (PROCESSED / "agencies.v1.json").write_text(
        json.dumps(ag, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"[core_tasks] {ct['stats']['task_count']} tasks "
          f"(AI focus: {ct['stats']['ai_focus_count']}, "
          f"impl plan: {ct['stats']['with_impl_plan']})")
    print(f"[agencies]   {len(ag['agencies'])} agencies")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
