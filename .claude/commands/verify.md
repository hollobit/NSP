---
description: 데이터 정합성 검증 (사업 수·예산·부처 커버리지)
allowed-tools: Bash, Read
---

# Verify Data Integrity

@.claude/agents/data-validator.md 의 invariants 검사 실행.

```
!cd /Users/jonghongjeon/git/nsb && python3 -c "
import json
p = json.load(open('data/processed/projects.v1.json'))
c = json.load(open('data/processed/core_tasks.v1.json'))
a = json.load(open('data/processed/agencies.v1.json'))
s = json.load(open('data/processed/std_bodies.v1.json'))
print('=== NSP Integrity Check ===')
print(f'Projects: {len(p[\"projects\"])} (expect 92)')
total_budget = sum(x['budget']['total_mil_krw'] for x in p['projects'])
print(f'Budget:   {total_budget:,} 백만원 (expect ~268,781)')
print(f'Tasks:    {len(c[\"tasks\"])} (expect 13)')
print(f'Agencies: {len(a[\"agencies\"])} (expect 18)')
with_laws = sum(1 for x in a['agencies'] if x.get('legal_basis'))
with_pi   = sum(1 for x in a['agencies'] if x.get('performance_indicators'))
with_con  = sum(1 for x in a['agencies'] if x.get('contact'))
print(f'Laws:     {with_laws}/18 agencies (expect >= 15)')
print(f'PIs:      {with_pi}/18 agencies (expect >= 17)')
print(f'Contact:  {with_con}/18 agencies (expect 18)')
print(f'AI exp:   {p[\"stats\"][\"ai_explicit\"]} sites (expect >= 24)')
print(f'AI dir:   {p[\"stats\"][\"ai_direct_pure_mil_krw\"]:,} 백만 (expect >= 10,000)')
print(f'Std bodies: {len(s[\"bodies\"])} (expect >= 46)')
"
```

결과 판정: PASS / WARN / FAIL.
