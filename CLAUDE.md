# NSB — 국가표준기본계획 · 시행계획 통합 대시보드

## 프로젝트 목적
`pdf/` 폴더의 두 공식 문서(제6차 국가표준기본계획 2026-2030, 2026 시행계획)를 구조화 데이터로 변환하고,
**18개 핵심 기술 × 18개 부처 × 사업/예산**을 AI 중심 연계로 탐색할 수 있는 웹 대시보드를 구축한다.

## 원본 문서
| 파일 | 역할 |
|------|------|
| `pdf/제6차 국가표준기본계획(2026-2030).pdf` | 5년 마스터플랜 (4대 분야 × 12대 과제, 18개 기술분류 선정 p.12) |
| `pdf/2026 시행계획.pdf` | 18개 부처청 × 세부사업/예산 (202p) |

## 참조 문서
- 데이터 모델 → @docs/data_model.md
- 기술 스택·배포 → @docs/tech_stack.md
- 아키텍처·데이터 플로우 → @docs/architecture.md
- 18개 기술 taxonomy → @docs/tech_taxonomy.md
- 태스크 플랜 → @Plans.md

## 디렉토리 구조
```
nsb/
├── pdf/                   # 원본 (read-only)
├── data/{raw,processed}/  # 가공 JSON (버전·타임스탬프)
├── src/{parser,web}/      # Python 파서 + Vite 프런트엔드
├── scripts/               # 빌드/추출 엔트리포인트
├── docs/                  # 설계·스키마
├── .claude/               # 하네스 설정
├── Plans.md
└── CLAUDE.md
```

## 핵심 원칙 (요약)
- 원본 PDF 절대 수정 금지 — `.claude/settings.local.json`에서 write deny
- 모든 가공 데이터는 원문 페이지 cite 필수
- 빌드 재현성: `scripts/build.sh` 한 번으로 PDF→JSON→웹 빌드 완결
- GitHub Actions로 자동 배포 (PDF 커밋만으로 대시보드 갱신)
