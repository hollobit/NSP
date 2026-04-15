# HISTORY — 국가 표준화 통합 대시보드

프로젝트 진화 기록. 작업 흐름·주요 의사결정·기술 전환을 시간 순으로 정리.

**저장소**: https://github.com/hollobit/NSP
**라이브**: https://hollobit.github.io/NSP/ (Pages 활성화 시)
**로컬**: `/Users/jonghongjeon/git/nsb/`

---

## 2026-04-15 · 단일 세션 내 구축

### ✨ 00:00 — Phase 0: 부트스트랩

- `pdf/` 폴더 두 원본 확보:
  - 「제6차 국가표준기본계획(2026-2030).pdf」(37p)
  - 「2026 시행계획.pdf」(209p, 18개 부처)
- `CLAUDE.md` 프로젝트 헌장 작성
- `Plans.md` + `.claude/settings.local.json` 권한 (pdf/ write deny)

### 🎯 Phase 1.5 — 18개 기술 taxonomy 확정

- 기본계획 **p.12** 근거: 4대 분야별 3 전략(첨단산업·NEXT·주요국) 교집합·합집합으로
  18개 분야 선정 (①AI ②양자 ③첨단제조 ... ⑱시티버스)
- `docs/tech_taxonomy.md` + `data/processed/tech_categories.v1.json`
- T01 AI를 **Anchor** 로 지정 — 이후 모든 분석의 기준축

### 📄 Phase 1 — PDF 원문 추출

- `scripts/extract_raw.py` (pdfplumber) — 페이지+표 JSON 추출
- 기본계획 37p · 시행계획 209p → `data/raw/*.pages.json`

### 🏛️ Phase 2 — 구조화 파싱 (13 과제 + 18 부처 + 92 사업)

- `src/parser/core_tasks.py` — p.2 매트릭스 ground truth 인코딩 (**5차 12개 → 6차 13개** 이력 명시)
- `src/parser/project_extractor.py` — 「사업N 헤더 + □ 섹션 마커 + 당해연도 추진계획/예산/성과지표」 패턴 파싱
  → **92 사업** · 84 예산 포착 · 총 **2,688억원** (268,781 백만원)
- `src/parser/history_encoder.py` — 5차 12개 세부과제 + 5개 성과 추이(2020→2025→2030) + 13개 5↔6 매핑
- `src/parser/impl_plan.py` — 부처 법적근거(54→70→**80**) · 연락처(18/18) · 고유성과지표(30→**42**)

### 🤖 Phase 3 — AI·기술·전략·기구 멀티 분류

- `src/parser/classify.py` — 키워드/정규식 기반 다축 태깅
  - **AI 관련성** 31건 (explicit 24 + implicit 7)
  - **18기술 멀티라벨**: 47/92 태깅, 125 중복 포함, 고유 70
  - **46→50 표준기구** NER (ISO/IEC/ITU + IEEE/3GPP/IETF/ASTM/JEDEC/ASME/MPAI 등)
  - **4대 전략 영역**: S-DOM 42 · S-CAB 13 · S-HR 35 · S-INT 54
  - **공적/사실상 트랙**: formal 28 · de_facto 5 · hybrid 7 · none 52

### 🎯 Phase 3.5 — AI 연계 가중치 그래프

- `src/parser/ai_linkage.py` — AI Anchor 17 엣지 + 18×18 매트릭스
- 가중치: `w = count × log₁₀(1 + budget_백만)`
- **Top 5 연계**: AI↔로봇(w 27.3 · 361억) · AI↔양자(26.8 · 290억) · AI↔반도체(23.2 · 436억) · AI↔첨단제조(22.7) · AI↔통신(17.7)

### 🧭 Phase 3.7/3.8 — 기구 level + 전략 이원 트랙

- 기구를 **Org/TC/JTC 3-레벨**로 구분 (ISO vs ISO/TC vs JTC1/SC42)
- JTC1~JTC5 + 산하 13 SC + JTC3 3 WG 참조 구조 인코딩
- 한글 통칭 "사실상표준화기구 대응" 문맥 감지 → generic de_facto 엔게이지먼트

### 💎 AI 예산 3-해상도 체계 정립

한 세션 내 발견된 핵심 개념 — 같은 'AI 예산'이 정의에 따라 4-5배 차이:

| 해상도 | 정의 | 값 |
|---|---|---|
| CT-1-2 정책 편성 | "AI 포커스 과제" 전체 | 195억 (7사업) |
| T01 기술 태깅 | AI 태그된 모든 사업 | 940억 (24사업, 중복 포함) |
| **순AI 표준화** | line-item "AI 표준화" 직접 명시 | **157억** (엄격), **104억** (line-only) |

