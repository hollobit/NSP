"""
Comprehensive unit tests for NSB parsers.

Covers:
  1. Budget regex (project_extractor, budget_trajectory)
  2. Legal basis patterns (impl_plan)
  3. Standard body NER (classify)
  4. Performance indicator parsing (impl_plan)
  5. AI classification validation (classify + projects.v1.json)
  6. Tech tagging validation (classify + projects.v1.json)
"""
from __future__ import annotations

import re

import pytest


# ═══════════════════════════════════════════════════════════════════════════
# 1. Budget regex tests
# ═══════════════════════════════════════════════════════════════════════════

class TestBudgetRegex:
    """Tests for project_extractor.parse_budget_line and budget_trajectory.parse_number."""

    # ── parse_budget_line ──────────────────────────────────────────────

    def test_simple_amount(self):
        from project_extractor import parse_budget_line
        result = parse_budget_line("차세대 유망 ICT 표준 개발 5,830")
        assert result == {"name": "차세대 유망 ICT 표준 개발", "amount_mil_krw": 5830}

    def test_amount_with_parenthetical(self):
        from project_extractor import parse_budget_line
        result = parse_budget_line("ICT 표준 개발(시장수요형, 일부 정책실현형) 2,821")
        assert result is not None
        assert result["amount_mil_krw"] == 2821

    def test_large_comma_separated(self):
        from project_extractor import parse_budget_line
        result = parse_budget_line("국가표준 체계 고도화 12,345")
        assert result is not None
        assert result["amount_mil_krw"] == 12345

    def test_no_comma_small(self):
        from project_extractor import parse_budget_line
        result = parse_budget_line("소규모 사업 500")
        assert result is not None
        assert result["amount_mil_krw"] == 500

    def test_reject_header_row(self):
        from project_extractor import parse_budget_line
        assert parse_budget_line("구분 예산(백만원)") is None

    def test_reject_footer_dash(self):
        from project_extractor import parse_budget_line
        assert parse_budget_line("- 10 -") is None

    def test_reject_zero_amount(self):
        from project_extractor import parse_budget_line
        assert parse_budget_line("테스트 항목 0") is None

    def test_reject_dash_value(self):
        from project_extractor import parse_budget_line
        assert parse_budget_line("수도시설 진단 프로세스 표준 개발 -") is None

    def test_reject_non_korean_english_name(self):
        from project_extractor import parse_budget_line
        assert parse_budget_line("123 456") is None

    def test_reject_합계(self):
        from project_extractor import parse_budget_line
        assert parse_budget_line("합계 10,000") is None

    def test_reject_총계(self):
        from project_extractor import parse_budget_line
        assert parse_budget_line("총계 20,000") is None

    def test_reject_ㅇ_prefix(self):
        from project_extractor import parse_budget_line
        assert parse_budget_line("ㅇ 비고 내용 100") is None

    @pytest.mark.parametrize("line,expected_amount", [
        ("AI 핵심기반 분야 3,546", 3546),
        ("ICT 국내 표준화 연구 (디지털 혁신 핵심기술) 2,500", 2500),
        ("글로벌 표준 리더십 확대 및 전략적 국제협력 네트워크 구축 1,234", 1234),
        ("English project name 999", 999),
    ])
    def test_various_valid_lines(self, line, expected_amount):
        from project_extractor import parse_budget_line
        result = parse_budget_line(line)
        assert result is not None, f"Failed to parse: {line}"
        assert result["amount_mil_krw"] == expected_amount

    # ── budget_trajectory.parse_number ─────────────────────────────────

    def test_parse_number_with_commas(self):
        from budget_trajectory import parse_number
        assert parse_number("127,599") == 127599

    def test_parse_number_plain(self):
        from budget_trajectory import parse_number
        assert parse_number("5700") == 5700

    def test_parse_number_dash_zero(self):
        from budget_trajectory import parse_number
        assert parse_number("-") == 0
        assert parse_number("–") == 0
        assert parse_number("—") == 0

    def test_parse_number_empty(self):
        from budget_trajectory import parse_number
        assert parse_number("") == 0

    def test_parse_number_spaces(self):
        from budget_trajectory import parse_number
        assert parse_number(" 1,234 ") == 1234

    def test_parse_number_invalid(self):
        from budget_trajectory import parse_number
        assert parse_number("abc") is None


