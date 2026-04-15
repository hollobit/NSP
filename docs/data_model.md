# 데이터 모델 (v0)

## 엔티티 개요

```
MasterPlan (기본계획)
  └─ Domain (4대 분야)
       └─ CoreTask (6차: 13개 · 5차는 12개 — 관행상 "12대"로 표기됨)   ⭐ 1급 분석 축
            ├─ id             (예: "CT-1-2" = 분야1-②)
            ├─ domain_id      (1|2|3|4)
            ├─ sub_no         (①|②|③|④ → 1|2|3|4)
            ├─ name           (예: "AI 핵심기반 및 AI 산업융합 표준화")
            ├─ description
            ├─ responsible_agencies[]   (주관 부처청 N개, p.2 매트릭스)
            ├─ has_impl_plan : bool     (p.2의 O/- 컬럼)
            ├─ source_page
            └─ is_ai_focus : bool       (1-② 등 AI가 명시된 과제)

ImplementationPlan (시행계획, 2026)
  └─ Agency (18개 부처청)
       ├─ overview (추진배경·추진목표)
       ├─ legal_basis[]               ← 법적근거 (법률명·조항, p.5-7 블록)
       ├─ performance_indicators[]    ← 고유성과지표 (연도별 계획/실적)
       │    PerfIndicator:
       │     ├─ domain (4대 분야)
       │     ├─ name, unit
       │     └─ yearly: [{year, plan, actual}] (2026~2030)
       └─ Project[]                    ← 실제 사업 단위 (아래 Project 엔티티)

TechCategory (18개 핵심 기술 분류 — 교차 분석 중심축, docs/tech_taxonomy.md)
  ├─ id, name_ko, name_en, type
  ├─ is_ai_anchor: bool
  ├─ std_bodies[]
  └─ aliases[]                       (동의어 사전)

AILinkage (AI ↔ 기타 기술 교차)
  ├─ ai_tech_id, partner_tech_id
  ├─ weight = co_occurrence × log(1 + sum_budget)
  ├─ evidence[] : [{file, page, snippet}]
  └─ subtask_ids[]

Project (사업/세부사업, 시행계획 atomic 단위)  ⭐
  ├─ id, agency_id
  ├─ linked_core_task_id         (12대 중점과제 번호: 1-①, 1-②, …)
  ├─ sequence_no                 (해당 과제 내 사업 순번: 사업1, 사업2, …)
  ├─ name                        (사업명, 예: "디지털 핵심기술 선도를 위한 표준 개발 및 표준화 전략 수립")
  ├─ description[]               (□ 사업 내용 — bullet 원문 보존)
  ├─ subtasks[]                  ⭐ 세부과제 (□ 당해연도 사업 추진계획)
  │    SubTaskItem:
  │     ├─ text                  (한 bullet = 한 세부과제)
  │     ├─ tech_category_ids[]
  │     └─ ai_relevance
  ├─ budget                       ⭐ 당해년도 예산 현황
  │    Budget:
  │     ├─ year: 2026
  │     ├─ amount_mil_krw        (백만원)
  │     ├─ status: {planned|confirmed|continuing} (계획/확정/계속사업)
  │     ├─ source_type: {자체|R&D|출연금|보조금|...}
  │     ├─ prev_year_amount      (가능하면 2025 비교)
  │     └─ source_page
  ├─ kpis[]                       ⭐ 사업별 성과지표
  │    KPI:
  │     ├─ name                  (지표명)
  │     ├─ unit                  (건/명/% 등)
  │     ├─ target_2026
  │     ├─ target_trajectory     (가능 시 2027~2030)
  │     ├─ linked_agency_indicator_id (부처 고유성과지표 연결)
  │     └─ source_page
  ├─ contact                      (담당부서·담당자·전화·이메일)
  ├─ tech_category_ids[]         (멀티 레이블)
  ├─ std_engagements[]           → StdEngagement
  ├─ cooperation[]               → Cooperation
  ├─ strategy_areas[]            ['S-DOM'|'S-CAB'|'S-HR'|'S-INT']
  ├─ track_type                  'formal'|'de_facto'|'hybrid'|'none'
  ├─ ai_relevance
  ├─ source: {file, page_range}
  └─ full_text_excerpt            (상세 분석용 원문 단락 보존)

Standard (개별 표준 — 국제/사실상/국가/단체)  ⭐
  ├─ id, title, type: {international|de_facto|national|org}
  ├─ std_body_id                     → StandardBody
  ├─ document_code                   (예: ISO/IEC 42001, IEEE P7001)
  ├─ status: {planning|drafting|published|revising}
  ├─ target_year (제·개정 목표 연도)
  └─ tech_category_ids[]

StandardBody (표준화 기구)  ⭐
  ├─ id, name, short_name            (예: ISO/IEC JTC1/SC42)
  ├─ type: {formal|de_facto|consortium|national}
  │     - formal   : 공적 표준화기구 (ISO, IEC, ITU, KATS/KS)
  │     - de_facto : 사실상 표준화기구 (IEEE-SA, ASTM, SAE, 3GPP, W3C, IETF, OASIS 등)
  │     - consortium : 산업 컨소시엄 (VESA, SEMI, Hydrogen Council, FIDO, MPAI, COVESA 등)
  │     - national : 국가표준기구 (KATS, ANSI, BSI, SAC)
  ├─ scope                           (분과·관심 영역)
  ├─ korean_engagement               (한국 참여 현황: P-member, O-member, 의장국 여부 등)
  ├─ strategic_weight                (전략적 중요도: 시장영향력 + 한국 참여도)
  └─ primary_tech_category_ids[]

StdEngagement (사업 ↔ 표준/표준화기구 대응 관계)  ⭐
  ├─ project_id
  ├─ standard_id or std_body_id
  ├─ role: {lead|contribute|monitor|adopt}
  ├─ activity: {proposal|editor|secretariat|wg_participation|tc_chair|...}
  ├─ evidence: {page, snippet}
  └─ year

Cooperation (협력 관계 — 국내 부처간 / 국제)  ⭐
  ├─ project_id
  ├─ partner_type: {domestic_agency|foreign_nsb|industry|academia|intl_body}
  ├─ partner_id_or_name              (부처라면 agency_id, 외국이면 기구명/국가)
  ├─ mode: {mou|joint_rd|co_standardization|mutual_recognition|benchmarking}
  ├─ description
  └─ evidence: {page, snippet}
```