### 🎨 4계층 AI 표준화 분류 (SC42 WG 체계 참고)

- **Foundation (기반)**: 인프라·데이터·모델 — 61억 · 6사업
- **Technology (기술)**: 신뢰·안전·평가 — 17억 · 8사업
- **Application (응용)**: 산업 융합 — 43억 · 17사업
- **Utilization (활용)**: AI 도구 사용 — 0억 · 6사업 (line 분리 부재)

### 🖼️ 웹 스택 3회 전환

1. (초안) Vite + React + TypeScript + Tailwind
2. (재확정) 단일 HTML 자립형 (Alpine.js + Tailwind Play CDN)
3. (최종) 파일 1개: `dist/index.html` — Python 빌더가 JSON을 인라인 주입

→ **빌드 도구 불필요 · `file://` 오프라인 동작 · GH Pages 업로드 1분 완료**

### 📊 개요 대시보드 위젯 11개 (스프린트)

1. 🏆 Top-10 예산 사업 (bar + 드로어)
2. 🎯 13과제 예산 도넛 (AI 포커스 앰버 강조)
3. 🏢 부처 Top-5 예산
4. 🗂️ 4대 분야(D1-D4) 분포
5. AI 3-해상도 비교 (195억/940억/157억)
6. 🔗 AI 간접 과제 Top-5 (CT-1-2 외 AI 비중)
7. 📈 5차→6차 목표 sparkline × 5
8. 📊 예산 편성 상태 도넛 (declared 84 / none 4 / unavailable 4)
9. ✅ 데이터 커버리지 게이지 × 4
10. 🏛️ 표준화기구 Top-10
11. ⚖️ 공적/사실상 트랙 도넛

### 🧰 Harness v3 구성

`.claude/` 디렉토리에 Claude Code harness 구축:

- **전문 에이전트 4개**: `pdf-parser` · `widget-builder` · `dashboard-deployer` · `data-validator`
- **슬래시 커맨드 4개**: `/rebuild` · `/verify` · `/sync` · `/plan`
- **자동화 훅 2개**: `pre-commit-build-check.sh` · `post-build-verify.sh`
- `.claude/settings.json` — 권한 + env 변수
- `.claude/README.md` — 구성 가이드

### 🔬 Phase 6-8 — 데이터 정밀화 + 검증

**Phase 6 정밀화 (5/5 완료):**
- 법적근거 18/18 부처 달성 (조달청 평문·질병청 해당없음·중기부 수동 인코딩)
- 예산 unknown 4 → unavailable 4 정확 분류
- 성과지표 중기부 12건 복구 (텍스트 fallback)
- 담당자 name/rank 분리 (`윤성봉 사무관` → `{name:"윤성봉", rank:"사무관"}`)
- 사실상표준기구 50개 (+JEDEC/ASME/ICDM/HL7 등)

**Phase 7.3 전략 공백 리포트**: `docs/insights/gaps.md`
- 216 셀 중 **134 공백** (62%)
- AI(T01) 4/12 공백 셀: S-DOM×hybrid, S-CAB×formal/hybrid, S-HR×formal

**Phase 7.5 CSV 내보내기**: 사업 탭 버튼, BOM+UTF-8, Excel 호환, 21 컬럼

**Phase 8.1 pytest**: `tests/` 3 파일 **41 tests 전부 통과**
- `test_project_extractor.py` — budget regex 8건
- `test_classify.py` — AI·기술·카테고리·기구 NER·전략 20건
- `test_impl_plan.py` — officer split·법률 plain list 13건

**Phase 8.2/8.3 샘플링 검증**: `docs/insights/validation.md`
- seed=20260415 결정론적 추출
- AI explicit 10/24 · 기술 태깅 10/47 수동 검토용 체크리스트

### 🚀 배포 (3회 push)