# ═══════════════════════════════════════════════════════════════════════════
# 2. Legal basis pattern tests
# ═══════════════════════════════════════════════════════════════════════════

class TestLegalBasisPatterns:
    """Tests for impl_plan regex patterns and legal extraction functions."""

    # ── RE_LAW_BRACKETS ───────────────────────────────────────────────

    def test_brackets_double_angle(self):
        from impl_plan import RE_LAW_BRACKETS
        m = RE_LAW_BRACKETS.search("「국가표준기본법」 제8조")
        assert m is not None
        assert (m.group(1) or m.group(2) or m.group(3)) == "국가표준기본법"

    def test_brackets_double_angle_alt(self):
        from impl_plan import RE_LAW_BRACKETS
        m = RE_LAW_BRACKETS.search("『산업표준화법』 시행령")
        assert m is not None
        assert (m.group(1) or m.group(2) or m.group(3)) == "산업표준화법"

    def test_brackets_halfwidth(self):
        from impl_plan import RE_LAW_BRACKETS
        m = RE_LAW_BRACKETS.search("｢전기용품안전관리법｣")
        assert m is not None
        assert (m.group(1) or m.group(2) or m.group(3)) == "전기용품안전관리법"

    def test_brackets_multiple_in_line(self):
        from impl_plan import RE_LAW_BRACKETS
        matches = RE_LAW_BRACKETS.findall("「국가표준기본법」 및 「산업표준화법」")
        laws = [m[0] or m[1] or m[2] for m in matches]
        assert "국가표준기본법" in laws
        assert "산업표준화법" in laws

    # ── RE_LAW_PLAIN ──────────────────────────────────────────────────

    def test_plain_law_with_article(self):
        from impl_plan import RE_LAW_PLAIN
        m = RE_LAW_PLAIN.search("국가표준기본법 제8조(국가표준시행계획의 수립)")
        assert m is not None
        assert m.group(1) == "국가표준기본법"
        assert "제8조" in m.group(2)

    def test_plain_law_regulation(self):
        from impl_plan import RE_LAW_PLAIN
        m = RE_LAW_PLAIN.search("ㅇ 전파법시행규정 제10조(전파관련 표준)")
        assert m is not None
        assert "시행규정" in m.group(1)

    # ── RE_LAW_PLAIN_LIST ─────────────────────────────────────────────

    def test_plain_list_simple(self):
        from impl_plan import RE_LAW_PLAIN_LIST
        text = "ㅇ 국가를 당사자로 하는 계약에 관한 법률, 시행령, 시행규칙"
        m = RE_LAW_PLAIN_LIST.search(text)
        assert m is not None
        assert "법률" in m.group(1)

    def test_plain_list_single_law(self):
        from impl_plan import RE_LAW_PLAIN_LIST
        text = "ㅇ 물품 다수공급자계약 업무처리규정"
        m = RE_LAW_PLAIN_LIST.search(text)
        assert m is not None
        assert "규정" in m.group(1)

    # ── legal_from_plain_list function ────────────────────────────────

    def test_legal_from_plain_list_conventional(self):
        from impl_plan import legal_from_plain_list
        page = {
            "page": 172,
            "text": (
                "법적근거\n"
                "ㅇ 국가를 당사자로 하는 계약에 관한 법률, 시행령, 시행규칙\n"
                "ㅇ 조달사업에 관한 법률, 시행령, 시행규칙\n"
                "ㅇ 물품 다수공급자계약 업무처리규정\n"
                "4. 연도별 추진실적 및 계획\n"
            ),
        }
        basis = legal_from_plain_list(page)
        laws = [b["law"] for b in basis]
        assert "국가를 당사자로 하는 계약에 관한 법률" in laws
        assert "조달사업에 관한 법률" in laws
        assert "물품 다수공급자계약 업무처리규정" in laws

    def test_legal_from_plain_list_skips_bracketed(self):
        from impl_plan import legal_from_plain_list
        page = {
            "page": 100,
            "text": (
                "법적근거\n"
                "ㅇ 「국가표준기본법」 제8조(국가표준시행계획의 수립)\n"
                "ㅇ 조달사업에 관한 법률\n"
                "4. 연도별 추진실적\n"
            ),
        }
        basis = legal_from_plain_list(page)
        laws = [b["law"] for b in basis]
        assert "국가표준기본법" not in laws
        assert "조달사업에 관한 법률" in laws

    def test_legal_from_plain_list_no_section(self):
        from impl_plan import legal_from_plain_list
        page = {"page": 50, "text": "추진배경\nㅇ 산업표준화법\n"}
        assert legal_from_plain_list(page) == []


