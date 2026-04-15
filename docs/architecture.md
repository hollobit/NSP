# NSB 아키텍처 개요

## 데이터 플로우

```
pdf/*.pdf  ──[pdfplumber]──▶  data/raw/*.pages.json
                                       │
                                       ▼
                        [src/parser/master_plan.py]
                        [src/parser/impl_plan.py]
                        [src/parser/project_extractor.py]
                                       │
                                       ▼
                        data/processed/{master,impl,projects}.v1.json
                                       │
                                       ▼
                        [src/parser/ai_classify.py] [tech_classify.py]
                                       │
                                       ▼
                        [src/parser/matrix_builder.py] [ai_linkage.py] [aggregate.py]
                                       │
                                       ▼
                        data/processed/*.v1.json  (multi-file)
                                       │
                        ┌──────────────┴──────────────┐
                        ▼                              ▼
            scripts/build_html.py            scripts/export_csv.py
    (template.html + JSON 인라인 주입)
                        │
                        ▼
              dist/index.html   (단일 자립형 파일)
                        │
                        ▼
                  GitHub Pages
```

## 컴포넌트 책임

### 1. Parser Layer (`src/parser/`)
- **단일 책임**: PDF 원문 → 스키마 준수 JSON
- 파생 정보(AI 태깅 등)는 별도 모듈로 분리
- 모든 필드에 `source: {file, page, bbox}` 포함 → 검증·cite 필수

### 2. Classifier Layer (`src/parser/ai_classify.py`)
- 1차: 키워드 규칙 (빠르고 결정적)
- 2차: 저신뢰(중복 매칭/키워드 부재) 건만 LLM 호출
- 결과는 원본을 **수정하지 않고** 별도 어노테이션 파일로 저장

### 3. Matrix Layer (`src/parser/matrix_builder.py`)
- 12대 과제 × 18부처 교차 인덱스 생성
- 시행계획 개요표(p.2 "O/-")를 ground truth로 활용

### 4. Web Layer — 단일 HTML 자립형
- `src/web/template.html` (템플릿) + Python 빌더가 JSON 인라인 주입 → `dist/index.html` **단일 파일**
- **CDN 런타임**: Alpine.js · Tailwind Play CDN · Chart.js · D3 · Fuse.js (버전 고정)
- 라우팅: URL hash (`#/tech/T01?agency=A02`) — 공유 가능한 링크
- 데이터: `<script type="application/json" id="nsb-data">`에 인라인, `file://`에서도 동작
- 배포: GitHub Actions → Pages (단일 파일 업로드)

## 불변 원칙

1. **원본 PDF는 절대 수정하지 않음** (settings에서 write deny)
2. **모든 가공 데이터에 버전·타임스탬프** (`v1`, `generated_at` 필드)
3. **금액은 반드시 원문 페이지 cite** (검증·신뢰성)
4. **파이프라인은 재실행 가능** (`scripts/build.sh` 한 번으로 end-to-end)
