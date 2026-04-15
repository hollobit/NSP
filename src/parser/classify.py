#!/usr/bin/env python3
"""
Multi-classifier for extracted projects. Enriches each Project in-place with:
  - tech_category_ids[]  : 18개 기술 taxonomy 멀티라벨
  - ai_relevance         : explicit | implicit | none
  - std_engagements[]    : {std_body_id/name, role, evidence}
  - strategy_areas[]     : S-DOM | S-CAB | S-HR | S-INT (멀티)
  - track_type           : formal | de_facto | hybrid | none

Input:  data/processed/projects.v1.json (raw projects from project_extractor)
        data/processed/tech_categories.v1.json
Output: data/processed/projects.v1.json (in-place enrichment)
        data/processed/std_bodies.v1.json (emerging registry)

This is a **rule/keyword-based MVP**: high precision for explicit mentions,
conservative for implicit. Low-confidence cases are left un-tagged rather
than guessed, to keep the dashboard trustworthy.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"

# ── AI relevance keyword sets ────────────────────────────────────────────────
AI_EXPLICIT = [
    "AI", "인공지능", "생성형", "LLM", "거대언어", "초거대AI",
    "머신러닝", "딥러닝", "피지컬 AI", "에이전틱", "AX",
]
AI_IMPLICIT = [
    "지능형", "자율주행", "자율차", "스마트시티", "디지털트윈",
    "디지털 전환", "스마트제조", "데이터셋", "추론",
]

# ── 순AI 분류: subtask/budget-line 수준에서 "AI 표준화 자체가 직접 대상"인지 판정 ──
# 엄격한 키워드셋 (AI 응용·융합 산업은 제외 — 순수 AI 표준화 활동만)
AI_DIRECT_STRICT = [
    "AI ", "AI(", "AI·", "AI모", "AI표", "AI 기", "AI 데", "AI 모",
    "AI 서", "AI 신", "AI 안", "AI 윤", "AI 인", "AI 융", "AI 전",
    "AI 표", "AI 학", "AI 핵", "AI 혁",
    "인공지능", "생성형 AI", "생성형AI", "머신러닝", "딥러닝",
    "피지컬 AI", "피지컬AI", "에이전틱", "거대언어", "초거대AI",
    "AX(AI", "AX 표", "AX 지원", "AX전환",
    "LLM", "파운데이션 모델", "파운데이션모델",
    "AI 적합", "AI 신뢰", "AI 표준 전",
]
# Negative patterns — AI가 언급되었으나 순AI 표준화 활동이 아닌 케이스
AI_DIRECT_NEGATIVE = [
    "AI 기반 재난",      # 재난 대응 시스템이 주된 목적
    "AI 스마트 정수",    # 정수장 표준화가 주된 목적
    "AI 의료기기",       # 의료기기 표준이 주된 목적
    "AI 친화적 공공",    # 공공데이터가 주된 목적
    "AI 전환 지원",      # AI를 도구로 사용 (수단)
    "AI R&D",           # R&D 체계가 주된 목적
]


def is_ai_direct(text: str) -> bool:
    """
    Fine-grained classifier: is this single line (subtask or budget item)
    about AI standardization *itself* rather than AI-enabled applications?
    """
    if not text:
        return False
    if not any(k.lower() in text.lower() if k.startswith("AI ") or "AI" not in k
               else k in text
               for k in AI_DIRECT_STRICT):
        return False
    for neg in AI_DIRECT_NEGATIVE:
        if neg in text:
            return False
    return True


# ─── 4계층 AI 표준화 분류 체계 (ISO/IEC JTC1/SC42 WG 체계 참고) ─────────────
# F = Foundation (기반):  AI가 작동하는 기반 — 데이터·모델·인프라·플랫폼 표준
# T = Technology (기술):  AI 기술 자체의 규범 — 신뢰성·안전성·평가·거버넌스
# A = Application (응용): 특정 산업·도메인에 AI를 통합 — 의료·제조·국방·자율주행
# U = Utilization (활용): AI를 도구로 사용해 다른 표준화 활동 지원 — AI 기반 시스템 운영·AX 전환

AI_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "foundation": [
        # 인프라·데이터·모델·학습
        "AI 인프라", "AI인프라", "AI 데이터", "AI데이터", "AI 모델", "AI모델",
        "AI 학습", "AI학습", "AI 플랫폼", "AI플랫폼",
        "AI 데이터셋", "데이터셋", "AI 반도체", "AI반도체",
        "파운데이션 모델", "파운데이션모델",
        "AI 핵심기반", "AI핵심기반", "AI 기반 기술",
        "학습·추론", "학습 데이터", "AI 서비스",
        "초연결", "AI 공통기술", "AI공통기술",
    ],
    "technology": [
        # 신뢰·안전·평가·거버넌스·알고리즘
        "AI 신뢰", "AI신뢰", "AI 안전", "AI안전", "AI 윤리", "AI윤리",
        "AI 평가", "AI평가", "성능평가",
        "AI 적합성", "AI 적합성평가", "AI 인증", "AI인증",
        "AI 검증", "AI 시험",
        "AI 거버넌스", "AI거버넌스", "AI 관리",
        "AI 품질", "AI품질", "AI 가이드라인", "AI가이드라인",
        "AI 표준 전문", "AI 표준 기반",
        "머신러닝", "딥러닝", "LLM", "생성형 AI", "생성형AI",
        "위험관리", "책임성",
    ],
    "application": [
        # 산업 도메인 × AI 융합
        "AI 융합", "AI융합", "산업 AI", "산업AI", "산업별 AI",
        "AI 산업융합", "산업융합 AI", "AI 전환",
        "피지컬 AI", "피지컬AI",  # 로봇·자율주행 등 물리적 AI
        "의료 AI", "의료AI", "바이오 AI", "헬스 AI",
        "제조 AI", "제조AI", "스마트제조",
        "국방 AI", "국방AI", "민·군 AI", "민군 AI",
        "자율주행", "자율차",
        "AI 로봇", "로봇 AI", "지능형 로봇",
        "AI 의료기기", "AI 의료",
        "문화 AI", "게임 AI", "AI 에셋",
        "공공 AI", "행정 AI",
        "AI 기반 재난", "AI 스마트",
    ],
    "utilization": [
        # AI를 도구로 활용
        "AX",         # AI 전환 (Transformation) — 수단으로서의 AI
        "AI 활용", "AI활용", "AI 적용", "AI적용", "AI 도입",
        "AI 기반 시스템", "AI 기반 운영",
        "AI 기반 검사", "AI 기반 분석",
        "AI 지원", "AI지원", "AI 연계",
        "AI를 통한", "AI를 이용한", "AI를 활용",
        "AI 친화",  # "AI 친화적 공공데이터" — 데이터를 AI가 쓰기 좋게 만듦
    ],
}


def classify_ai_categories(text: str) -> list[str]:
    """Return list of AI categories matched in text (multi-label)."""
    if not text:
        return []
    hits = []
    for cat, keywords in AI_CATEGORY_KEYWORDS.items():
        if any(k in text for k in keywords):
            hits.append(cat)
    return hits

# ── Standardization body patterns ────────────────────────────────────────────
# Regex → (canonical name, type)
# NOTE: `level` distinguishes organization-level (org) from technical-group-level (tc/sg).
# 'org' = ISO, IEC, ITU, JTC1 등 기관 전체
# 'tc'  = ISO/TC*, IEC/TC*, JTC1/SC*, ITU-T SG* 등 기술위원회·분과위원회 수준
STD_BODY_PATTERNS: list[tuple[re.Pattern[str], str, str, str]] = [
    # ── ISO/IEC JTC1 체계 (기술그룹 레벨) ──
    (re.compile(r"ISO/?IEC\s*(?:JTC\s*)?1/?SC\s*42", re.I), "ISO/IEC JTC1/SC42", "formal", "tc"),
    (re.compile(r"ISO/?IEC\s*(?:JTC\s*)?1/?SC\s*27", re.I), "ISO/IEC JTC1/SC27", "formal", "tc"),
    (re.compile(r"ISO/?IEC\s*(?:JTC\s*)?1/?SC\s*29", re.I), "ISO/IEC JTC1/SC29", "formal", "tc"),
    (re.compile(r"ISO/?IEC\s*(?:JTC\s*)?1/?SC\s*41", re.I), "ISO/IEC JTC1/SC41", "formal", "tc"),
    # JTC1 (org level — 공적 국제표준화 기구의 합동위원회)
    (re.compile(r"ISO/?IEC\s*JTC\s*1(?!/)", re.I),         "ISO/IEC JTC1",      "formal", "org"),
    (re.compile(r"ISO/?IEC\s*JTC\s*3", re.I),              "ISO/IEC JTC3",      "formal", "org"),
    # ── ISO/TC, IEC/TC (기술그룹 레벨) ──
    (re.compile(r"ISO/?TC\s*\d+(?:/SC\s*\d+)?", re.I),     "ISO/TC",            "formal", "tc"),
    (re.compile(r"IEC/?TC\s*\d+(?:/SC\s*\d+)?", re.I),     "IEC/TC",            "formal", "tc"),
    # ── ITU (기술그룹 레벨 vs 기관 레벨) ──
    (re.compile(r"ITU[-‐\s]?T\s*SG\s*\d+", re.I),          "ITU-T SG",          "formal", "tc"),
    (re.compile(r"ITU[-‐\s]?R\s*SG\s*\d+", re.I),          "ITU-R SG",          "formal", "tc"),
    (re.compile(r"ITU[-‐\s]?D", re.I),                     "ITU-D",             "formal", "tc"),
    (re.compile(r"\bITU\b(?!-)", re.I),                    "ITU",               "formal", "org"),
    # ── 공적 기관 (org level) ──
    (re.compile(r"\bETSI\b"),                              "ETSI",              "formal", "org"),
    (re.compile(r"\bCODEX\b"),                             "CODEX",             "formal", "org"),
    (re.compile(r"\bNIST\b"),                              "NIST",              "national", "org"),
    (re.compile(r"\bANSI\b"),                              "ANSI",              "national", "org"),
    (re.compile(r"\bBSI\b"),                               "BSI",               "national", "org"),
    (re.compile(r"\bDIN\b"),                               "DIN",               "national", "org"),
    # ── 사실상 — IEEE 계열 ──
    (re.compile(r"\bIEEE[\s-]?P?\d{3,5}(?:[-./]\d+)?", re.I), "IEEE P/Std",     "de_facto", "tc"),
    (re.compile(r"\bIEEE[-\s]?SA\b", re.I),                "IEEE-SA",           "de_facto", "org"),
    (re.compile(r"\bIEEE\b", re.I),                        "IEEE",              "de_facto", "org"),
    # ── 사실상 — 인터넷 표준 ──
    (re.compile(r"\bIETF\b"),                              "IETF",              "de_facto", "org"),
    (re.compile(r"\bW3C\b"),                               "W3C",               "de_facto", "org"),
    # ── 사실상 — 산업 ──
    (re.compile(r"\b3GPP\b"),                              "3GPP",              "de_facto", "org"),
    (re.compile(r"\bASTM\b"),                              "ASTM",              "de_facto", "org"),
    (re.compile(r"\bSAE\b"),                               "SAE",               "de_facto", "org"),
    # ── 컨소시엄 — AI ──
    (re.compile(r"\bMPAI\b"),                              "MPAI",              "consortium", "org"),
    (re.compile(r"AI\s*Alliance", re.I),                   "AI Alliance",       "consortium", "org"),
    (re.compile(r"Partnership\s*on\s*AI", re.I),           "Partnership on AI", "consortium", "org"),
    (re.compile(r"MLCommons", re.I),                       "MLCommons",         "consortium", "org"),
    (re.compile(r"\bOpenXLA\b", re.I),                     "OpenXLA",           "consortium", "org"),
    # ── 컨소시엄 — 자동차·디스플레이·반도체 ──
    (re.compile(r"\bCOVESA\b"),                            "COVESA",            "consortium", "org"),
    (re.compile(r"\bVESA\b"),                              "VESA",              "consortium", "org"),
    (re.compile(r"\bSEMI\b"),                              "SEMI",              "consortium", "org"),
    (re.compile(r"AUTOSAR", re.I),                         "AUTOSAR",           "consortium", "org"),
    # ── 컨소시엄 — 보안·아이덴티티 ──
    (re.compile(r"\bFIDO\b"),                              "FIDO",              "consortium", "org"),
    (re.compile(r"\bOASIS\b"),                             "OASIS",             "consortium", "org"),
    (re.compile(r"\bOpenID\b"),                            "OpenID",            "consortium", "org"),
    # ── 컨소시엄 — 양자/에너지/IoT ──
    (re.compile(r"\bQuINSA\b", re.I),                      "QuINSA",            "consortium", "org"),
    (re.compile(r"Hydrogen\s*Council", re.I),              "Hydrogen Council",  "consortium", "org"),
    (re.compile(r"\bOGC\b"),                               "OGC",               "consortium", "org"),
    (re.compile(r"\bOCF\b"),                               "OCF",               "consortium", "org"),
    (re.compile(r"OPC\s*Foundation|OPC\s*UA", re.I),       "OPC Foundation",    "consortium", "org"),
    (re.compile(r"\bIIC\b"),                               "IIC",               "consortium", "org"),
    # ── 사실상 — 반도체/디스플레이 상세 ──
    (re.compile(r"\bJEDEC\b", re.I),                       "JEDEC",             "de_facto", "org"),
    (re.compile(r"\bICDM\b", re.I),                        "ICDM",              "de_facto", "org"),
    (re.compile(r"\bSID\b(?=\s*\(|\s*표)", re.I),          "SID",               "de_facto", "org"),
    # ── 사실상 — 원자력·에너지 ──
    (re.compile(r"\bASME\b", re.I),                        "ASME",              "de_facto", "org"),
    (re.compile(r"\bHWC\b"),                               "HWC",               "de_facto", "org"),
    # ── 사실상 — 의료 ──
    (re.compile(r"\bHL7\b"),                               "HL7",               "de_facto", "org"),
    (re.compile(r"\bDICOM\b"),                             "DICOM",             "de_facto", "org"),
    (re.compile(r"\bIHE\b"),                               "IHE",               "de_facto", "org"),
    # ── 사실상 — 해운/항공 ──
    (re.compile(r"\bAPI\b(?=\s*(?:표준|규격|차세대))"),     "API",               "de_facto", "org"),
    # ── 사실상 — 전기안전·제품인증 ──
    (re.compile(r"\bUL\b(?=\s*(?:표준|규격|인증|시험))"),   "UL",                "de_facto", "org"),
    # ── 국가표준기관 — 한국 ──
    (re.compile(r"\bKATS\b"),                              "KATS",              "national", "org"),
    (re.compile(r"국가기술표준원"),                         "KATS",              "national", "org"),
    (re.compile(r"\bKRISS\b"),                             "KRISS",             "national", "org"),
    (re.compile(r"\bKOLAS\b"),                             "KOLAS",             "national", "org"),
    (re.compile(r"\bKAB\b(?=\s*\(|\s*인정)"),              "KAB",               "national", "org"),
    (re.compile(r"한국인정기구"),                           "KAB",               "national", "org"),
    (re.compile(r"\bTTA\b"),                               "TTA",               "national", "org"),
    (re.compile(r"한국통신기술협회|한국정보통신기술협회"),    "TTA",               "national", "org"),
    # ── 국제 공적 기구 — 계량·인정 ──
    (re.compile(r"\bBIPM\b"),                              "BIPM",              "formal", "org"),
    (re.compile(r"국제도량형국"),                           "BIPM",              "formal", "org"),
    (re.compile(r"\bOIML\b"),                              "OIML",              "formal", "org"),
    (re.compile(r"국제법정계량기구"),                       "OIML",              "formal", "org"),
    (re.compile(r"\bILAC\b"),                              "ILAC",              "formal", "org"),
    (re.compile(r"\bIAF\b"),                               "IAF",               "formal", "org"),
    (re.compile(r"\bCIPM\b"),                              "CIPM",              "formal", "org"),
    (re.compile(r"\bCGPM\b"),                              "CGPM",              "formal", "org"),
    # ── 국제 공적 기구 — 통상·무역 ──
    (re.compile(r"\bWTO\b"),                               "WTO",               "formal", "org"),
    (re.compile(r"세계무역기구"),                           "WTO",               "formal", "org"),
    (re.compile(r"\bTBT\b"),                               "TBT",               "formal", "org"),
    # ── 국제 공적 기구 — 기타 UN 계열 ──
    (re.compile(r"\bIMO\b"),                               "IMO",               "formal", "org"),
    (re.compile(r"국제해사기구"),                           "IMO",               "formal", "org"),
    (re.compile(r"\bICAO\b"),                              "ICAO",              "formal", "org"),
    (re.compile(r"국제민간항공기구"),                       "ICAO",              "formal", "org"),
    (re.compile(r"\bIAEA\b"),                              "IAEA",              "formal", "org"),
    (re.compile(r"국제원자력기구"),                         "IAEA",              "formal", "org"),
    (re.compile(r"\bWHO\b"),                               "WHO",               "formal", "org"),
    (re.compile(r"세계보건기구"),                           "WHO",               "formal", "org"),
    (re.compile(r"\bFAO\b"),                               "FAO",               "formal", "org"),
    (re.compile(r"\bWMO\b"),                               "WMO",               "formal", "org"),
    (re.compile(r"세계기상기구"),                           "WMO",               "formal", "org"),
    (re.compile(r"\bUNECE\b"),                             "UNECE",             "formal", "org"),
    (re.compile(r"\bWIPO\b"),                              "WIPO",              "formal", "org"),
    # ── 지역·다자 협력 기구 ──
    (re.compile(r"\bAPEC\b"),                              "APEC",              "formal", "org"),
    (re.compile(r"\bSCSC\b"),                              "APEC SCSC",         "formal", "org"),
    (re.compile(r"\bPASC\b"),                              "PASC",              "formal", "org"),
    (re.compile(r"\bAPMP\b"),                              "APMP",              "formal", "org"),
    (re.compile(r"\bCEN\b(?!/C)"),                         "CEN",               "formal", "org"),
    (re.compile(r"\bCENELEC\b"),                           "CENELEC",           "formal", "org"),
    # ── 사실상 — 전기·전자 추가 ──
    (re.compile(r"\bCSA\b(?=\s*(?:표준|인증|그룹))"),       "CSA Group",         "de_facto", "org"),
    (re.compile(r"\bGS1\b"),                               "GS1",               "consortium", "org"),
    # ── 한글 통칭 매핑 (기관 수준) ──
    (re.compile(r"국제표준화기구(?:\(ISO\))?"),              "ISO",               "formal", "org"),
    (re.compile(r"국제전기기술위원회"),                      "IEC",               "formal", "org"),
    (re.compile(r"국제전기통신연합"),                        "ITU",               "formal", "org"),
    (re.compile(r"국제식품규격위원회"),                      "CODEX",             "formal", "org"),
    # ── Generic ISO/IEC (org level — 마지막 우선순위) ──
    (re.compile(r"\bISO\b(?!/?IEC)", re.I),                "ISO",               "formal", "org"),
    (re.compile(r"\bIEC\b(?!/?TC|/?IEC)", re.I),           "IEC",               "formal", "org"),
]

# ── "사실상표준기구" contextual boost — if the phrase appears near generic org
#     mention, flag track_type hybrid even without explicit de-facto match.
RE_DEFACTO_CONTEXT = re.compile(
    r"(사실상\s*표준|de[-\s]?facto|민간\s*표준|산업\s*표준화\s*기구)"
)

# 한글 통칭 "사실상표준화기구"가 나오면 "generic de_facto" 엔게이지먼트를 추가
# (특정 기구명 없이도 de_facto 참여로 기록)
RE_DEFACTO_GENERIC_MENTION = re.compile(
    r"사실상\s*표준(?:화\s*기구)?\s*(?:대응|참여|활동|기반|로드맵|본격\s*추진)"
)

# ── Std engagement role inference ────────────────────────────────────────────
ROLE_KEYWORDS: list[tuple[str, str]] = [
    ("의장",     "lead"),
    ("간사",     "lead"),
    ("에디터",   "lead"),
    ("editor",   "lead"),
    ("리더십",   "lead"),
    ("주도",     "lead"),
    ("공동",     "contribute"),
    ("제안",     "contribute"),
    ("기고",     "contribute"),
    ("개발",     "contribute"),
    ("참여",     "contribute"),
    ("참가",     "contribute"),
    ("대응",     "monitor"),
    ("분석",     "monitor"),
    ("모니터",   "monitor"),
    ("채택",     "adopt"),
    ("수용",     "adopt"),
    ("준수",     "adopt"),
]

# ── Strategy (4대 영역) keyword sets ─────────────────────────────────────────
STRATEGY_KEYWORDS: dict[str, list[str]] = {
    "S-DOM": [
        "KS", "한국산업표준", "국가표준", "단체표준", "표준 제·개정",
        "표준제정", "표준개정", "KATS",
    ],
    "S-CAB": [
        "KOLAS", "공인기관", "적합성평가", "적합성 평가",
        "시험·인증", "시험인증", "시험 인증", "인정", "ILAC", "IAF", "인증서비스",
    ],
    "S-HR": [
        "전문가", "전문인력", "양성", "교육", "멘토링", "의장",
        "간사", "명장", "자격", "Step-up", "훈련",
    ],
    "S-INT": [
        "ISO", "IEC", "ITU", "국제표준", "기고", "제안", "MOU", "MRA",
        "Fast-Track", "Dual-logo", "사실상표준", "국제협력",
    ],
}

FORMAL_TYPES = {"formal", "national"}
DEFACTO_TYPES = {"de_facto", "consortium"}


# ── Classifiers ─────────────────────────────────────────────────────────────

def project_haystack(p: dict) -> str:
    """Concatenate all searchable text in a project for keyword matching."""
    parts = [p.get("name", "")]
    parts.extend(p.get("description", []) or [])
    parts.extend(p.get("subtasks", []) or [])
    parts.extend(p.get("kpis_raw", []) or [])
    return " ".join(parts)


def classify_ai(text: str) -> str:
    for k in AI_EXPLICIT:
        if k.lower() in text.lower():
            return "explicit"
    for k in AI_IMPLICIT:
        if k in text:
            return "implicit"
    return "none"


def classify_tech(text: str, taxonomy: list[dict]) -> list[str]:
    hits: list[str] = []
    lower = text.lower()
    for t in taxonomy:
        aliases = t.get("aliases") or []
        if any(a and a.lower() in lower for a in aliases):
            hits.append(t["id"])
    return hits


def extract_std_engagements(text: str) -> list[dict]:
    """Find std body mentions and attach a coarse role + level (org|tc).
    Also detects 한글 통칭 '사실상표준화기구' 대응 → generic de_facto engagement."""
    engagements: list[dict] = []
    seen: set[tuple[str, str]] = set()

    sentences = re.split(r"[.。•·;]\s*", text)

    for sent in sentences:
        # Specific body patterns
        for item in STD_BODY_PATTERNS:
            pat, body_name, body_type, level = item
            m = pat.search(sent)
            if not m:
                continue
            matched_token = m.group(0)
            # Use matched_token only for generic TC patterns (ISO/TC*, IEC/TC*)
            # where the match includes the specific TC number;
            # for all other patterns (including Korean names), use body_name.
            if body_name in ("ISO/TC", "IEC/TC", "ITU-T SG", "ITU-R SG") and len(matched_token) > len(body_name):
                canonical = matched_token
            else:
                canonical = body_name
            role = "unknown"
            for kw, r in ROLE_KEYWORDS:
                if kw in sent:
                    role = r
                    break
            key = (canonical, role)
            if key in seen:
                continue
            seen.add(key)
            engagements.append({
                "body_name": canonical,
                "body_type": body_type,
                "body_level": level,
                "role": role,
                "snippet": sent.strip()[:160],
            })

    # Korean generic mention → synthetic de_facto engagement (once per text)
    if RE_DEFACTO_GENERIC_MENTION.search(text):
        # Only add if no specific de_facto/consortium body already matched
        has_specific_defacto = any(e["body_type"] in ("de_facto", "consortium") for e in engagements)
        if not has_specific_defacto:
            snippet_m = RE_DEFACTO_GENERIC_MENTION.search(text)
            engagements.append({
                "body_name": "(사실상표준화기구 통칭)",
                "body_type": "de_facto",
                "body_level": "org",
                "role": "contribute",
                "snippet": text[max(0, snippet_m.start()-40):snippet_m.end()+80].strip()[:160],
            })

    return engagements


def classify_strategy(text: str, engagements: list[dict]) -> tuple[list[str], str]:
    areas: list[str] = []
    for area, keywords in STRATEGY_KEYWORDS.items():
        if any(k in text for k in keywords):
            areas.append(area)

    # Infer track_type from engagements
    types = {e["body_type"] for e in engagements}
    has_defacto_context = bool(RE_DEFACTO_CONTEXT.search(text))

    if types & FORMAL_TYPES and (types & DEFACTO_TYPES or has_defacto_context):
        track = "hybrid"
    elif types & FORMAL_TYPES:
        # If "사실상표준" phrase also present without specific body → upgrade to hybrid
        track = "hybrid" if has_defacto_context else "formal"
    elif types & DEFACTO_TYPES:
        track = "de_facto"
    elif has_defacto_context:
        # "사실상표준기구 대응" 같은 통칭만 있는 경우
        track = "de_facto"
    else:
        track = "none"

    # Fast-Track/Dual-logo explicit → hybrid
    if re.search(r"Fast[- ]?Track|Dual[- ]?logo", text, re.I):
        track = "hybrid"

    return areas, track


def classify_ai_direct_and_categories(p: dict) -> dict:
    """Drill down to subtask/budget line-item level:
       1) compute pure AI standardization budget
       2) assign 4-layer AI categories (foundation/technology/application/utilization)
    Categories are multi-label per item and aggregated to project level."""
    result = _classify_ai_direct_core(p)
    # 4-layer categories — aggregate from name + subtasks + line-item names
    cat_amount = {c: 0 for c in AI_CATEGORY_KEYWORDS.keys()}
    cat_count = {c: 0 for c in AI_CATEGORY_KEYWORDS.keys()}

    subtasks = p.get("subtasks") or []
    lines = (p.get("budget") or {}).get("line_items") or []
    total_budget = int((p.get("budget") or {}).get("total_mil_krw") or 0)

    # Per-subtask category tagging
    subtask_categories = []
    for s in subtasks:
        cats = classify_ai_categories(s)
        subtask_categories.append(cats)
        for c in cats:
            cat_count[c] += 1

    # Project-name categories serve as fallback bucket
    name_cats = classify_ai_categories(p.get("name", ""))

    # Per-line-item category tagging + amount attribution
    # For each AI-direct line, if its own text doesn't match categories,
    # inherit the project-name categories (so AI-direct money always lands
    # in at least one category).
    line_categories = []
    for i, ln in enumerate(lines):
        cats = classify_ai_categories(ln.get("name", ""))
        line_is_ai = result["budget_line_ai_flags"][i] if i < len(result["budget_line_ai_flags"]) else False
        # For non-AI lines with no categories, skip
        # For AI-direct lines without own categories, inherit project-name categories
        effective_cats = cats if cats else (name_cats if line_is_ai else [])
        line_categories.append(effective_cats)
        amt = int(ln.get("amount_mil_krw") or 0)
        if effective_cats and line_is_ai:
            per = amt / len(effective_cats)
            for c in effective_cats:
                cat_amount[c] += per

    # Fallback distribution: use union of project-name + subtask categories,
    # weighted by subtask occurrence counts so subtask-level signals reach
    # budget attribution when line items don't name-match categories.
    if result["ai_direct_fallback_mil_krw"] > 0:
        # Combine signals from project name + subtask counts
        score = {c: 0.0 for c in cat_count}
        # name categories contribute 1 each
        for c in name_cats:
            score[c] += 1
        # subtask counts contribute their frequency
        for c, n in cat_count.items():
            score[c] += n
        total_score = sum(score.values())
        if total_score > 0:
            for c, s in score.items():
                if s > 0:
                    cat_amount[c] += result["ai_direct_fallback_mil_krw"] * (s / total_score)

    result["ai_categories"] = {
        "name_categories": name_cats,
        "subtask_categories": subtask_categories,
        "line_item_categories": line_categories,
        "amounts_mil_krw": {c: int(round(v)) for c, v in cat_amount.items()},
        "subtask_counts": cat_count,
    }
    return result


def _classify_ai_direct_core(p: dict) -> dict:
    """
    Drill down to subtask and budget line-item level to compute the
    *pure* AI standardization portion of a project.

    Output dict:
      subtask_ai_flags : list[bool]   per-subtask AI-direct flag
      budget_line_ai_flags : list[bool]   per-line-item AI-direct flag
      ai_direct_mil_krw : int   sum of AI-direct line item amounts
      ai_direct_fallback_mil_krw : int   estimate when line items are
          non-AI-named but project itself is AI-direct (uses subtask ratio)
      ai_budget_share : float   final AI-direct / total ratio (0..1)
    """
    subtasks = p.get("subtasks") or []
    name = p.get("name") or ""
    name_is_ai = is_ai_direct(name)

    # Subtask-level
    subtask_flags = [is_ai_direct(s) for s in subtasks]
    ai_subtasks = sum(1 for f in subtask_flags if f)

    # Budget line-item level
    budget = p.get("budget") or {}
    lines = budget.get("line_items") or []
    total = int(budget.get("total_mil_krw") or 0)
    line_flags = [is_ai_direct(ln.get("name", "")) for ln in lines]
    ai_line_amount = sum(
        int(ln.get("amount_mil_krw") or 0)
        for ln, f in zip(lines, line_flags) if f
    )

    # Fallback estimation when no line items match but project/subtasks are AI
    ai_direct = ai_line_amount
    fallback = 0
    if ai_direct == 0 and total > 0:
        if name_is_ai and ai_subtasks > 0 and subtasks:
            # Project is AI-direct by name + has AI subtasks: use subtask ratio
            fallback = int(total * ai_subtasks / len(subtasks))
        elif name_is_ai and not subtasks:
            # Project entirely AI-named with no subtask detail: assume all
            fallback = total
        # else: no fallback — project isn't AI-direct at line level

    final = ai_direct + fallback
    share = (final / total) if total > 0 else 0.0

    return {
        "name_is_ai_direct": name_is_ai,
        "subtask_ai_flags": subtask_flags,
        "subtask_ai_count": ai_subtasks,
        "budget_line_ai_flags": line_flags,
        "ai_direct_mil_krw": ai_direct,
        "ai_direct_fallback_mil_krw": fallback,
        "ai_direct_total_mil_krw": final,
        "ai_budget_share": round(share, 4),
    }


def enrich(projects: list[dict], taxonomy: list[dict]) -> dict:
    std_body_registry: dict[str, dict] = {}

    for p in projects:
        text = project_haystack(p)
        p["ai_relevance"] = classify_ai(text)
        p["tech_category_ids"] = classify_tech(text, taxonomy)
        engagements = extract_std_engagements(text)
        p["std_engagements"] = engagements
        areas, track = classify_strategy(text, engagements)
        p["strategy_areas"] = areas
        p["track_type"] = track
        p["ai_direct"] = classify_ai_direct_and_categories(p)
        # Propagate flags to line items for UI access
        lines = p.get("budget", {}).get("line_items") or []
        for i, ln in enumerate(lines):
            if i < len(p["ai_direct"]["budget_line_ai_flags"]):
                ln["is_ai_direct"] = bool(p["ai_direct"]["budget_line_ai_flags"][i])
            line_cats = p["ai_direct"]["ai_categories"]["line_item_categories"]
            if i < len(line_cats):
                ln["ai_categories"] = line_cats[i]

        for e in engagements:
            name = e["body_name"]
            body_id = re.sub(r"[^A-Za-z0-9]", "_", name).strip("_") or name
            if body_id not in std_body_registry:
                std_body_registry[body_id] = {
                    "id": f"SB-{body_id}",
                    "name": name,
                    "type": e["body_type"],
                    "level": e.get("body_level", "org"),
                    "mention_count": 0,
                    "project_ids": [],
                }
            std_body_registry[body_id]["mention_count"] += 1
            pid = p["id"]
            if pid not in std_body_registry[body_id]["project_ids"]:
                std_body_registry[body_id]["project_ids"].append(pid)

    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "bodies": sorted(std_body_registry.values(), key=lambda b: -b["mention_count"]),
    }


def merge_reference_bodies(extracted: dict) -> dict:
    """Merge reference JTC/SC structure into the registry, so the UI can show
    hierarchy even when project text doesn't explicitly mention a body."""
    from std_bodies_reference import all_reference_bodies
    existing = {b["id"]: b for b in extracted["bodies"]}
    for ref in all_reference_bodies():
        if ref["id"] in existing:
            # Enrich with reference metadata but keep extraction stats
            cur = existing[ref["id"]]
            cur.setdefault("level", ref.get("level", "org"))
            cur.setdefault("parent", ref.get("parent"))
            cur.setdefault("scope", ref.get("scope"))
            cur.setdefault("primary_tech_category_ids",
                           ref.get("primary_tech_category_ids", []))
            if "established" in ref:
                cur.setdefault("established", ref["established"])
            if "status" in ref:
                cur.setdefault("status", ref["status"])
        else:
            existing[ref["id"]] = {
                "id": ref["id"],
                "name": ref["name"],
                "type": ref["type"],
                "level": ref["level"],
                "parent": ref.get("parent"),
                "scope": ref.get("scope"),
                "primary_tech_category_ids": ref.get("primary_tech_category_ids", []),
                "mention_count": 0,   # from reference, not extracted
                "project_ids": [],
                "source": "reference",
                **({"established": ref["established"]} if "established" in ref else {}),
                **({"status": ref["status"]} if "status" in ref else {}),
            }
    # Sort: reference JTCs first, then SCs under parent, then extracted
    def sort_key(b):
        lvl_order = {"jtc": 0, "tc": 1, "org": 2}.get(b.get("level", "org"), 3)
        return (lvl_order, b.get("parent") or "", -b["mention_count"], b["name"])
    extracted["bodies"] = sorted(existing.values(), key=sort_key)
    return extracted