# ═══════════════════════════════════════════════════════════════════════════
# 3. Standard body NER tests
# ═══════════════════════════════════════════════════════════════════════════

class TestStdBodyNER:
    """Tests for classify.extract_std_engagements."""

    @pytest.mark.parametrize("text,expected_name", [
        ("ISO/IEC JTC1/SC42 WG1 참여", "ISO/IEC JTC1/SC42"),
        ("IEEE-P7001 준수", "IEEE P/Std"),
        ("3GPP 기고", "3GPP"),
        ("IETF RFC 6749", "IETF"),
        ("JEDEC 반도체 표준", "JEDEC"),
        ("ASME 원자력 기준", "ASME"),
        ("ITU-T SG13 대응", "ITU-T SG"),
        ("W3C 표준 참여", "W3C"),
        ("ASTM 시험 표준", "ASTM"),
        ("FIDO 인증", "FIDO"),
    ])
    def test_detects_known_bodies(self, text, expected_name):
        from classify import extract_std_engagements
        engagements = extract_std_engagements(text)
        names = [e["body_name"] for e in engagements]
        assert any(
            expected_name in n or n in expected_name for n in names
        ), f"Expected '{expected_name}' in {names} for text: '{text}'"

    def test_iso_detected(self):
        from classify import extract_std_engagements
        engagements = extract_std_engagements("ISO 표준 제안")
        assert any(e["body_type"] == "formal" for e in engagements)

    def test_iec_detected(self):
        from classify import extract_std_engagements
        engagements = extract_std_engagements("IEC 국제표준 대응")
        assert any("IEC" in e["body_name"] for e in engagements)

    def test_itu_detected(self):
        from classify import extract_std_engagements
        engagements = extract_std_engagements("ITU 기고문 제출")
        assert any("ITU" in e["body_name"] for e in engagements)

    def test_defacto_generic_mention(self):
        from classify import extract_std_engagements
        engagements = extract_std_engagements(
            "사실상표준화기구 대응 활동을 강화한다"
        )
        assert any("사실상표준화기구" in e["body_name"] for e in engagements)

    def test_role_inference_lead(self):
        from classify import extract_std_engagements
        engagements = extract_std_engagements("ISO/TC20 의장 활동")
        roles = [e["role"] for e in engagements]
        assert "lead" in roles

    def test_role_inference_contribute(self):
        from classify import extract_std_engagements
        engagements = extract_std_engagements("ITU 기고문 제안")
        roles = [e["role"] for e in engagements]
        assert "contribute" in roles

    def test_no_match_plain_text(self):
        from classify import extract_std_engagements
        engagements = extract_std_engagements("상수도 관리 표준 연구")
        # Should not match any body (no org acronym present)
        assert len(engagements) == 0

    def test_body_type_classification(self):
        from classify import extract_std_engagements
        eng_iso = extract_std_engagements("ISO 표준 참여")
        eng_ieee = extract_std_engagements("IEEE 표준 참여")
        assert any(e["body_type"] == "formal" for e in eng_iso)
        assert any(e["body_type"] == "de_facto" for e in eng_ieee)

    def test_consortium_bodies(self):
        from classify import extract_std_engagements
        for body in ["MPAI", "COVESA", "VESA", "SEMI"]:
            engagements = extract_std_engagements(f"{body} 참여")
            assert any(
                e["body_type"] == "consortium" for e in engagements
            ), f"{body} should be consortium"


# ═══════════════════════════════════════════════════════════════════════════
# 4. Performance indicator parsing tests
# ═══════════════════════════════════════════════════════════════════════════

