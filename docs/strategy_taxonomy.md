# 전략 체계 (Strategy Taxonomy)

**목적**: 국가표준 사업을 **2개의 직교 축**으로 분류하여 전략 공백·중복·협력 기회를 정량 분석한다.

## 축 A — 표준화 기구 트랙 (track_type)

| 코드 | 이름 | 정의 | 대표 기구 |
|------|------|------|----------|
| `formal` | 공적 표준화 | WTO/TBT 협정 하 국가대표 참여, 규범적 지위 | ISO, IEC, ITU, KATS/KS |
| `de_facto` | 사실상 표준화 | 시장 주도, 민간/산업 리더십 | IEEE-SA, ASTM, SAE, 3GPP, W3C, IETF, OASIS |
| `hybrid` | 혼합/연계 | Fast-Track, Dual-logo, 기구 간 교차 채택 | (예) ASTM F2866 → IEC/ASTM 62885-7 |
| `none` | 미참여 | 국내 활동만 |

**판정 규칙**: 사업의 `std_engagements[]`에 연결된 `StandardBody.type` 집합으로 자동
- 전부 formal → `formal`
- 전부 de_facto/consortium → `de_facto`
- 혼재 또는 공식 Fast-Track/Dual-logo 명시 → `hybrid`
- 엔게이지먼트 없음 → `none`

## 축 B — 표준 활동 4대 영역 (strategy_areas[])

| 코드 | 영역 | 포함 활동 | 판정 키워드 |
|------|------|----------|------------|
| `S-DOM` | **국내 표준** | KS 제·개정, 단체표준, 표준문서 현대화, SMART 표준 | KS, 한국산업표준, 단체표준, 표준 제·개정 |
| `S-CAB` | **시험·인증 (적합성평가)** | KOLAS, 공인기관, 시험법, 인증서비스, ILAC/IAF MRA | KOLAS, 공인기관, 적합성평가, 시험·인증, 인정, ILAC, IAF |
| `S-HR`  | **표준 전문인력** | 전문가 양성, 국제의장/간사, Step-up 교육, 명장 멘토링 | 전문가, 전문인력, 양성, 교육, 멘토링, 의장, 간사, 명장, 자격 |
| `S-INT` | **국제 표준 연계** | ISO/IEC 제안·반영, ITU 기고, 사실상표준 참여, MOU/MRA | ISO, IEC, ITU, 국제표준, 기고, 제안, MOU, MRA, Fast-Track, 사실상표준 |

**멀티레이블**: 한 사업은 복수 영역 동시 소속 가능. 예: "SC42 에디터 양성 + ISO 42001 제안" → `S-HR` + `S-INT`

## 축 A × 축 B 전략 매트릭스 (4 × 3 = 12 셀, `none` 제외)

|  | formal | de_facto | hybrid |
|---|---|---|---|
| **S-DOM** | KS 제·개정 | 단체표준(산업) | — (드묾) |
| **S-CAB** | KOLAS/ILAC | IEEE 공인·ASTM 시험법 | 국내외 상호인정 |
| **S-HR**  | ISO/IEC 의장·간사 양성 | IEEE/ASTM 에디터 양성 | 국제 명장 교류 |
| **S-INT** | ISO/IEC/ITU 제안 | IEEE/3GPP/W3C 참여 | Fast-Track, Dual-logo |

각 셀은 `(기술 T01~T18) × (셀)`로 다시 쪼개져 **18×12=216 분석 단위**가 된다.
AI(T01) 기준 12 셀이 **최우선 분석 단면**이다.

## 전략 분석 출력 (Phase 3.8·5.5 산출물)

### 1. 전략 포트폴리오 대시보드
- 각 전략 영역별 예산·사업 비율 (4카드)
- 공적/사실상 트랙 비중 파이차트
- AI 관련 사업의 전략 분포 (4영역 × 2트랙)

### 2. 전략 공백 리포트 (자동)
다음 조건의 셀을 "공백(gap)"으로 플래그:
- 사업 수 = 0
- 예산 합 < 임계치(예: 전략 평균의 25%)
- 부처 수 = 1 (단일 부처 의존 리스크)

**AI 우선 예시 질문**이 자동 답변 가능해야 함:
- "AI × S-INT × de_facto" (IEEE AI 표준 참여)의 사업 수·예산은?
- "AI × S-HR × formal" (SC42 의장/에디터 양성)에 부족은?
- "AI × S-CAB × hybrid" (AI 모델 적합성평가 상호인정)의 공백은?

### 3. 협력 매칭
- 같은 `(기술, 전략영역, 트랙)` 셀에 다수 부처 존재 → **국내 협력 후보**
- 같은 `StandardBody`에 다수 부처 참여 → **국내 중복 조정 대상**
- `hybrid` 트랙 사업 중 파트너 미명시 → **국제 협력 미개척**

### 4. 리더십 기회 지수
`leadership_gap = strategic_weight(기구) − korean_engagement(기구)`
- 높은 값일수록 **투자 우선순위 높은 기구**
- S-HR(전문인력 양성)과 연결하면 "어디에 전문가를 보내야 하는가" 답이 나옴

## Project 필드 매핑

```json
{
  "id": "P-MSIT-2026-042",
  "tech_category_ids": ["T01", "T06"],
  "std_engagements": [
    {"std_body_id": "SB-SC42", "role": "lead", "activity": "editor"}
  ],
  "strategy_areas": ["S-INT", "S-HR"],
  "track_type": "formal",
  "strategy_rationale": "ISO/IEC JTC1/SC42 에디터로 참여해 AI 42001 개정안 제안"
}
```