def main() -> int:
    projects_doc = json.loads((PROCESSED / "projects.v1.json").read_text(encoding="utf-8"))
    taxonomy = json.loads((PROCESSED / "tech_categories.v1.json").read_text(encoding="utf-8"))

    projects = projects_doc["projects"]
    bodies_doc = enrich(projects, taxonomy["categories"])
    bodies_doc = merge_reference_bodies(bodies_doc)

    # Update stats
    stats = projects_doc.get("stats", {})
    stats["ai_explicit"] = sum(1 for p in projects if p["ai_relevance"] == "explicit")
    stats["ai_implicit"] = sum(1 for p in projects if p["ai_relevance"] == "implicit")
    stats["ai_related"]  = stats["ai_explicit"] + stats["ai_implicit"]
    stats["ai_direct_pure_mil_krw"] = sum(
        p["ai_direct"]["ai_direct_mil_krw"] for p in projects)
    stats["ai_direct_with_fallback_mil_krw"] = sum(
        p["ai_direct"]["ai_direct_total_mil_krw"] for p in projects)
    stats["ai_direct_subtask_count"] = sum(
        p["ai_direct"]["subtask_ai_count"] for p in projects)
    stats["projects_with_ai_direct_budget"] = sum(
        1 for p in projects if p["ai_direct"]["ai_direct_total_mil_krw"] > 0)
    # 4-layer category roll-up
    cat_totals = {c: 0 for c in ("foundation", "technology", "application", "utilization")}
    cat_project_counts = {c: 0 for c in cat_totals}
    for p in projects:
        cats = p["ai_direct"].get("ai_categories", {}).get("amounts_mil_krw", {})
        for c, v in cats.items():
            if v > 0:
                cat_totals[c] += v
        # Count project as belonging to category if any amount OR any subtask tagged
        pcats = p["ai_direct"].get("ai_categories", {}).get("subtask_counts", {})
        nm_cats = p["ai_direct"].get("ai_categories", {}).get("name_categories", [])
        for c in cat_totals:
            if cats.get(c, 0) > 0 or pcats.get(c, 0) > 0 or c in nm_cats:
                cat_project_counts[c] += 1
    stats["ai_category_budgets_mil_krw"] = {c: int(v) for c, v in cat_totals.items()}
    stats["ai_category_project_counts"] = cat_project_counts
    stats["tech_tagged"] = sum(1 for p in projects if p["tech_category_ids"])
    stats["with_std_engagement"] = sum(1 for p in projects if p["std_engagements"])
    stats["track_distribution"] = {
        t: sum(1 for p in projects if p["track_type"] == t)
        for t in ("formal", "de_facto", "hybrid", "none")
    }
    stats["strategy_distribution"] = {
        a: sum(1 for p in projects if a in p["strategy_areas"])
        for a in ("S-DOM", "S-CAB", "S-HR", "S-INT")
    }
    projects_doc["stats"] = stats

    (PROCESSED / "projects.v1.json").write_text(
        json.dumps(projects_doc, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (PROCESSED / "std_bodies.v1.json").write_text(
        json.dumps(bodies_doc, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"[classify] {len(projects)} projects enriched")
    print(f"  AI: explicit={stats['ai_explicit']} implicit={stats['ai_implicit']} "
          f"total AI-related={stats['ai_related']}")
    print(f"  AI 직접 예산 (순수, line-item 기준): "
          f"{stats['ai_direct_pure_mil_krw']:,} 백만 "
          f"({stats['projects_with_ai_direct_budget']} 사업)")
    print(f"  AI 직접 예산 (fallback 포함): "
          f"{stats['ai_direct_with_fallback_mil_krw']:,} 백만")
    print(f"  AI 직접 세부과제: {stats['ai_direct_subtask_count']} 건")
    print(f"  4계층 AI 표준화 예산 분포 (백만):")
    for c, v in stats["ai_category_budgets_mil_krw"].items():
        n = stats["ai_category_project_counts"][c]
        print(f"    {c:12s} {v:>8,} 백만 ({n} 사업)")
    print(f"  tech tagged: {stats['tech_tagged']}")
    print(f"  std engagements: {stats['with_std_engagement']}")
    print(f"  tracks: {stats['track_distribution']}")
    print(f"  strategy: {stats['strategy_distribution']}")
    print(f"  unique std bodies: {len(bodies_doc['bodies'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