## AI 중심 표준화 기구 대응 분석 (필수 축)

T01(AI)을 중심으로 다음 3단계 분석이 필수다:

1. **대응 현황**: 각 AI 관련 사업이 어느 표준화 기구(`StandardBody`)에 어떤 역할(`role/activity`)로 참여하고 있는지 집계.
   - 예: ISO/IEC JTC1/SC42 P-member 참여, WG 의장, TS/IS 제안, 공동 에디터 등
2. **공백/중복 식별**: 18개 기술 × 주요 기구 매트릭스에서 비대응 셀(공백) vs 중복 대응(자원 분산) 노출.
3. **협력 기회**: AI 사업과 타 기술 사업 간 **동일 기구 공동 참여**를 협력 후보로 제안.
   - 예: SC42(AI) + TC22(자율주행) 공동 작업 → 자율주행 AI 안전성 표준 공동 대응

## Cooperation 축의 의미
- **국내 부처간**: 같은 표준화기구에 여러 부처 공동 참여 → 중복 제거 또는 역할 분담 기회
- **국제 협력**: MRA(상호인정), 양자·다자 MOU, Fast-Track(ISO/IEC Dual-logo) 가능성
- **민관 리더십**: 사실상표준기구(ASTM, IEEE 등) 참여 확대 근거

## 전략 체계 (StrategyTaxonomy) ⭐

모든 사업은 **2가지 직교 축**으로 분류되어 전략 수립·비교가 가능해야 한다.