class TestPerformanceIndicatorParsing:
    """Tests for impl_plan helper functions for PI extraction."""

    # ── _parse_plan_value ─────────────────────────────────────────────

    def test_parse_plan_value_with_unit(self):
        from impl_plan import _parse_plan_value
        result = _parse_plan_value("335개")
        assert result["value"] == 335
        assert result["unit"] == "개"
        assert result["is_numeric"] is True

    def test_parse_plan_value_건(self):
        from impl_plan import _parse_plan_value
        result = _parse_plan_value("10건")
        assert result["value"] == 10
        assert result["unit"] == "건"
        assert result["is_numeric"] is True

    def test_parse_plan_value_comma_number(self):
        from impl_plan import _parse_plan_value
        result = _parse_plan_value("5,700")
        assert result["value"] == 5700
        assert result["is_numeric"] is True

    def test_parse_plan_value_text(self):
        from impl_plan import _parse_plan_value
        result = _parse_plan_value("법안 마련")
        assert result["value"] is None
        assert result["is_numeric"] is False
        assert result["raw"] == "법안 마련"

    def test_parse_plan_value_dash(self):
        from impl_plan import _parse_plan_value
        result = _parse_plan_value("-")
        assert result["value"] is None
        assert result["is_numeric"] is False
        assert result["raw"] is None

    def test_parse_plan_value_empty(self):
        from impl_plan import _parse_plan_value
        result = _parse_plan_value("")
        assert result["value"] is None
        assert result["is_numeric"] is False

    def test_parse_plan_value_parenthesized(self):
        from impl_plan import _parse_plan_value
        result = _parse_plan_value("(제안)")
        assert result["value"] is None
        assert result["is_numeric"] is False

    def test_parse_plan_value_percent(self):
        from impl_plan import _parse_plan_value
        result = _parse_plan_value("85%")
        assert result["value"] == 85
        assert result["unit"] == "%"
        assert result["is_numeric"] is True

    def test_parse_plan_value_명(self):
        from impl_plan import _parse_plan_value
        result = _parse_plan_value("120명")
        assert result["value"] == 120
        assert result["unit"] == "명"

    # ── _split_merged_cells ───────────────────────────────────────────

    def test_split_merged_cells_no_split_single_line(self):
        from impl_plan import _split_merged_cells
        result = _split_merged_cells("KS 제정 건수", ["10", "15", "20"])
        assert len(result) == 1
        assert result[0][0] == "KS 제정 건수"
        assert result[0][1] == ["10", "15", "20"]

    def test_split_merged_cells_matching_newlines(self):
        from impl_plan import _split_merged_cells
        result = _split_merged_cells(
            "표준 제정\n시험 인증",
            ["10\n20", "15\n25", "20\n30"],
        )
        assert len(result) == 2
        assert result[0][0] == "표준 제정"
        assert result[0][1] == ["10", "15", "20"]
        assert result[1][0] == "시험 인증"
        assert result[1][1] == ["20", "25", "30"]

    def test_split_merged_cells_non_matching_counts(self):
        from impl_plan import _split_merged_cells
        # Name has 2 lines but values have 1 line each -> no split
        result = _split_merged_cells(
            "긴 이름이\n두 줄",
            ["10", "15"],
        )
        assert len(result) == 1
        assert "긴 이름이 두 줄" in result[0][0]

    def test_split_merged_cells_empty_values(self):
        from impl_plan import _split_merged_cells
        result = _split_merged_cells("이름\n이름2", ["", "-", ""])
        assert len(result) == 1  # No non-empty values -> no split

    def test_split_merged_cells_name_grouping(self):
        """When name has more lines than value count, group consecutive names."""
        from impl_plan import _split_merged_cells
        result = _split_merged_cells(
            "A\nB\nC\nD",
            ["10\n20", "30\n40"],
        )
        assert len(result) == 2
        assert result[0][0] == "A B"
        assert result[1][0] == "C D"

    # ── _split_officer ────────────────────────────────────────────────

    def test_split_officer_suffix_rank(self):
        from impl_plan import _split_officer
        result = _split_officer("윤성봉 사무관")
        assert result["name"] == "윤성봉"
        assert result["rank"] == "사무관"

    def test_split_officer_prefix_rank(self):
        from impl_plan import _split_officer
        result = _split_officer("서기관 이형")
        assert result["name"] == "이형"
        assert result["rank"] == "서기관"

    def test_split_officer_no_rank(self):
        from impl_plan import _split_officer
        result = _split_officer("홍길동")
        assert result["name"] == "홍길동"
        assert result["rank"] is None

    def test_split_officer_empty(self):
        from impl_plan import _split_officer
        result = _split_officer("")
        assert result["name"] is None
        assert result["rank"] is None

    @pytest.mark.parametrize("input_str,expected_rank", [
        ("김철수 주무관", "주무관"),
        ("이영희 서기관", "서기관"),
        ("박민정 연구관", "연구관"),
        ("최수진 과장", "과장"),
        ("정우석 팀장", "팀장"),
        ("한소라 연구사", "연구사"),
        ("이준호 행정사무관", "행정사무관"),
    ])
    def test_split_officer_various_ranks(self, input_str, expected_rank):
        from impl_plan import _split_officer
        result = _split_officer(input_str)
        assert result["rank"] == expected_rank

    # ── _domain_code ──────────────────────────────────────────────────

    def test_domain_code_d1(self):
        from impl_plan import _domain_code
        assert _domain_code("미래 핵심산업 표준화") == "D1"

    def test_domain_code_d2(self):
        from impl_plan import _domain_code
        assert _domain_code("국민 체감 표준화") == "D2"
        assert _domain_code("국민체감") == "D2"

    def test_domain_code_d3(self):
        from impl_plan import _domain_code
        assert _domain_code("기술규제 혁신") == "D3"
        assert _domain_code("기술 규제") == "D3"

    def test_domain_code_d4(self):
        from impl_plan import _domain_code
        assert _domain_code("혁신적 표준 인프라") == "D4"
        assert _domain_code("혁신적표준") == "D4"

    def test_domain_code_none(self):
        from impl_plan import _domain_code
        assert _domain_code(None) is None
        assert _domain_code("기타") is None


