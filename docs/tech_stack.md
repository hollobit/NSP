# 기술 스택 (확정 — 단일 HTML 자립형)

## 핵심 원칙
> **"빌드 도구 없이 `index.html` 한 파일로 완결"**
> GitHub Pages에 파일 하나만 올리면 동작 — 가장 낮은 운영 비용.

## 파이프라인
- **PDF 파싱**: Python 3.11+ · `pdfplumber` · LLM 보조 분류(선택)
- **빌드 방식**: Python 스크립트가 JSON을 HTML 템플릿에 **인라인 주입** → 단일 `index.html` 출력
  - `scripts/build_html.py`: 템플릿(`src/web/template.html`) + `data/processed/*.json` → `dist/index.html`
  - 데이터는 `<script type="application/json" id="nsb-data">...</script>`로 삽입
  - `file://` 로도 동작 (CORS·fetch 불필요, 오프라인 뷰어 기능 보너스)

## 웹 (단일 HTML)
- **런타임**: CDN 기반 (빌드 도구 없음)
  - **Alpine.js** (~15KB, 반응형 상태/이벤트) — React 대신 초경량 선택
  - **Tailwind CSS Play CDN** (`cdn.tailwindcss.com`) — 개발 편의, 설정 불필요
  - **Chart.js** (차트) — Recharts 대비 CDN 친화적
  - **D3.js** (18×18 매트릭스 heatmap + AI spoke 네트워크)
  - **Fuse.js** (검색, UMD 빌드)
- **라우팅**: URL hash 기반 (`#/tech/T01`) — 바닐라 `window.addEventListener('hashchange')`
- **데이터 로드**: 페이지 로드 시 `document.getElementById('nsb-data').textContent` 파싱 → Alpine store

## 산출물 구조
```
dist/
└── index.html   (단일 파일: HTML + CDN 태그 + 인라인 JSON + 인라인 JS)
```

(데이터가 커지면 `dist/data.json`으로 분리 옵션, 기본은 인라인)

## 배포
- **GitHub Pages**: `dist/index.html`을 루트에 올리면 즉시 동작
- `.github/workflows/deploy.yml`: Python 파싱 + HTML 생성 → `actions/upload-pages-artifact` → `deploy-pages`
- 리포 Settings → Pages → Source: **GitHub Actions**
- **경로 문제 無**: 상대 경로도 없음(단일 파일), `base` 설정 불필요

## 임계치 정책
| 인라인 데이터 크기 | 조치 |
|---|---|
| < 500KB | 인라인 유지 (기본) |
| 500KB ~ 2MB | 인라인 유지 + gzip(GH Pages 자동) |
| > 2MB | `dist/data.json`으로 분리하고 `fetch('./data.json')` |

(18개 부처 × 수십 사업 예상 → 충분히 2MB 미만 유지 가능)

## 개발 원칙
- 원본 PDF 절대 수정 금지 (`.claude/settings.local.json` write deny)
- 가공 데이터에 버전·타임스탬프 포함
- 수치(예산)는 **반드시 원문 페이지 cite**
- CDN URL은 **버전 고정** (예: `alpinejs@3.14.1`) — 공급망 위험 완화
