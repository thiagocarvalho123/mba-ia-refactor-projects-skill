# Template do Relatório de Auditoria

Knowledge base for the artifact printed (and, when the invoking project has a `reports/` directory convention, saved) at the end of **Phase 2**. Fill every placeholder with real data gathered in Phase 1/2 — never leave a placeholder literally in the output.

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <project folder name>
Stack:   <language> + <framework>
Files:   <N> analyzed | ~<LOC> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [<SEVERITY>] <Anti-pattern name>
File: <path>:<line or line-range>
Description: <what is actually in the code — be concrete, quote it if useful>
Impact: <what can go wrong because of this, stated concretely>
Recommendation: <the transformation to apply, referencing the playbook pattern by name>

### [<SEVERITY>] <Anti-pattern name>
File: <path>:<line or line-range>
Description: ...
Impact: ...
Recommendation: ...

<... one block per finding ...>

================================
Total: <N> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## Rules for filling the template

1. **Ordering:** findings are listed strictly CRITICAL → HIGH → MEDIUM → LOW. Within the same severity, order by the file they appear in (top of the project down) so the report reads coherently against the codebase.
2. **File:line is mandatory and exact.** `File: models.py:1-350` for a range, `File: app.py:8` for a single line. Never say "throughout the file" without also giving the concrete lines you actually verified.
3. **Description must reference the real code**, not a category. "SECRET_KEY hardcoded as `'minha-chave-super-secreta-123'`" is acceptable; "bad security practice" is not.
4. **Impact is concrete and causal** — state what an attacker/user/maintainer can actually do because of this finding, not a generic warning.
5. **Recommendation names the playbook pattern** that Phase 3 will apply (e.g. "Apply RP-02: parameterize this query" ), so there's a direct thread from finding → fix.
6. **The summary counts must match the findings listed** — recompute them from the actual list, don't estimate.
7. **The confirmation prompt is part of the template, not optional flavor text.** The report is not complete without it, and Phase 3 must not start until it's answered.
8. If the invoking project's repository has a `reports/` directory at its root (sibling to the skill's project, per the challenge's expected layout), also write this exact report to `reports/audit-project-N.md` (infer N from which of the three challenge projects — or ask if ambiguous — otherwise just print it and let the human save it).
