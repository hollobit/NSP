# .claude/ — Harness v3 Configuration

NSP (국가 표준화 통합 대시보드) 프로젝트의 Claude Code harness 구성.

## 구조

```
.claude/
├── README.md                  ← 이 파일
├── settings.json              ← 전역 권한 + env
├── settings.local.json        ← 로컬 override (gitignore 아님, 실험용)
├── agents/
│   ├── pdf-parser.md          ← PDF 파싱 정밀화 전문가
│   ├── widget-builder.md      ← UI 위젯 구현가
│   ├── dashboard-deployer.md  ← hollobit/NSP 배포 관리
│   └── data-validator.md      ← 정합성 검증
├── commands/
│   ├── sync.md                ← /sync — 빌드 + 원격 push
│   ├── rebuild.md             ← /rebuild — 파이프라인 전체 재실행
│   ├── verify.md              ← /verify — invariants 검증
│   └── plan.md                ← /plan — Plans.md 상태 조회
├── hooks/
│   ├── pre-commit-build-check.sh   ← 빌드 누락 방지
│   └── post-build-verify.sh         ← 빌드 후 무결성 체크
├── sessions/                  ← 세션 아카이브
├── state/                     ← 런타임 상태 (자동 관리)
├── logs/                      ← 실행 로그
└── memory/                    ← 지속 기억
```

## Quick Commands

| 명령 | 효과 |
|------|------|
| `/rebuild` | PDF → JSON → HTML 8단계 재실행 |
| `/verify` | 정합성 invariants 체크 (92 사업·2,688억원 등) |
| `/sync` | 빌드 후 hollobit/NSP main으로 push |
| `/plan` | Plans.md 상태 + Task 요약 |

## Specialist Agents

| Agent | 언제 호출? |
|---|---|
| `pdf-parser` | 추출 누락 복구 · 법적근거/성과지표 정밀화 · 예산 unknown 복원 |
| `widget-builder` | 신규 대시보드 위젯 · SVG 차트 · 반응형 레이아웃 |
| `dashboard-deployer` | 원격 push · 커밋 메시지 작성 · safety guard |
| `data-validator` | 빌드 후 회귀 감지 · 커버리지 리포트 |

## Hooks

- **pre-commit-build-check**: `git commit` 전에 dist/ 가 최신인지 확인 (template.html 변경 vs dist 타임스탬프)
- **post-build-verify**: `bash scripts/build.sh` 후 payload 크기·getter 포함 여부 확인

훅 활성화 (선택):

```jsonc
// settings.json 에 추가
"hooks": {
  "PreToolUse": [{
    "matcher": "Bash(git:commit:*)",
    "hooks": [{"type": "command", "command": ".claude/hooks/pre-commit-build-check.sh"}]
  }],
  "PostToolUse": [{
    "matcher": "Bash(bash:scripts/build.sh)",
    "hooks": [{"type": "command", "command": ".claude/hooks/post-build-verify.sh"}]
  }]
}
```

## Invariants (NSP 프로젝트 상수)

- 92 사업 · 2,688억원 (268,781 백만원) · 13 과제 · 18 부처 · 18 기술 · 46+ 표준기구
- 법적근거 ≥ 15/18 부처 · 성과지표 ≥ 17/18 · 연락처 18/18
- AI explicit ≥ 24 사업 · 순AI 예산 ≥ 10,000 백만

상기 수치 회귀 시 `data-validator` 로 진단.

## Related Docs

- 프로젝트 헌장: [@CLAUDE.md](/Users/jonghongjeon/git/nsb/CLAUDE.md)
- 태스크 계획: [@Plans.md](/Users/jonghongjeon/git/nsb/Plans.md)
- 데이터 모델: [@docs/data_model.md](/Users/jonghongjeon/git/nsb/docs/data_model.md)
- 기술 스택: [@docs/tech_stack.md](/Users/jonghongjeon/git/nsb/docs/tech_stack.md)
- 아키텍처: [@docs/architecture.md](/Users/jonghongjeon/git/nsb/docs/architecture.md)
