#!/usr/bin/env python3
"""
Encode historical context from 제6차 국가표준기본계획:
  - 5차 12개 세부과제 (p.9 회고표)
  - 5차 성과지표 실적 → 6차 목표 (p.9, p.11)
  - 5차 12개 ↔ 6차 13개 과제 매핑 (best-effort, editorial)

Outputs:
  data/processed/history_5th.v1.json
  data/processed/goal_trajectory.v1.json
  data/processed/task_mapping_5_to_6.v1.json
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"

SOURCE_MASTER_P9 = {"file": "제6차 국가표준기본계획(2026-2030).pdf", "page": 9}
SOURCE_MASTER_P11 = {"file": "제6차 국가표준기본계획(2026-2030).pdf", "page": 11}

# ── 5차 구조: 4개 상위 묶음 × 3 = 12 세부과제 (p.9 회고표 근거) ─────────────
FIFTH_PLAN = {
    "period": "2021-2025",
    "task_count": 12,
    "top_groups": [
        {
            "id": "G5-1", "name": "세계시장 선점을 위한 표준화",
            "tasks": [
                {"id": "T5-1-1", "name": "디지털기술 표준화",
                 "achievement": "AI 데이터 품질 등 국제표준 제안 69건 / 5G 보안 등 ICT 핵심기술 국가기고서 1,468건"},
                {"id": "T5-1-2", "name": "국가유망기술 표준화",
                 "achievement": "탄소섬유 등 소부장 분야 국제표준 27건 / 미래차·반도체 등 첨단산업 156건"},
                {"id": "T5-1-3", "name": "저탄소기술 표준화",
                 "achievement": "수소·태양광·풍력 등 국제표준 19건 / 탄소발자국 검증 인정체계 마련"},
            ],
        },
        {
            "id": "G5-2", "name": "기업 혁신을 지원하는 표준화",
            "tasks": [
                {"id": "T5-2-1", "name": "맞춤형 시험·인증 서비스 확대",
                 "achievement": "NEP(289건)·NET(363건)·GR(702건) 인증 지원 / KOLAS 국제공인기관 1,317개"},
                {"id": "T5-2-2", "name": "국내외 기술규제 애로 해소",
                 "achievement": "해외 기술규제 기업 애로 해소 405건 / 한-미, 한-독, 한-중-일 국제표준협력포럼 개최"},
                {"id": "T5-2-3", "name": "新 측정표준 개발·보급",
                 "achievement": "폐배터리 양극소재·감염병 진단 등 표준물질 503종 / 3차원 광산란·초정밀 절대거리 등 측정표준 550건"},
            ],
        },
        {
            "id": "G5-3", "name": "국민이 행복한 삶을 위한 표준화",
            "tasks": [
                {"id": "T5-3-1", "name": "생활밀착 서비스 표준화",
                 "achievement": "생활편의표준화 아이디어 공모전·고령친화 디자인 등 서비스표준 109종"},
                {"id": "T5-3-2", "name": "사회안전 서비스 표준화",
                 "achievement": "수출 유망 가공식품(김·김치)의 CODEX 표준 개발 / 안전인증·안전확인 취득·유지 170,475건"},
                {"id": "T5-3-3", "name": "공공·민간데이터 표준화",
                 "achievement": "48개 데이터센터 운영·참조표준 84천여종 개발 / 공공데이터 공통표준용어 13,159개"},
            ],
        },
        {
            "id": "G5-4", "name": "혁신 주도형 표준화체계 확립",
            "tasks": [
                {"id": "T5-4-1", "name": "R&D-표준-특허 연계체계 확보",
                 "achievement": "표준화동향조사 680건·전문가컨설팅 156건 / 표준안 반영 특허 475건"},
                {"id": "T5-4-2", "name": "개방형 국가표준체계 확립",
                 "achievement": "민간 표준포럼 22개·ICT 표준포럼/위원회 31개 / 민간 국제표준 공동개발 7개 분야"},
                {"id": "T5-4-3", "name": "기업 중심 표준화 기반구축",
                 "achievement": "이나라표준인증 활용 7,697만건 / 표준융합강좌(4대학)·고위과정 인력양성 541명"},
            ],
        },
    ],
    "source": SOURCE_MASTER_P9,
}

# ── 5차 성과 실적 (p.9) + 6차 목표 (p.11) ─────────────────────────────────
# 5차 목표 대비 실적으로 달성도를 구하고, 6차 목표까지의 증가율을 계산한다.
GOAL_TRAJECTORIES = [
    {
        "id": "GT-ISO-IEC",
        "name": "ISO/IEC 국제표준 제안",
        "unit": "건",
        "fifth": {"baseline_2020": 1073, "target_2025": 1400, "actual_2025": 1514,
                  "achievement_pct": 108.1, "source": SOURCE_MASTER_P9},
        "sixth": {"baseline_2025": 1514, "target_2030": 1950,
                  "source": SOURCE_MASTER_P11},
    },
    {
        "id": "GT-ITU",
        "name": "ITU 기고문 제안",
        "unit": "건",
        "fifth": {"baseline_2020": 7482, "target_2025": 8482, "actual_2025": 8950,
                  "achievement_pct": 105.5, "source": SOURCE_MASTER_P9},
        "sixth": {"baseline_2025": 8950, "target_2030": 10350,
                  "source": SOURCE_MASTER_P11},
    },
    {
        "id": "GT-SVC-STD",
        "name": "서비스표준 개발 (5차) / 국민체감 표준화 (6차)",
        "unit": "건",
        "fifth": {"baseline_2020": 1216, "target_2025": 1316, "actual_2025": 1325,
                  "achievement_pct": 100.5, "source": SOURCE_MASTER_P9,
                  "note": "5차의 '서비스표준 개발'과 6차의 '국민체감 표준화' 지표는 범위가 다르므로 직접 비교 주의"},
        "sixth": {"baseline_2025": 1323, "target_2030": 1410,
                  "source": SOURCE_MASTER_P11},
    },
    {
        "id": "GT-KOLAS",
        "name": "국제공인인증기관 (5차) / 숙련도 시험 참가 (6차)",
        "unit": "개 / 건",
        "fifth": {"baseline_2020": 962, "target_2025": 1100, "actual_2025": 1319,
                  "achievement_pct": 119.9, "source": SOURCE_MASTER_P9,
                  "note": "5차는 기관 수, 6차는 숙련도 시험 참가 건수 — 지표가 달라짐"},
        "sixth": {"baseline_2025": 1793, "target_2030": 2500,
                  "source": SOURCE_MASTER_P11},
    },
    {
        "id": "GT-INFOUSE",
        "name": "표준인증정보 활용 (5차) / 기술규제 애로해소 (6차)",
        "unit": "만건 / 개",
        "fifth": {"baseline_2020": 2200, "target_2025": 4500, "actual_2025": 7697,
                  "achievement_pct": 171.0, "source": SOURCE_MASTER_P9,
                  "note": "단위 '만건' — 6차 애로해소는 별도 지표"},
        "sixth": {"baseline_2025": 399, "target_2030": 1150,
                  "source": SOURCE_MASTER_P11,
                  "note": "6차 신규 지표: 기술규제 애로해소 개수"},
    },
]


def _delta_pct(a: float, b: float) -> float:
    return round((b - a) / a * 100, 1) if a else None


for gt in GOAL_TRAJECTORIES:
    a = gt["fifth"].get("actual_2025")
    b = gt["sixth"].get("target_2030")
    if a and b and gt["id"] in ("GT-ISO-IEC", "GT-ITU"):
        gt["growth_pct_2025_to_2030"] = _delta_pct(a, b)
    else:
        gt["growth_pct_2025_to_2030"] = None  # units/definitions differ


# ── 5차 12개 ↔ 6차 13개 매핑 (editorial, best-effort) ─────────────────────
# confidence: high | medium | low (명칭/범위 유사도 기반 휴리스틱)
TASK_MAPPINGS = [
    # 5차 디지털기술 → 6차 D1-1 미래 핵심산업 & D1-2 AI
    {"fifth_id": "T5-1-1", "sixth_ids": ["CT-1-1", "CT-1-2"], "confidence": "high",
     "rationale": "AI/ICT 국제표준·기고서 실적이 6차 D1-1 미래 핵심산업과 D1-2 AI 과제로 승계·분리"},
    # 5차 국가유망기술 → 6차 D1-1 미래 핵심산업
    {"fifth_id": "T5-1-2", "sixth_ids": ["CT-1-1"], "confidence": "high",
     "rationale": "미래차·반도체 등 첨단산업 표준화 범위가 D1-1에 포괄됨"},
    # 5차 저탄소기술 → 6차 D1-1 (청정에너지 일부) + D3-1 (규제 대응)
    {"fifth_id": "T5-1-3", "sixth_ids": ["CT-1-1", "CT-3-1"], "confidence": "medium",
     "rationale": "수소·재생E 표준화가 D1-1 청정에너지 기술군으로 흡수, 탄소발자국 검증은 D3-1 규제 대응"},
    # 5차 맞춤형 시험인증 → 6차 D3-2, D3-3
    {"fifth_id": "T5-2-1", "sixth_ids": ["CT-3-2", "CT-3-3"], "confidence": "high",
     "rationale": "NEP/NET/KOLAS 연속성 — 신수요 시험인증 확대와 신뢰성 제고로 분화"},
    # 5차 규제애로 → 6차 D3-1
    {"fifth_id": "T5-2-2", "sixth_ids": ["CT-3-1"], "confidence": "high",
     "rationale": "기술규제 대응체계의 직접 승계"},
    # 5차 측정표준 → 6차 D1-4 첨단산업 지원 산업계량
    {"fifth_id": "T5-2-3", "sixth_ids": ["CT-1-4"], "confidence": "high",
     "rationale": "표준물질·측정표준이 산업계량 과제로 재편"},
    # 5차 생활밀착 → 6차 D2-2 편의·건강
    {"fifth_id": "T5-3-1", "sixth_ids": ["CT-2-2"], "confidence": "high",
     "rationale": "생활편의·고령친화 서비스 표준이 D2-2로 재편"},
    # 5차 사회안전 → 6차 D2-1 안전한 사회
    {"fifth_id": "T5-3-2", "sixth_ids": ["CT-2-1"], "confidence": "high",
     "rationale": "안전인증·CODEX 등 사회안전 연속성"},
    # 5차 공공민간데이터 → 6차 D4-3 정보·인력 표준 기반 고도화
    {"fifth_id": "T5-3-3", "sixth_ids": ["CT-4-3"], "confidence": "medium",
     "rationale": "참조표준·공공데이터 인프라가 정보 표준 기반 고도화로 이관"},
    # 5차 R&D-표준-특허 → 6차 D1-3 R&D 성과물 표준화
    {"fifth_id": "T5-4-1", "sixth_ids": ["CT-1-3"], "confidence": "high",
     "rationale": "R&D 연계체계의 직접 승계"},
    # 5차 개방형 국가표준체계 → 6차 D4-2 민간 리더십
    {"fifth_id": "T5-4-2", "sixth_ids": ["CT-4-2"], "confidence": "high",
     "rationale": "민간 표준포럼·국제 공동개발 기조가 민간 리더십 활용·확대로 승계"},
    # 5차 기업중심 표준화 기반 → 6차 D4-3 정보·인력 표준 기반 고도화 (전문인력·정보)
    {"fifth_id": "T5-4-3", "sixth_ids": ["CT-4-3"], "confidence": "high",
     "rationale": "이나라표준인증·인력양성이 D4-3의 정보·인력 기반 고도화로 통합"},
    # 6차 신규: 전략적 표준외교 (CT-4-1) — 5차 분산된 활동의 승급
    {"fifth_id": None, "sixth_ids": ["CT-4-1"], "confidence": "low",
     "rationale": "6차 신설 '전략적 표준외교 강화' — 5차 2-2(규제애로)·4-2(개방형)에서 외교 요소가 독립 과제로 분리·승격"},
]


def main() -> int:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    (PROCESSED / "history_5th.v1.json").write_text(
        json.dumps(
            {"schema_version": "1.0", "generated_at": now, **FIFTH_PLAN},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )

    (PROCESSED / "goal_trajectory.v1.json").write_text(
        json.dumps(
            {"schema_version": "1.0", "generated_at": now,
             "trajectories": GOAL_TRAJECTORIES,
             "note": "5차 실적(2025) ↔ 6차 목표(2030). 일부 지표는 범위 재정의됨 — note 참조"},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )

    (PROCESSED / "task_mapping_5_to_6.v1.json").write_text(
        json.dumps(
            {"schema_version": "1.0", "generated_at": now,
             "mappings": TASK_MAPPINGS,
             "legend": {
                "confidence": {"high": "명칭·범위 직접 승계",
                               "medium": "부분 승계·재분배",
                               "low": "신설/재편"}
             }},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )

    print(f"[history_5th] {len(FIFTH_PLAN['top_groups'])} groups / "
          f"{sum(len(g['tasks']) for g in FIFTH_PLAN['top_groups'])} tasks")
    print(f"[goal_trajectory] {len(GOAL_TRAJECTORIES)} trajectories")
    print(f"[task_mapping] {len(TASK_MAPPINGS)} mappings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
