"""Unit tests for src/parser/impl_plan.py helpers."""
from __future__ import annotations

import pytest


def test_split_officer_basic():
    from impl_plan import _split_officer
    result = _split_officer("윤성봉 사무관")
    assert result["name"] == "윤성봉"
    assert result["rank"] == "사무관"
    assert result["raw"] == "윤성봉 사무관"


@pytest.mark.parametrize("input_str,name,rank", [
    ("김철수 주무관", "김철수", "주무관"),
    ("이영희 서기관", "이영희", "서기관"),
    ("박민정 연구관", "박민정", "연구관"),
    ("최대리 대리", "최대리", "대리"),   # 성+직급 동형
])
def test_split_officer_various_ranks(input_str, name, rank):
    from impl_plan import _split_officer
    result = _split_officer(input_str)
    assert result["name"] == name
    assert result["rank"] == rank


def test_split_officer_unknown_rank():
    from impl_plan import _split_officer
    result = _split_officer("홍길동")   # 직급 없음
    assert result["name"] == "홍길동"
    assert result["rank"] is None


def test_split_officer_empty():
    from impl_plan import _split_officer
    result = _split_officer("")
    assert result["name"] is None
    assert result["rank"] is None


def test_legal_from_plain_list_conventional():
    """조달청 스타일 — 브래킷 없는 평문 법률 리스트."""
    from impl_plan import legal_from_plain_list
    page = {
        "page": 172,
        "text": """법적근거
ㅇ 국가를 당사자로 하는 계약에 관한 법률, 시행령, 시행규칙
ㅇ 조달사업에 관한 법률, 시행령, 시행규칙
ㅇ 물품 다수공급자계약 업무처리규정
4. 연도별 추진실적 및 계획
"""
    }
    basis = legal_from_plain_list(page)
    laws = [b["law"] for b in basis]
    assert "국가를 당사자로 하는 계약에 관한 법률" in laws
    assert "조달사업에 관한 법률" in laws
    assert "물품 다수공급자계약 업무처리규정" in laws


def test_legal_from_plain_list_skips_bracketed():
    """「」 브래킷 있는 라인은 bracket 파서가 처리 — plain_list는 건너뜀."""
    from impl_plan import legal_from_plain_list
    page = {
        "page": 100,
        "text": """법적근거
ㅇ 「국가표준기본법」 제8조(국가표준시행계획의 수립)
ㅇ 조달사업에 관한 법률
4. 연도별 추진실적
"""
    }
    basis = legal_from_plain_list(page)
    laws = [b["law"] for b in basis]
    # bracketed item should NOT be in plain_list result
    assert "국가표준기본법" not in laws
    assert "조달사업에 관한 법률" in laws
