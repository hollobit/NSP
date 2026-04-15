---
description: 파이프라인 8단계 전체 재실행 (PDF → JSON → HTML)
allowed-tools: Bash, Read
---

# Full Rebuild

```
!bash /Users/jonghongjeon/git/nsb/scripts/build.sh
```

실행 후:
- 페이로드 크기 확인
- 각 단계 stdout 요약
- 정합성 invariants 체크 (@.claude/agents/data-validator.md 의 command 실행)

이상 시 `data-validator` agent 디스패치하여 진단.
