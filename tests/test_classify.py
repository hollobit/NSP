"""Unit tests for src/parser/classify.py AI classifier."""
from __future__ import annotations

import pytest


# ── AI relevance ─────────────────────────────────────────────────────────

def test_classify_ai_explicit():
    from classify import classify_ai
    assert classify_ai("AI 핵심기반 표준화") == "explicit"
    assert classify_ai("인공지능 학습 데이터") == "explicit"
    assert classify_ai("생성형 모델 안전성") == "explicit"


def test_classify_ai_implicit():
    from classify import classify_ai
    assert classify_ai("자율주행 표준화 추진") == "implicit"
    assert classify_ai("지능형 로봇 시스템") == "implicit"
    assert classify_ai("스마트시티 인프라") == "implicit"


def test_classify_ai_none():
    from classify import classify_ai
    assert classify_ai("상수도 관리 표준") == "none"
    assert classify_ai("계량법 개정") == "none"


# ── AI direct (순AI) ─────────────────────────────────────────────────────

def test_is_ai_direct_positive():
    from classify import is_ai_direct
    assert is_ai_direct("AI 핵심기반 분야")
    assert is_ai_direct("인공지능 표준 전문연구실")
    assert is_ai_direct("머신러닝 적합성평가")


def test_is_ai_direct_negative_context():
    """AI가 언급되어도 AI 자체 표준화가 아닌 경우는 False."""
    from classify import is_ai_direct
    assert not is_ai_direct("AI 스마트 정수장 국제표준(ISO) 개발")
    assert not is_ai_direct("AI 의료기기 표준화")
    assert not is_ai_direct("AI 친화적 공공데이터")


def test_is_ai_direct_no_ai_mention():
    from classify import is_ai_direct
    assert not is_ai_direct("수도시설 진단 프로세스 표준")
    assert not is_ai_direct("국제표준 리더십 확대")


# ── Tech classification ──────────────────────────────────────────────────

def test_classify_tech_matches_taxonomy():
    from classify import classify_tech
    taxonomy = [
        {"id": "T01", "aliases": ["AI", "인공지능"]},
        {"id": "T06", "aliases": ["반도체", "웨이퍼", "HBM"]},
        {"id": "T09", "aliases": ["로봇", "휴머노이드"]},
    ]
    result = classify_tech("AI 반도체 표준 개발", taxonomy)
    assert set(result) == {"T01", "T06"}


def test_classify_tech_empty_when_no_match():
    from classify import classify_tech
    taxonomy = [{"id": "T01", "aliases": ["AI"]}]
    assert classify_tech("날씨 예보 서비스", taxonomy) == []


# ── AI category 4-layer ──────────────────────────────────────────────────

def test_classify_ai_categories_foundation():
    from classify import classify_ai_categories
    cats = classify_ai_categories("AI 핵심기반 인프라 데이터셋 표준화")
    assert "foundation" in cats


def test_classify_ai_categories_technology():
    from classify import classify_ai_categories
    cats = classify_ai_categories("AI 신뢰·안전성 평가 기준")
    assert "technology" in cats


def test_classify_ai_categories_application():
    from classify import classify_ai_categories
    cats = classify_ai_categories("의료 AI 융합 표준")
    assert "application" in cats


def test_classify_ai_categories_utilization():
    from classify import classify_ai_categories
    cats = classify_ai_categories("AX 전환 지원 인프라")
    assert "utilization" in cats


# ── Std body NER ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("text,expected_name", [
    ("ISO/IEC JTC1/SC42 WG1 참여", "ISO/IEC JTC1/SC42"),
    ("IEEE-P7001 준수", "IEEE P/Std"),
    ("3GPP 기고", "3GPP"),
    ("IETF RFC 6749", "IETF"),
    ("JEDEC 반도체 표준", "JEDEC"),
    ("ASME 원자력 기준", "ASME"),
])
def test_extract_std_engagements_specific_body(text, expected_name):
    from classify import extract_std_engagements
    engagements = extract_std_engagements(text)
    names = [e["body_name"] for e in engagements]
    # Canonical OR partial match (pattern may return longer matched token)
    assert any(expected_name in n or n in expected_name for n in names), \
        f"Expected {expected_name} in {names}"


def test_extract_std_engagements_korean_generic():
    from classify import extract_std_engagements
    engagements = extract_std_engagements(
        "사실상표준화기구 대응 활동을 강화한다")
    assert any("사실상표준화기구" in e["body_name"] for e in engagements)


# ── Strategy inference ───────────────────────────────────────────────────

def test_classify_strategy_all_areas():
    from classify import classify_strategy
    areas, _ = classify_strategy(
        "KOLAS 공인기관 확대 및 국제표준 ISO 제안 전문가 양성",
        engagements=[]
    )
    assert "S-CAB" in areas   # KOLAS
    assert "S-INT" in areas   # ISO, 국제표준
    assert "S-HR" in areas    # 전문가


def test_classify_strategy_track_formal():
    from classify import classify_strategy
    _, track = classify_strategy(
        "ISO 표준 제안",
        engagements=[{"body_type": "formal", "body_level": "org",
                      "body_name": "ISO", "role": "contribute", "snippet": ""}]
    )
    assert track == "formal"


def test_classify_strategy_track_hybrid_via_fast_track():
    from classify import classify_strategy
    _, track = classify_strategy(
        "Fast-Track을 통한 국제표준 승격",
        engagements=[]
    )
    assert track == "hybrid"
