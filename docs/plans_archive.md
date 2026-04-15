# Plans Archive — 완료/이관 항목

## Phase 0 — 프로젝트 부트스트랩 ✅
- 디렉토리 뼈대 / CLAUDE.md / Plans.md / 권한 / requirements.txt / .gitignore
- CLAUDE.md 리팩토링 (docs/ 분리, `@docs/*` 참조)

## Phase 1 — PDF 원문 추출 ✅
- `scripts/extract_raw.py` — pdfplumber 기반 페이지+표 추출
- 기본계획 37p, 시행계획 209p → `data/raw/*.pages.json`

## Phase 1.5 — 18개 기술 taxonomy 확정 ✅
- 출처: 제6차 기본계획 p.12
- `docs/tech_taxonomy.md` + `data/processed/tech_categories.v1.json`
- T01~T18, AI Anchor 플래그, 동의어 사전, std_bodies 매핑

## Phase 2 — 구조화 파싱 ✅
- `src/parser/core_tasks.py` — 13 과제 × 18 부처 ground-truth 인코딩 (p.2 매트릭스)
- `src/parser/impl_plan.py` — 법적근거 70건(15/18 부처, 3 추출모드) + 연락처 18/18 + 고유성과지표 30행(17/18 부처)
- `src/parser/project_extractor.py` — 92 사업 atomic, 84 예산 포착 (declared/declared_none/unavailable/unknown 상태), 표+텍스트 이중 병합, total 2,688억원
- `core_tasks.v1.json` · `agencies.v1.json` · `projects.v1.json`

## Phase 3 — AI 관련성 + 18기술 멀티태깅 ✅
- `src/parser/classify.py` — 동의어 사전 기반
- AI: explicit 24 / implicit 7 / none 61 (31/92 관련)
- Tech: 47/92 멀티라벨
- Strategy: S-DOM 42 / S-CAB 13 / S-HR 35 / S-INT 54

## Phase 3.5 — AI 중심 연계 그래프 ✅
- `src/parser/ai_linkage.py` — `weight = count × log₁₀(1+budget)`
- AI 17엣지 전수 연결, 18×18 matrix 252 cell
- Top 5: AI↔T09 로봇(w27.3) · T02 양자(26.8) · T06 반도체(23.2) · T03 첨단제조(22.7) · T04 통신(17.7)

## Phase 3.7 — 표준화 기구 대응 ✅
- `classify.py` NER 40+ 패턴 (공적/사실상/컨소시엄/국가)
- AI-특화 보강: MPAI, AI Alliance, Partnership on AI, MLCommons, OpenXLA
- 26개 고유 기구 자동 발견
- "사실상표준" 맥락 부스팅으로 트랙 분류 강화
- 트랙 분포: formal 29 · de_facto 5 · hybrid 7 · none 51
- 39/92 사업에 기구 대응 레코드

## Phase 3.8 — 전략 체계 분류 ✅
- `docs/strategy_taxonomy.md` — 4대 영역(S-DOM/S-CAB/S-HR/S-INT) × 공적/사실상 직교 매트릭스
- classify.py에 편입 (strategy_areas 멀티, track_type 단일)

## Phase 5 — 웹 대시보드 핵심 뷰 ✅
- 단일 HTML 자립형 (Alpine + Tailwind Play + D3/Chart.js/Fuse.js CDN)
- 빌드: `scripts/build_html.py` + `scripts/build.sh` 8단계 파이프라인
- 활성 14뷰:
  - overview · coretask · tech · agency · projects(필터/상세)
  - matrix-ca(과제×부처) · matrix-ct(과제×기술) · matrix-at(부처×기술)
  - ai-spoke(가중치 기반) · tech-body(18기술×주요기구) · strategy
  - history(5차→6차) · search(placeholder)
- 상세 드로어: 기술 카드 · 과제 카드 · 부처 카드(법적근거·연락처·고유성과지표) · 사업 카드(전 분류 배지·예산 라인아이템·기구 대응)

## 의사결정 & 데이터 이력

| 일자 | 결정 |
|------|------|
| 2026-04-15 09:17 | 초기 하네스·플랜 |
| 09:30 | Project 엔티티 신설 (기술×부처×사업 드릴다운) |
| 09:35 | 18개 taxonomy 확정 (제6차 기본계획 p.12) |
| 09:50 | 웹 스택: 단일 HTML 자립형 (Alpine+CDN, Python 인라인 주입) |
| 10:00 | Standard/StandardBody/StdEngagement/Cooperation 엔티티 신설 |
| 10:10 | 공적/사실상 이원 전략 + 4전략 영역 축 신설 |
| 10:20 | 5차 12개 → 6차 13개 구조 확정, 관행 명칭 주석 |
| 10:30 | Project 엔티티 확장 (subtasks, budget_status, kpis, contact, source.page_range) |
| 10:40 | 5차 12개 세부과제·goal_trajectory·task_mapping 인코딩 |
| 10:50 | project_extractor MVP — 92 사업 / 81 예산 |
| 11:00 | 예산 추출 regex 수정 — 84/92 |
| 11:10 | 분류 체인 전량 (AI·tech·std·strategy) + legal basis + 뷰 다수 |
| 11:30 | 정밀화 5건: 성과지표 표 + NER 확장 + 법적근거 3모드 + 연락처 + 3 뷰(AI spoke/tech-body/strategy) |
| 11:45 | AI 연계 가중치 + 2 heatmap 뷰(과제×기술·부처×기술) |

## 해결된 미결정 사항
- ~~프런트 스택~~: 단일 HTML (Alpine+Tailwind+D3/Chart.js CDN)
- ~~18개 기술 분류 출처~~: 제6차 기본계획 p.12
- ~~12대 vs 13개~~: 6차 실제 13개, 5차 12개 — 명칭 관성
- ~~AI 연계 가중치 산식~~: `count × log₁₀(1+budget)` (Phase 3.5 완료)
