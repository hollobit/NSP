---
description: 로컬 빌드 → dist/index.html 원격 동기화 (hollobit/NSP main)
argument-hint: [--skip-build] [--message "커밋 메시지"]
allowed-tools: Bash, Read, Edit
---

# Sync Dashboard to Remote

## Steps

```
!echo "== 1. Build =="
!bash /Users/jonghongjeon/git/nsb/scripts/build.sh 2>&1 | tail -5

!echo "== 2. Staging =="
!cp /Users/jonghongjeon/git/nsb/dist/index.html /tmp/nsp-publish/index.html
!cp /Users/jonghongjeon/git/nsb/README.md /tmp/nsp-publish/README.md

!echo "== 3. Diff preview =="
!cd /tmp/nsp-publish && git pull --rebase origin main -q && git add index.html README.md && git diff --cached --stat

!echo "== 4. Commit + Push =="
```

사용자 지시($ARGUMENTS) 에 따라 커밋 메시지 결정 후 push.

push 후 원격 커밋 URL 출력: `https://github.com/hollobit/NSP/commit/<sha>`

## Safety

- 빌드 실패 시 중단
- `git pull --rebase` 충돌 시 중단하고 사용자 확인
- force push 금지
