# Catálogo de Anti-Patterns

Knowledge base for **Phase 2**. Each entry: what to look for (language-agnostic signal), why it's a problem, and the severity to assign. Severity follows the project-wide rubric:

- **CRITICAL** — breaks correct operation, exposes sensitive data, or fully collapses separation of responsibilities.
- **HIGH** — strong MVC/SOLID violation that makes maintenance/testing hard.
- **MEDIUM** — standardization/duplication/moderate performance problems.
- **LOW** — readability, naming, magic numbers.

Cite exact file + line(s) for every match. Point each finding at its corresponding pattern in `refactoring-playbook.md`.

---

## CRITICAL

### AP-01 · Hardcoded Secrets / Credentials
**Signal:** API keys, DB passwords, SMTP credentials, JWT/session secret keys, or payment-gateway keys written as string literals in source (`SECRET_KEY = "..."`, `dbPass: "..."`, `paymentGatewayKey: "..."`). Applies even if the value "looks like" a placeholder — if it ships in the repo, it's compromised the moment the repo is shared.
**Why:** Anyone with read access to the code (or git history) gets production credentials. Cannot be rotated without a deploy.
**Playbook:** RP-01 (Extract config to environment variables).

### AP-02 · SQL Injection
**Signal:** SQL built via string concatenation or f-strings/template literals with values that originate from request input (`"SELECT * FROM x WHERE id = " + id`, `` `... ${input}` ``), or any endpoint that executes a client-supplied raw query string.
**Why:** Direct path to full database compromise (read/write/delete any data, bypass auth).
**Playbook:** RP-02 (Parameterized queries / ORM).

### AP-03 · God Class / God Module
**Signal:** One file/class owns persistence, business rules, and orchestration for *multiple unrelated domains* (e.g. a single `models.py` with SQL for products, users and orders; a single class doing DB setup + routing + payment processing + reporting). Rule of thumb: if removing one domain's code requires touching lines that belong to a different domain in the same file, it's a god module.
**Why:** Impossible to test or reason about in isolation; any change risks breaking unrelated features.
**Playbook:** RP-03 (Split by domain into models/controllers).

### AP-04 · Plaintext or Weakly-Hashed Passwords
**Signal:** Passwords stored as-is (no hashing at all), hashed with a broken/inappropriate primitive (MD5, SHA1, a hand-rolled "hash" function), or returned verbatim in API responses (`to_dict()`/serializer includes the password/hash field).
**Why:** A single DB leak compromises every user's real-world password (password reuse across sites).
**Playbook:** RP-04 (Proper password hashing + response serialization that excludes secrets).

### AP-05 · Unauthenticated Destructive / Admin Endpoint
**Signal:** Routes that reset/wipe data, run arbitrary code, or execute arbitrary client-supplied queries/commands, reachable with no authentication or authorization check (`/admin/*` with no auth middleware, an endpoint that `execute()`s a `sql` field taken straight from the request body).
**Why:** Anyone who finds the URL can destroy or exfiltrate all data.
**Playbook:** RP-05 (Auth/role-gated admin routes; remove raw-query execution endpoints entirely).

---

## HIGH

### AP-06 · Fat Controller / Business Logic in Route Handlers
**Signal:** Route handlers (or the request-handling function) directly containing multi-step business rules — discount calculation, stock checks, payment status decisions, aggregation math — rather than delegating to a controller/service and only shaping the HTTP response.
**Why:** Business rules can't be reused or unit-tested independently of the HTTP layer; routes balloon in size.
**Playbook:** RP-06 (Extract to Controller layer).

### AP-07 · Tight Coupling / No Dependency Injection
**Signal:** Direct use of a module-level global connection/singleton (`global db_connection`, a DB handle created once at import time and reached into from anywhere) instead of an injected/managed resource; hard-coded `new` of concrete classes deep inside business logic instead of passing dependencies in.
**Why:** Cannot substitute a test double, cannot control lifecycle, hidden shared state across requests.
**Playbook:** RP-07 (Dependency injection / composition root).

### AP-08 · Broken or Fake Authentication
**Signal:** Auth "tokens" that are predictable/derivable (`'fake-jwt-token-' + user.id`), issued but never verified by a middleware/guard on subsequent requests, or an auth flow that never checks the returned token at all.
**Why:** Anyone can forge a valid-looking token for any user id; auth is security theater.
**Playbook:** RP-08 (Real token issuance/verification behind middleware).

### AP-09 · Uncontrolled Global Mutable State
**Signal:** Module-level mutable containers (`let cache = {}`, `let total = 0`) written to from request handlers and shared across all requests/users.
**Why:** Race conditions under concurrent requests, state leaks between unrelated requests, untestable in isolation.
**Playbook:** RP-09 (Move state into request-scoped or properly managed storage).

