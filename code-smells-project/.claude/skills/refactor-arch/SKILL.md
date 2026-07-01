---
name: refactor-arch
description: Analyzes a backend codebase (any language/framework), audits it for architectural and security anti-patterns, and refactors it to the MVC pattern after human confirmation. Use when asked to "refactor architecture", "audit code smells", "convert to MVC", or invoked as /refactor-arch.
---

# refactor-arch — Automated Architectural Refactoring

You are acting as an architecture auditor and refactoring engineer. You operate on the codebase rooted at the current working directory (the project that invoked this skill — never a different project). You are **technology-agnostic**: nothing in this skill should assume Python, Flask, JavaScript or any specific stack. Detect the stack from evidence, don't assume it.

This skill runs in exactly **3 sequential phases**. Do not skip a phase, do not merge phases, and do not silently reorder them. Print the section headers exactly as shown below (the `====...====` banners) so the phases are visually distinguishable in the transcript.

Load the reference files in `references/` before acting — they are not optional background reading, they are the knowledge base this skill runs on:

| File | Used in |
|---|---|
| `references/project-analysis.md` | Phase 1 |
| `references/anti-patterns-catalog.md` | Phase 2 |
| `references/report-template.md` | Phase 2 |
| `references/architecture-guidelines.md` | Phase 3 |
| `references/refactoring-playbook.md` | Phase 3 |

---

## Phase 1 — Análise (Project Analysis)

Goal: understand what you're dealing with before judging it.

1. Walk the project tree (skip `node_modules/`, `.git/`, `venv/`, `__pycache__/`, `.claude/`, lockfiles) and read every source file.
2. Apply the heuristics in `references/project-analysis.md` to determine: language, framework + version, key dependencies, the application's domain (infer it from route names, table names, model fields — don't guess generically), the current architectural shape (monolithic single-file, ad-hoc multi-file, partially layered, etc.), and how many source files exist.
3. Detect the persistence layer (DB engine, ORM vs raw SQL, table names) from code, not from assumptions.
4. Print a summary in this exact shape (fill in real values, keep the banner style):

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <detected>
Framework:      <detected + version if known>
Dependencies:  <notable deps>
Domain:        <inferred business domain>
Architecture:  <one-line description of current structure>
Source files:  <N> files analyzed
DB tables:     <table/collection names>
================================
```

Do not proceed to Phase 2 in the same breath without this summary existing in the transcript first.

## Phase 2 — Auditoria (Audit)

Goal: produce an evidence-based, severity-ranked findings report — and stop.

1. Cross-reference every source file against `references/anti-patterns-catalog.md`. For every match, record: the anti-pattern name, exact file path, exact line number(s), a description of what's wrong grounded in the actual code (quote or paraphrase it, don't be generic), the impact, and a recommendation pointing at the relevant transformation in `references/refactoring-playbook.md`.
2. Explicitly check for deprecated/obsolete API usage (see the "Deprecated APIs" section of the catalog) and include any matches as findings with the modern replacement named.
3. Assign severity per finding using the CRITICAL/HIGH/MEDIUM/LOW rubric in the catalog. Do not inflate or deflate severity to hit a quota — but do keep looking until you have found real findings; a production-grade audit of a legacy backend essentially never has fewer than 5.
4. Render the full report using `references/report-template.md`. Findings **must** be sorted CRITICAL → HIGH → MEDIUM → LOW, each with a summary count at the top.
5. Print the report to the transcript in full.
6. **Stop.** Ask explicitly: `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`. Do not touch a single file, do not begin Phase 3 planning, until the human responds affirmatively. If the answer is no, stop the skill entirely and wait for further instructions. This gate is mandatory, not a formality — the report is the artifact a human reviews before any code changes happen.

## Phase 3 — Refatoração (Refactoring)

Goal: eliminate the audited findings by restructuring the project onto the MVC pattern described in `references/architecture-guidelines.md`, using the concrete transformations in `references/refactoring-playbook.md`. Only start this phase after explicit human confirmation from Phase 2.

1. Design the target directory layout per `references/architecture-guidelines.md`, adapted to the language's idioms (e.g. `src/models`, `src/views` or `src/routes`, `src/controllers`, `src/middlewares`, `src/config`, plus a clear composition-root entry point). If the project already has partial layering, evolve it — don't gratuitously rename things that are already correctly placed.
2. Apply the refactoring playbook pattern-by-pattern: extract configuration/secrets to a config module (env vars, no hardcoded credentials), split any "god" file into per-domain models, move business logic out of routes into controllers, parameterize all SQL / use the ORM correctly, centralize error handling, remove dead code and deprecated API usage, fix the specific issues named in the Phase 2 report.
3. Preserve all existing external behavior: same routes, same request/response contracts, same status codes — this is a structural refactor, not a rewrite of functionality. New env-driven config must have working defaults so the app still boots with zero manual setup.
4. Validate the result:
   - Boot the application and confirm it starts without errors.
   - Exercise the original endpoints (the ones enumerated in Phase 1/2) and confirm they still respond with equivalent success/error semantics.
   - Confirm none of the CRITICAL/HIGH findings from the audit remain exploitable in the new structure.
5. Print a completion summary in this shape:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<tree of the new src/ layout>

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero anti-patterns remaining
================================
```

If validation fails, fix the regression before declaring the phase complete — do not report success on a broken app.

## Operating rules

- Never invent findings or metrics; every number in every report must trace back to something you actually read in the code.
- Be specific in detection signals and recommendations ("raw SQL string built via `+` concatenation with request input at models.py:28", not "bad code").
- This skill must work unmodified on any backend project dropped into its working directory — don't hardcode project-specific names, table names, or route paths anywhere in this file or the references. Project-specific facts belong in the Phase 1/2 output, never in the skill's instructions.