# ═══════════════════════════════════════════════════════════════════════════
# 5. AI classification validation (against live data)
# ═══════════════════════════════════════════════════════════════════════════

class TestAIClassificationValidation:
    """Validate AI classifications in projects.v1.json."""

    AI_KEYWORDS = [
        "AI", "인공지능", "생성형", "LLM", "머신러닝", "딥러닝",
        "지능형", "AX", "초거대", "에이전틱", "피지컬 AI",
    ]

    def _project_text(self, p: dict) -> str:
        """Concatenate all searchable text in a project."""
        parts = [p.get("name", "")]
        parts.extend(p.get("description", []) or [])
        parts.extend(p.get("subtasks", []) or [])
        return " ".join(parts)

    def test_explicit_projects_contain_ai_keywords(self, projects_data):
        """AI-explicit projects should contain at least one AI keyword."""
        projects = projects_data["projects"]
        explicit = [p for p in projects if p.get("ai_relevance") == "explicit"]
        assert len(explicit) > 0, "No AI-explicit projects found"

        failures = []
        for p in explicit:
            text = self._project_text(p)
            has_keyword = any(kw.lower() in text.lower() for kw in self.AI_KEYWORDS)
            if not has_keyword:
                failures.append(p["id"])

        precision = (len(explicit) - len(failures)) / len(explicit) * 100
        assert precision >= 90, (
            f"AI explicit precision {precision:.1f}% < 90%. "
            f"Failures: {failures}"
        )

    def test_t01_tagged_projects_mention_ai(self, projects_data):
        """Projects tagged with T01 (AI) should mention AI-related terms."""
        projects = projects_data["projects"]
        t01_projects = [
            p for p in projects
            if "T01" in (p.get("tech_category_ids") or [])
        ]
        if not t01_projects:
            pytest.skip("No T01-tagged projects found")

        failures = []
        for p in t01_projects:
            text = self._project_text(p)
            has_keyword = any(kw.lower() in text.lower() for kw in self.AI_KEYWORDS)
            if not has_keyword:
                failures.append(p["id"])

        precision = (len(t01_projects) - len(failures)) / len(t01_projects) * 100
        assert precision >= 85, (
            f"T01 tag precision {precision:.1f}% < 85%. "
            f"Failures: {failures}"
        )

    def test_ai_classifier_function_consistency(self, projects_data):
        """classify_ai result should match stored ai_relevance for a sample."""
        from classify import classify_ai, project_haystack
        projects = projects_data["projects"]
        sample = projects[:20]
        mismatches = []
        for p in sample:
            text = project_haystack(p)
            computed = classify_ai(text)
            stored = p.get("ai_relevance", "none")
            if computed != stored:
                mismatches.append((p["id"], computed, stored))

        # Allow small tolerance for edge cases
        assert len(mismatches) <= 3, (
            f"{len(mismatches)} mismatches in first 20 projects: {mismatches}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# 6. Tech tagging validation
# ═══════════════════════════════════════════════════════════════════════════

class TestTechTaggingValidation:
    """Validate tech category tagging precision against project content."""

    # Mapping: tech ID -> keywords expected in tagged projects
    TECH_KEYWORDS = {
        "T01": ["AI", "인공지능", "생성형", "LLM", "머신러닝", "딥러닝", "지능형", "AX"],
        "T02": ["양자", "quantum"],
        "T03": ["첨단제조", "스마트제조", "스마트팩토리", "적층제조", "3D프린팅"],
        "T04": ["6G", "5G", "차세대통신", "이동통신", "위성통신"],
        "T05": ["디스플레이", "OLED", "LED"],
        "T06": ["반도체", "웨이퍼", "HBM", "뉴로모픽"],
        "T07": ["자율주행", "전기차", "수소차", "미래차", "모빌리티"],
        "T08": ["미래선박", "친환경선박", "자율운항", "선박"],
        "T09": ["로봇", "휴머노이드", "로보틱스"],
        "T10": ["첨단바이오", "디지털헬스", "정밀의료", "바이오"],
        "T11": ["수소", "청정에너지", "재생에너지", "태양광", "풍력", "연료전지"],
        "T12": ["핵심소재", "소재", "나노", "탄소"],
        "T13": ["원자력", "SMR", "원전", "방사선", "핵융합"],
        "T14": ["이차전지", "배터리", "전고체", "리튬"],
        "T15": ["메타버스", "XR", "VR", "AR", "디지털휴먼"],
        "T16": ["항공우주", "위성", "발사체", "드론", "UAM"],
        "T17": ["사이버보안", "개인정보", "제로트러스트", "FIDO", "보안"],
        "T18": ["스마트시티", "디지털트윈", "IoT", "사물인터넷"],
    }

    def _project_text(self, p: dict) -> str:
        parts = [p.get("name", "")]
        parts.extend(p.get("description", []) or [])
        parts.extend(p.get("subtasks", []) or [])
        return " ".join(parts)

    def test_sample_ai_explicit_content(self, projects_data):
        """Sample up to 10 AI-explicit projects and verify AI keywords in content."""
        projects = projects_data["projects"]
        ai_explicit = [p for p in projects if p.get("ai_relevance") == "explicit"][:10]
        if not ai_explicit:
            pytest.skip("No AI-explicit projects")

        ai_kws = self.TECH_KEYWORDS["T01"]
        correct = 0
        for p in ai_explicit:
            text = self._project_text(p)
            if any(kw.lower() in text.lower() for kw in ai_kws):
                correct += 1

        precision = correct / len(ai_explicit) * 100
        print(f"\nAI-explicit sample precision: {precision:.0f}% ({correct}/{len(ai_explicit)})")
        assert precision >= 90, f"AI explicit precision {precision:.0f}% < 90%"

    def test_sample_tech_tagged_content(self, projects_data):
        """Sample tech-tagged projects and verify tags match content keywords."""
        projects = projects_data["projects"]
        tagged = [p for p in projects if p.get("tech_category_ids")]
        if not tagged:
            pytest.skip("No tech-tagged projects")

        sample = tagged[:10]
        correct = 0
        total_tags = 0
        mismatches = []

        for p in sample:
            text = self._project_text(p)
            for tid in p["tech_category_ids"]:
                total_tags += 1
                keywords = self.TECH_KEYWORDS.get(tid, [])
                if not keywords:
                    correct += 1  # No keywords defined -> give benefit of doubt
                    continue
                if any(kw.lower() in text.lower() for kw in keywords):
                    correct += 1
                else:
                    mismatches.append((p["id"], tid))

        if total_tags == 0:
            pytest.skip("No tech tags to validate")

        precision = correct / total_tags * 100
        print(f"\nTech-tag sample precision: {precision:.0f}% ({correct}/{total_tags})")
        print(f"Mismatches: {mismatches}")
        assert precision >= 85, f"Tech tag precision {precision:.0f}% < 85%"

    def test_classify_tech_function_matches_taxonomy(self, tech_taxonomy):
        """classify_tech should correctly match against the taxonomy."""
        from classify import classify_tech
        result = classify_tech("AI 반도체 표준 개발", tech_taxonomy)
        assert "T01" in result or "T06" in result, f"Expected T01 or T06, got {result}"

    def test_classify_tech_empty_for_irrelevant(self, tech_taxonomy):
        from classify import classify_tech
        result = classify_tech("날씨 예보 서비스 개선", tech_taxonomy)
        assert result == []


# ═══════════════════════════════════════════════════════════════════════════
# Additional unit-level classifier tests
# ═══════════════════════════════════════════════════════════════════════════

class TestClassifyAI:
    """Direct unit tests for classify.classify_ai."""

    def test_explicit_AI(self):
        from classify import classify_ai
        assert classify_ai("AI 핵심기반 표준화") == "explicit"

    def test_explicit_인공지능(self):
        from classify import classify_ai
        assert classify_ai("인공지능 학습 데이터") == "explicit"

    def test_explicit_생성형(self):
        from classify import classify_ai
        assert classify_ai("생성형 모델 안전성") == "explicit"

    def test_implicit_자율주행(self):
        from classify import classify_ai
        assert classify_ai("자율주행 표준화 추진") == "implicit"

    def test_implicit_스마트시티(self):
        from classify import classify_ai
        assert classify_ai("스마트시티 인프라") == "implicit"

    def test_none_unrelated(self):
        from classify import classify_ai
        assert classify_ai("상수도 관리 표준") == "none"
        assert classify_ai("계량법 개정") == "none"


class TestIsAIDirect:
    """Direct unit tests for classify.is_ai_direct."""

    def test_positive_AI_core(self):
        from classify import is_ai_direct
        assert is_ai_direct("AI 핵심기반 분야")
        assert is_ai_direct("인공지능 표준 전문연구실")
        assert is_ai_direct("머신러닝 적합성평가")

    def test_negative_ai_application(self):
        from classify import is_ai_direct
        assert not is_ai_direct("AI 스마트 정수장 국제표준(ISO) 개발")
        assert not is_ai_direct("AI 의료기기 표준화")
        assert not is_ai_direct("AI 친화적 공공데이터")

    def test_negative_no_ai(self):
        from classify import is_ai_direct
        assert not is_ai_direct("수도시설 진단 프로세스 표준")
        assert not is_ai_direct("국제표준 리더십 확대")


class TestClassifyAICategories:
    """Direct unit tests for classify.classify_ai_categories."""

    def test_foundation(self):
        from classify import classify_ai_categories
        cats = classify_ai_categories("AI 핵심기반 인프라 데이터셋 표준화")
        assert "foundation" in cats

    def test_technology(self):
        from classify import classify_ai_categories
        cats = classify_ai_categories("AI 신뢰·안전성 평가 기준")
        assert "technology" in cats

    def test_application(self):
        from classify import classify_ai_categories
        cats = classify_ai_categories("의료 AI 융합 표준")
        assert "application" in cats

    def test_utilization(self):
        from classify import classify_ai_categories
        cats = classify_ai_categories("AX 전환 지원 인프라")
        assert "utilization" in cats

    def test_empty_text(self):
        from classify import classify_ai_categories
        assert classify_ai_categories("") == []
        assert classify_ai_categories("날씨 관련 업무") == []


class TestClassifyStrategy:
    """Direct unit tests for classify.classify_strategy."""

    def test_multiple_areas(self):
        from classify import classify_strategy
        areas, _ = classify_strategy(
            "KOLAS 공인기관 확대 및 국제표준 ISO 제안 전문가 양성",
            engagements=[],
        )
        assert "S-CAB" in areas
        assert "S-INT" in areas
        assert "S-HR" in areas

    def test_formal_track(self):
        from classify import classify_strategy
        _, track = classify_strategy(
            "ISO 표준 제안",
            engagements=[{
                "body_type": "formal", "body_level": "org",
                "body_name": "ISO", "role": "contribute", "snippet": "",
            }],
        )
        assert track == "formal"

    def test_hybrid_via_fast_track(self):
        from classify import classify_strategy
        _, track = classify_strategy(
            "Fast-Track을 통한 국제표준 승격",
            engagements=[],
        )
        assert track == "hybrid"

    def test_de_facto_track(self):
        from classify import classify_strategy
        _, track = classify_strategy(
            "IEEE 표준 참여",
            engagements=[{
                "body_type": "de_facto", "body_level": "org",
                "body_name": "IEEE", "role": "contribute", "snippet": "",
            }],
        )
        assert track == "de_facto"

    def test_none_track(self):
        from classify import classify_strategy
        _, track = classify_strategy(
            "일반 업무 수행",
            engagements=[],
        )
        assert track == "none"