### AP-10 · Sensitive Data Logged or Exposed in Responses
**Signal:** Full credit-card numbers, passwords, secret keys, or tokens written to `console.log`/`print`, or included in a JSON response body (e.g. a `/health` endpoint that echoes back `secret_key`).
**Why:** Leaks sensitive data into logs (often shipped to third-party log aggregators) or directly to any API caller.
**Playbook:** RP-10 (Redact/remove sensitive fields from logs and responses).

---

## MEDIUM

### AP-11 · N+1 Query Problem
**Signal:** A loop over a result set that issues one additional query per iteration to fetch related data (fetch orders, then per-order fetch items, then per-item fetch product name) instead of a join/eager-load.
**Why:** Query count scales linearly with data size; kills performance at any real scale.
**Playbook:** RP-11 (Join / eager loading / batch fetch).

### AP-12 · Missing Input Validation / Inconsistent Response Contracts
**Signal:** Endpoints that trust request fields without checking type/range/presence beyond a bare existence check, or a set of endpoints where success/error response shapes are inconsistent (`{erro: ...}` vs `{error: ...}` vs a plain text `res.send(...)`).
**Why:** Invalid data reaches the persistence layer; API consumers can't handle errors uniformly.
**Playbook:** RP-12 (Centralized validation + consistent envelope).

### AP-13 · Duplicated Business Logic
**Signal:** The same non-trivial rule (e.g. an "is this overdue" calculation, a discount tier calculation) re-implemented with copy-pasted branching logic in 2+ places instead of calling one shared function/method.
**Why:** Logic drifts — a bugfix or rule change applied to one copy silently doesn't apply to the others.
**Playbook:** RP-13 (Extract to a single reusable method).

### AP-14 · Missing Pagination on List Endpoints
**Signal:** A "list all" endpoint that runs `SELECT *`/`Model.query.all()` with no limit/offset/cursor and returns every row.
**Why:** Response size and query cost grow unbounded with data volume; eventual outage.
**Playbook:** RP-14 (Add pagination parameters).

---

## LOW

### AP-15 · Magic Numbers / Hardcoded Constants
**Signal:** Bare numeric/string literals with business meaning scattered inline (`if len(nome) > 200`, `if p >= 1 and p <= 5`) instead of named constants.
**Why:** Meaning isn't self-evident; the same limit has to be hunted down and changed in every occurrence.
**Playbook:** RP-15 (Named constants module).

### AP-16 · Poor Naming
**Signal:** Single-letter or cryptic identifiers for non-trivial values (`u`, `e`, `p`, `cc`, `cid` for user/email/password/card/course-id).
**Why:** Code requires re-deriving meaning from context every time it's read.
**Playbook:** RP-16 (Descriptive renames).

### AP-17 · print()/console.log-Based Logging
**Signal:** Ad hoc `print("ERRO: " + ...)` / `console.log(...)` calls used as the only error/audit trail, with no levels, structure, or log framework.
**Why:** No way to filter by severity, no timestamps/structure for production log aggregation.
**Playbook:** RP-17 (Structured logging module).

### AP-18 · Overly Broad Exception Handling
**Signal:** Bare `except:` (Python) or an empty/blanket `catch` that swallows all errors and returns a generic message, discarding the actual cause.
**Why:** Hides real bugs, makes production incidents undebuggable, can mask non-recoverable errors that should propagate.
**Playbook:** RP-18 (Catch specific exceptions, centralize handling).

---

## Deprecated / Obsolete API Detection

Always check for these regardless of the domain-specific findings above; report any match as its own finding with the severity that fits its actual impact (usually MEDIUM, HIGH if it also creates a security gap):

| Deprecated / discouraged usage | Modern replacement |
|---|---|
| Python `hashlib.md5()` / `sha1()` for password hashing | `werkzeug.security.generate_password_hash` (PBKDF2) or `bcrypt`/`argon2-cffi` |
| Flask `app.run(debug=True)` left on for what is otherwise treated as the production entry point | `debug` driven by an environment variable, defaulting to `False`; use a WSGI server (gunicorn/waitress) for real deployment |
| Node `sqlite3` package's callback-style API (`db.run(sql, cb)`, `db.get(sql, cb)`) used for new code | `sqlite3`'s promise wrapper, or `better-sqlite3` (synchronous, no callback pyramids), or an async ORM (Prisma/Sequelize with `async/await`) |
| Node `Buffer.from(x).toString('base64')` hand-rolled as a "hash"/crypto primitive | Node's built-in `crypto` module (`crypto.scrypt`, `crypto.pbkdf2`) or `bcrypt` — never invent a crypto primitive |
| Manual `for` loops building dict/object output field-by-field where the model already defines a serializer (`to_dict()`/`toJSON()`) | Call the existing serializer; keep one source of truth for the wire format |
| Flask's implicit reliance on `app.add_url_rule` wired directly to bare functions with no blueprint separation | Flask `Blueprint`s (or the framework's router/module system) per resource |

If the project pins a framework version in its manifest, cross-check whether that specific version has since deprecated something you observe in use (e.g. an old middleware signature); note it even if not listed above — this table is a starting point, not an exhaustive list.