| 커밋 | 주요 변경 |
|---|---|
| [`8c094fd`](https://github.com/hollobit/NSP/commit/8c094fd) | 초기 dist/index.html 업로드 (493KB) |
| [`1e162f4`](https://github.com/hollobit/NSP/commit/1e162f4) | README 확장 (프로젝트 문서화) |
| [`6bdd658`](https://github.com/hollobit/NSP/commit/6bdd658) | 제목 "AI 표준화" 변경 (→ 재번복) |
| [`5257a5c`](https://github.com/hollobit/NSP/commit/5257a5c) | 제목 "국가 표준화 통합 대시보드" 확정 |
| [`f2b76cc`](https://github.com/hollobit/NSP/commit/f2b76cc) | 개요 위젯 11개 추가 (517KB) |
| [`ef980b1`](https://github.com/hollobit/NSP/commit/ef980b1) | Phase 6-8 정밀화·리포트·pytest (529KB) |

---

## 📦 최종 산출물

### 데이터 계층 (`data/processed/`)
```
tech_categories.v1.json     18 기술 + AI Anchor + aliases
core_tasks.v1.json          13 과제 + 5↔6 이력
agencies.v1.json            18 부처 + 법적근거 + 연락처 + 성과지표
projects.v1.json            92 사업 + 전 분류 (AI·tech·std·strategy·4계층)
std_bodies.v1.json          50 기구 (org/tc/jtc 3레벨)
ai_linkage.v1.json          17 AI 엣지 + 18×18 매트릭스 (가중치)
history_5th.v1.json         5차 12개 세부과제
goal_trajectory.v1.json     5 목표 지표 2020→2030 추이
task_mapping_5_to_6.v1.json 13 매핑 (신뢰도 포함)
strategy_gaps.v1.json       공백 큐브 요약
sampling_validation.v1.json 수동 검증 샘플
```

### 파서 계층 (`src/parser/`)
```
core_tasks.py               ground-truth 인코딩
history_encoder.py          5차 회고·목표 추이·매핑
project_extractor.py        사업 atomic 추출 (regex + 표 병합)
classify.py                 AI·tech·std·strategy 멀티 태깅 + 4계층 AI
impl_plan.py                부처 메타 (법적근거 3-mode + PI text fallback + officer split)
ai_linkage.py               18×18 공출현 매트릭스
gap_report.py               전략 공백 큐브 분석
std_bodies_reference.py     JTC1~5 + SC/WG 참조 구조
```

### 웹 계층
```
src/web/template.html       Alpine + Tailwind CDN 단일 템플릿
scripts/build_html.py       JSON 인라인 주입 → dist/index.html
scripts/build.sh            9단계 파이프라인 오케스트레이터
scripts/sampling_validation.py 검증 샘플 추출
```

### 품질 계층
```
tests/                      pytest 41 tests · ~0.05s
.claude/                    Harness v3 (agents/commands/hooks/settings)
docs/
├── data_model.md           엔티티 스키마
├── tech_taxonomy.md        18 기술 확정본
├── strategy_taxonomy.md    4 전략 × 공적/사실상
├── tech_stack.md           · architecture.md · plans_archive.md
└── insights/
    ├── gaps.md             전략 공백 리포트
    └── validation.md       태깅 검증 체크리스트
```

### 배포
```
dist/index.html             529.1 KB (data 334 KB inlined)
원격: hollobit/NSP@ef980b1  LICENSE · README.md · index.html
```

---

## 🔑 핵심 설계 결정

| # | 결정 | 맥락 |
|---|------|------|
| 1 | 단일 HTML 자립형 전환 | Vite→복잡도 대비 가치 낮음, GH Pages 즉시 배포 우선 |
| 2 | AI를 T01 Anchor로 고정 | 18기술 중 유일한 횡단축 — 모든 교차 분석의 기준점 |
| 3 | 13개 과제 (vs 관행 12대) | 5차 12 → 6차 13 확대 명시, 관행 명칭 충돌 투명 표시 |
| 4 | AI 예산 3-해상도 병기 | 단일 수치 제시 금지 (195/940/157억 동시 노출) |
| 5 | 4계층 AI 분류 도입 | "AI 관련" 추상도 해소, 실제 투자 구조 가시화 |
| 6 | 원본 PDF write deny | .claude/settings.json 에서 hard deny, 저작권 보호 |
| 7 | line-item 단위 정밀도 | "순AI 표준화"를 사업 단위 아닌 예산 항목 단위로 추출 |

---

## 📚 진화 그래프

```
초기       Phase 1      Phase 2       Phase 3-3.8    위젯        Phase 6-8
0 파일 → 9 개 데이터 → 92 사업   → 4축 다중 분류 → 11 위젯 → 정밀화+품질
                                                  ↓                ↓
                                            단일 HTML 자립 단일 HTML 529KB
                                                  ↓                ↓
                                           원격 배포 (6 커밋)  pytest 41 통과
```

---

## 🎯 남은 작업 (다음 세션)

- **Phase 7.1/7.2**: 협력 관계(Cooperation) 엔티티 + 부처 협력 매트릭스
- **Phase 7.4/7.6**: 사업 비교 (4건 side-by-side) + 5축 Sankey
- **Phase 8.4/8.5**: 접근성 WCAG AA + 오프라인 수동 검증
- **Phase 9**: GitHub Pages 활성화 · PDF 저작권 · README 스크린샷 · Issue 템플릿

---

*생성: 2026-04-15 · 작업 경과 자동 기록*