### 축 A — 표준화 기구 유형 (공적 vs 사실상)
- `formal_track` (공적): ISO/IEC/ITU 중심, 국가대표 참여, 규범적 지위
- `de_facto_track` (사실상): IEEE/ASTM/3GPP/W3C 등, 시장 주도, 민간 리더십
- `hybrid_track` (혼합): Fast-Track, Dual-logo, 표준기구 간 협력

### 축 B — 표준 활동 영역 (4대 전략)
| 코드 | 영역 | 세부 활동 | 관련 지표 |
|------|------|----------|----------|
| S-DOM | **국내 표준 (KS)** | KS 제·개정, 단체표준 제·개정, 표준문서 현대화 | KS 제정 건수, 단체표준 건수 |
| S-CAB | **시험·인증 (적합성평가)** | KOLAS 지정, 시험법 개발, 국제상호인정(ILAC/IAF), 시험·인증서비스 확대 | KOLAS 공인기관 수, 적합성평가 인정 건수 |
| S-HR  | **표준 전문인력** | 전문가 양성, 국제 의장/간사 배출, 명장 멘토링, 단계별(Step-up) 교육 | 전문가 수, 국제의장 수, 멘토링 건수 |
| S-INT | **국제 표준 연계** | ISO/IEC 제안, ITU 기고문, 사실상표준기구 참여, 양자·다자 협력, MRA | 국제표준 제안·반영 건수, ITU 기고문 건수 |

> 교차로: `formal_track × S-INT` (ISO/IEC 제안), `de_facto_track × S-INT` (IEEE 참여) 등이 **전략 셀**이 된다.

### Project 필드 확장
```
Project 추가 필드 (기존에 이어서):
  ├─ strategy_areas[]     : ['S-DOM'|'S-CAB'|'S-HR'|'S-INT'] 멀티레이블
  ├─ track_type           : 'formal'|'de_facto'|'hybrid'|'mixed'
  └─ strategy_rationale   : 근거 원문 인용
```

### 전략 분석 산출물
- `agg_by_strategy.json`: 4대 전략 × 18기술 × (공적/사실상) 3차원 큐브
- **전략 공백 식별**: 예를 들어 "AI × S-INT × de_facto" 셀이 비었다면 IEEE AI 표준 대응 부재 의미
- **협력 매칭**: 같은 `(tech, strategy_area, track_type)` 셀에 다수 부처가 있으면 국내 협력 후보
- **리더십 기회**: `strategic_weight`가 높은 기구에서 한국 참여도가 낮은 셀 → 전문인력(S-HR) 투자 우선순위

## 드릴다운 규약
모든 사업은 **다음 5개 축 중 어디서든 진입 가능**하며, 임의 노드에서 상/하위 이동 가능해야 한다:

1. **12대 중점과제 축** — CoreTask `CT-1-2 AI 핵심기반…` → 주관 부처들 → 해당 사업 → 상세 원문
2. **18개 기술 축** — TechCategory `T01 AI` → 관련 부처 → 사업 → 상세
3. **부처 축** — Agency `과기정통부` → 사업 → 상세
4. **표준화기구 축** — StandardBody `ISO/IEC JTC1/SC42` → 참여 사업 → 상세
5. **전략 축** — `S-INT × formal` → 사업 → 상세

Project는 위 5개 축에 모두 인덱싱되어야 검색/필터가 O(1)로 동작한다.

## AI 관련성 판정 규칙
1. `explicit`: 과제명/설명에 "AI", "인공지능", "생성형", "LLM" 등 명시
2. `implicit`: 연관 기술(자율주행, 로봇, 디지털전환, 스마트시티 등) + AI 활용 맥락
3. `none`: 그 외

## AI 중심 교차 분석 요건
- 모든 과제는 18개 기술분류 중 1개 이상에 매핑 (멀티 레이블)
- AI(T01)를 anchor로 두고 나머지 17개와 연계 쌍 식별
- 연계 근거: 동일 과제 공출현, 부처 공동 주관, 예산 결합
- UI 최소 2뷰: (a) AI 중심 spoke, (b) 18×18 매트릭스(AI 행/열 강조)
