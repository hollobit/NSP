# 국가 표준화 통합 대시보드 — Plans.md

작성일: 2026-04-15
완료된 이전 Phase → @docs/plans_archive.md

---

## ✅ 완료 (2026-04-15)

### 개요 위젯 11개 (스프린트 완료 · f2b76cc 푸시)

| Task | 내용 | Status |
|------|------|--------|
| 1.1  | Top-10 예산 사업 카드 | cc:완료 |
| 1.2  | 13과제 예산 도넛 (SVG) | cc:완료 |
| 1.3  | 부처 Top-5 예산 가로 bar | cc:완료 |
| 1.4  | 4대 분야(D1-D4) 분포 | cc:완료 |
| 2.1  | AI 3-해상도 비교 | cc:완료 |
| 2.2  | AI 간접 과제 Top-5 | cc:완료 |
| 3.1  | 5차→6차 목표 sparkline × 5 | cc:완료 |
| 3.2  | 예산 편성 상태 도넛 | cc:완료 |
| 3.3  | 데이터 커버리지 게이지 × 4 | cc:완료 |
| 4.1  | 표준화기구 Top-10 | cc:완료 |
| 4.2  | 공적/사실상 트랙 도넛 | cc:완료 |
| 5.1  | 개요 레이아웃 재조직 | cc:완료 |
| 5.2  | 빌드·검증 (517KB) | cc:완료 |
| 5.3  | hollobit/NSP main push | cc:완료 |

### Harness v3 구성 (완료)

| Task | 내용 | Status |
|------|------|--------|
| H.1  | `.claude/settings.json` 권한·env 정의 | cc:완료 |
| H.2  | 전문 에이전트 4개 (pdf-parser/widget-builder/dashboard-deployer/data-validator) | cc:완료 |
| H.3  | 슬래시 커맨드 4개 (/rebuild · /verify · /sync · /plan) | cc:완료 |
| H.4  | 훅 2개 (pre-commit-build-check · post-build-verify) | cc:완료 |
| H.5  | .claude/README.md 구성 가이드 | cc:완료 |

---

## 🎯 남은 작업

### Phase 10 — 연도별 계획 추출 및 다축 연계 (2026-2030)

> **목표**: PDF 원문에서 2026~2030년 연도별 계획 데이터를 정밀 추출하고,
> 부처별·과제별·예산별·성과지표별로 교차 연계하여 연도별 변화를 추적할 수 있는 대시보드 뷰를 구축한다.

#### Step A — 성과지표 정밀 재추출 (파서 개선)

| Task | 내용 | DoD | Depends | Status | Owner |
|------|------|-----|---------|--------|-------|
| 10.1 | `impl_plan.py` 성과지표 표 파서 리팩토링 — 셀 병합·줄바꿈 분리 | 산업부 등 오염 데이터 클린업, 18부처 전부 개별 지표 분리 | - | cc:완료 | pdf-parser |
| 10.2 | 성과지표 fallback 12부처 원문 재조사 — 고유 PI 존재 여부 확인 | 12부처 각각에 대해 "고유성과지표 없음(공통만)" vs "추출 실패" 판별 | - | cc:완료 | pdf-parser |
| 10.3 | 부처별 성과지표 `yearly[]` 정규화 — `{year, plan_value, plan_unit, actual}` 구조 통일 | 모든 PI의 yearly가 int/float + unit으로 파싱 (문자열 혼합 제거) | 10.1 | cc:완료 | pdf-parser |
| 10.4 | `performance_indicators.v1.json` 독립 산출물 생성 | 부처×지표×연도 flat 테이블, 검증용 집계 stats 포함 | 10.3 | cc:완료 | pdf-parser |

#### Step B — 기본계획 PDF 연도별 목표 추출

| Task | 내용 | DoD | Depends | Status | Owner |
|------|------|-----|---------|--------|-------|
| 10.5 | 기본계획 PDF p.30 연도별 예산 추출 (18부처 × 5년) | `budget_trajectory.v1.json` — 총 1.49조원, 18부처 완전 커버 | - | cc:완료 | pdf-parser |
| 10.6 | 13과제별 연도별 예산 집계 + 타임라인 | `task_timeline.v1.json` — 과제×연도 agency_yearly_budget | - | cc:완료 | pdf-parser |
| 10.7 | `goal_trajectory.v1.json` 보강 — 2026-2029 선형보간 추가 | 2/5 목표 보간 완료, 3/5 지표범위 변경으로 보간 불가 표시 | - | cc:완료 | pdf-parser |

#### Step C — 다축 연계 인덱스 구축

| Task | 내용 | DoD | Depends | Status | Owner |
|------|------|-----|---------|--------|-------|
| 10.8 | 사업 KPI ↔ 부처 PI 자동 링크 (91/130, 70%) | `kpi_pi_links.v1.json` — 유사도 매칭 | 10.4 | cc:완료 | pdf-parser |
| 10.9 | 연도별 집계 JSON 생성 — `yearly_summary.v1.json` | 부처별·과제별·기술별 × 연도별 예산·지표 합산 피벗 | 10.4, 10.5 | cc:완료 | pdf-parser |

#### Step D — 대시보드 연도별 뷰

