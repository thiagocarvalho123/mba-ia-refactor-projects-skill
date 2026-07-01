# Guidelines de Arquitetura — Padrão MVC Alvo

Knowledge base for **Phase 3**. Defines the target architecture every refactor converges on, independent of language. Adapt file extensions and idioms to the detected stack (Python module vs JS file, etc.) but keep the layer boundaries below non-negotiable.

## Layers and responsibilities

### Config (`src/config/`)
- Owns environment-driven configuration: secrets, connection strings, ports, feature flags.
- Nothing outside this layer reads `process.env`/`os.environ` directly — everything else imports the resolved config object.
- Ships with safe local defaults so the app still boots with zero manual setup, but never with a hardcoded *secret* — random/dev-only secrets are generated or read from a `.env.example` documented default, not committed as a real production-looking value.

### Models (`src/models/`)
- Owns data shape and persistence access for exactly one domain concept (one file per entity: `produto_model.py`, `user.model.js`, etc. — never one file for every entity).
- Contains: schema/columns, query methods for that entity (parameterized/ORM — never raw string-built SQL), serialization to a safe public shape (excludes password hashes, internal-only fields).
- Does **not** contain: HTTP concerns (no `request`/`response` objects), cross-domain orchestration (a Product model doesn't create Orders), or business rules that span multiple entities.

### Views / Routes (`src/views/` or `src/routes/`)
- Owns the mapping from HTTP method+path to a controller action, and request-shape concerns only: reading params/body, calling the controller, translating the controller's result into an HTTP status + JSON body.
- Does **not** contain: business logic, validation rules beyond "is this the right shape to even call the controller", direct DB access.
- Group by resource (one router/blueprint per domain), not one giant file registering every route.

### Controllers (`src/controllers/`)
- Owns the orchestration flow for a use case: validate input, call one or more models, apply business rules (discounts, stock checks, status transitions), decide the outcome, hand a plain result back to the view layer.
- Framework-agnostic where possible — a controller function should be testable by calling it directly with plain arguments, not by simulating an HTTP request.
- One controller module per domain, mirroring the models split.

### Middlewares (`src/middlewares/`)
- Owns cross-cutting concerns applied uniformly: centralized error handling (catch what bubbles up, log it once, return a consistent error envelope), authentication/authorization checks, request logging.
- Anti-pattern AP-05/AP-08 fixes land here: admin/destructive routes get an auth-check middleware, not an inline `if` in the route.

### Entry point (`src/app.<ext>` or equivalent — the composition root)
- The one place that: reads config, constructs the app instance, wires models/db, registers routers/blueprints, registers middlewares, starts listening.
- Contains no business logic and no route handler bodies itself.

## Migration rules (apply regardless of starting shape)

1. **Never break the public contract.** Every route path, method, and response shape that existed before the refactor must still exist and behave equivalently after — this is a structural refactor, not a rewrite. If a bug in the original behavior is also a security hole (e.g. plaintext passwords), fixing it is expected and the audit report should already have flagged it as CRITICAL/HIGH; document the behavior change in the completion summary.
2. **One concern per file.** If a file is doing two of {routing, controlling, modeling, configuring}, it isn't done being split yet.
3. **No global mutable singletons.** Database connections/clients are constructed once in config or the entry point and passed down (via app context, dependency injection, or the framework's idiomatic mechanism) — not reached into as a bare module-level global from deep inside business logic.
4. **Adapt, don't template.** A project that already has `models/`, `routes/`, `services/` is not "wrong" just because it doesn't match this exact folder naming — evaluate whether the *responsibilities* are correctly separated, and only move things that are actually misplaced (e.g. business logic sitting in a route file even though a `services/` folder already exists — move it into services/controllers, don't invent a parallel structure).
5. **Errors are centralized.** Route/controller code should not each hand-roll their own `try/except`/`try/catch` boilerplate with ad hoc string messages — a middleware (or framework-level error handler) catches unhandled errors once and returns a consistent shape.
6. **Config is centralized and secret-free.** After refactor, `grep`-ing the repo for the literal secret values found in Phase 2 should return nothing outside of `.env`/environment configuration.
