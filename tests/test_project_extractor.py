"""Unit tests for src/parser/project_extractor.py."""
from __future__ import annotations

import pytest


def test_parse_budget_line_simple():
    from project_extractor import parse_budget_line
    result = parse_budget_line("차세대 유망 ICT 표준 개발 5,830")
    assert result == {"name": "차세대 유망 ICT 표준 개발", "amount_mil_krw": 5830}


def test_parse_budget_line_with_parentheses():
    from project_extractor import parse_budget_line
    result = parse_budget_line("ICT 표준 개발(시장수요형, 일부 정책실현형) 2,821")
    assert result is not None
    assert result["amount_mil_krw"] == 2821


def test_parse_budget_line_rejects_header():
    from project_extractor import parse_budget_line
    assert parse_budget_line("구분 예산(백만원)") is None


def test_parse_budget_line_rejects_footer():
    from project_extractor import parse_budget_line
    assert parse_budget_line("- 10 -") is None


def test_parse_budget_line_rejects_zero():
    from project_extractor import parse_budget_line
    assert parse_budget_line("테스트 항목 0") is None


def test_parse_budget_line_rejects_dash():
    from project_extractor import parse_budget_line
    assert parse_budget_line("수도시설 진단 프로세스 표준 개발 -") is None


def test_parse_budget_line_enforces_korean_or_english_name():
    from project_extractor import parse_budget_line
    # Name must contain at least some Korean/English character
    assert parse_budget_line("123 456") is None


@pytest.mark.parametrize("line,expected_amount", [
    ("AI 핵심기반 분야 3,546", 3546),
    ("ICT 국내 표준화 연구 (디지털 혁신 핵심기술) 2,500", 2500),
    ("글로벌 표준 리더십 확대 및 전략적 국제협력 네트워크 구축 1,234", 1234),
])
def test_parse_budget_line_variations(line, expected_amount):
    from project_extractor import parse_budget_line
    result = parse_budget_line(line)
    assert result is not None, f"Failed to parse: {line}"
    assert result["amount_mil_krw"] == expected_amount