| Task | 내용 | DoD | Depends | Status | Owner |
|------|------|-----|---------|--------|-------|
| 10.10 | 연도별 탭 UI (예산추이/성과지표/로드맵 3탭) | Alpine.js 서브탭 전환, nav에 '연도별' 버튼 추가 | 10.9 | cc:완료 | widget-builder |
| 10.11 | 부처별 성과지표 카드 (도메인 배지 + 5년 값 + 미니바) | 부처 필터, D1-D4 배지, sparkline 바 | 10.4, 10.10 | cc:완료 | widget-builder |
| 10.12 | 과제별 연도 로드맵 (예산 기반 가로 바) | 13과제 × 5년 opacity 바 + 부처수/사업수 표시 | 10.6, 10.10 | cc:완료 | widget-builder |
| 10.13 | 예산 연도별 스택 bar chart (Top-5 부처) | Chart.js stacked bar, 부처별 테이블 (합계 포함) | 10.5, 10.10 | cc:완료 | widget-builder |
| 10.14 | 빌드·검증 (709KB, schema v0.5) | build_html.py에 4개 신규 JSON 통합, 데이터 검증 통과 | 10.10~10.13 | cc:완료 | - |

### Phase 6 — 데이터 정밀화 (Long-tail)

| Task | 내용 | DoD | Depends | Status | Owner |
|------|------|-----|---------|--------|-------|
| 6.1  | 법적근거 18/18 완료 (중기부 수동인코딩 포함) | 18/18 커버리지 | - | cc:완료 | pdf-parser |
| 6.2  | 예산 unknown 0건 (이전 Phase에서 해결) | unknown 0 | - | cc:완료 | pdf-parser |
| 6.3  | 성과지표 18/18 완료 (Phase 10에서 해결, 100개 PI) | 18/18 | - | cc:완료 | pdf-parser |
| 6.4  | 사실상표준기구 NER 보강 → 59개 기구 | ≥50 달성 (50→59) | - | cc:완료 | pdf-parser |
| 6.5  | 담당자 18/18 직위 분리 (접두사 패턴 추가) | 18/18 rank 파싱 | - | cc:완료 | pdf-parser |

### Phase 7 — 분석 기능 확장

| Task | 내용 | DoD | Depends | Status | Owner |
|------|------|-----|---------|--------|-------|
| 7.1  | 협력 관계 추출 → `cooperations.v1.json` (36건) | MOU/MRA/국제협력 패턴 추출 | - | cc:완료 | pdf-parser |
| 7.2  | 부처간 공동 기구 참여 매트릭스 | `agency_cooperation_matrix.v1.json` 20쌍 | 7.1 | cc:완료 | widget-builder |
| 7.3  | 전략 공백 리포트 (63% 점유, 80셀 공백) | `strategy_gaps.v1.json` + `docs/insights/gaps.md` | - | cc:완료 | - |
| 7.4  | 사업 비교 (최대 4건 side-by-side 모달) | 체크박스 + 비교 모달 9개 항목 | - | cc:완료 | widget-builder |
| 7.5  | CSV 내보내기 (필터 상태 기준) | 이전 Phase에서 구현 완료 | - | cc:완료 | widget-builder |
| 7.6  | 5축 Sankey (과제↔기술↔부처↔전략↔트랙) | D3 Sankey + 축 선택 UI | - | cc:완료 | widget-builder |

### Phase 8 — 품질·검증

| Task | 내용 | DoD | Depends | Status | Owner |
|------|------|-----|---------|--------|-------|
| 8.1  | pytest 108개 테스트 전부 통과 | budget·law·NER·PI·AI·tech·strategy 커버 | - | cc:완료 | - |
| 8.2  | AI explicit 25건 정밀도 **100%** | ≥90% 달성 (전문 포함 검증) | - | cc:완료 | - |
| 8.3  | 기술 태깅 85건 정밀도 **98.8%** | ≥85% 달성 | - | cc:완료 | - |
| 8.4  | 접근성 기본 aria 속성 추가 | role/aria-label 헤더·네비·메인 | - | cc:완료 | widget-builder |
| 8.5  | 오프라인(`file://`) 호환 검증 | fetch 0건, inline data, CDN만 외부 | - | cc:완료 | - |

### Phase 9 — 배포·운영

| Task | 내용 | DoD | Depends | Status | Owner |
|------|------|-----|---------|--------|-------|
| 9.1  | GitHub Pages 활성화 확인 | https://hollobit.github.io/NSP/ 접속 가능 | - | cc:TODO | - |
| 9.2  | 원격 PDF 저작권 검토 후 업로드 여부 결정 | 업로드 or `data/raw/` 공개 | - | cc:TODO | - |
| 9.3  | README 스크린샷·데모 GIF 추가 | 개요/AI 연계/기술×기구 3장 이상 | 9.1 | cc:TODO | - |
| 9.4  | 이슈 템플릿 (.github/ISSUE_TEMPLATE/) | bug/data_error/feature 3종 | - | cc:TODO | - |

---

## 🚫 위험 및 미결정

| 항목 | 상태 | 영향도 |
|------|------|--------|
| LLM 분류기 도입 시점 (rule-based 한계 시) | Phase 8 정밀도 결과 후 결정 | 중 |
| 원문 PDF 동봉 (저작권) | Phase 9.2 전 결정 | 중 |
| Sankey vs 대안 시각화 선택 | Phase 7.6 착수 전 | 하 |

---

## 우선순위 권장

Phase 6, 7, 8, 10 **전부 완료**. 남은 작업은 Phase 9 (배포·운영) 4건만.

1. **Phase 9.1 GitHub Pages 활성화** — 즉시 가치 실현
2. **Phase 9.3 README 스크린샷** — 데모 GIF
3. **Phase 9.4 이슈 템플릿** — 커뮤니티 준비
4. **Phase 9.2 PDF 저작권 검토** — 의사결정 필요
