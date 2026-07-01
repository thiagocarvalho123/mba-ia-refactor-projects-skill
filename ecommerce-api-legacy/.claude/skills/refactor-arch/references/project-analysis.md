# Análise de Projeto — Heurísticas de Detecção

Knowledge base for **Phase 1**. Goal: identify stack and current architecture from *evidence in the repo*, never from assumptions about "what this challenge probably contains".

## 1. Language detection

Look at file extensions and manifest files, in this priority order:

| Signal | Language |
|---|---|
| `requirements.txt`, `Pipfile`, `pyproject.toml`, `*.py` | Python |
| `package.json`, `*.js`/`*.ts`/`*.mjs` | JavaScript / TypeScript |
| `go.mod`, `*.go` | Go |
| `pom.xml`, `build.gradle`, `*.java` | Java |
| `Gemfile`, `*.rb` | Ruby |
| `composer.json`, `*.php` | PHP |

If more than one is present, the language with the actual application entry point (see §4) wins; the others are tooling/scripts.

## 2. Framework + version detection

- Python: read `requirements.txt`/`pyproject.toml` for `flask`, `django`, `fastapi`, etc., and capture the pinned version. Confirm by checking imports (`from flask import Flask`, `Flask(__name__)`).
- Node: read `package.json` `dependencies` for `express`, `koa`, `fastify`, `nestjs`, etc. Confirm via `require('express')` / `import express from 'express'`.
- Never report a framework you didn't confirm via an actual import/require in the source — the manifest can list something unused.

## 3. Dependencies worth calling out

Report dependencies that materially affect architecture or security posture: ORMs (`flask-sqlalchemy`, `sequelize`, `prisma`), DB drivers (`sqlite3`, `pg`, `mysqlclient`), CORS packages, auth/crypto libraries (or their conspicuous absence, e.g. no `bcrypt`/`argon2`/`jsonwebtoken` in a project that hand-rolls auth).

## 4. Entry point & routing surface

Find the composition root: the file that creates the app instance and either registers routes directly or mounts routers/blueprints (`app.py`, `src/app.js`, `main.py`, `index.js`...). Enumerate every route it exposes (method + path), and note whether routes are registered inline (`app.add_url_rule(...)`, `app.get(...)`) or through some intermediate grouping (blueprints, routers). This route list is what Phase 3 validation will re-test.

## 5. Domain inference

Do not label the domain generically ("a CRUD API"). Infer the actual business domain from:
- Route/resource names (`/produtos`, `/pedidos` → e-commerce; `/checkout`, `/enrollments`, `/courses` → LMS/e-learning; `/tasks`, `/categories` → task management).
- Table/model field names (e.g. `estoque`, `preco` → inventory/pricing domain; `enrollment_id`, `course_id` → course enrollment domain).
- Any README/docstring in the project.

State the domain in one line, e.g. "E-commerce API (produtos, pedidos, usuários)" or "LMS API with checkout flow".

## 6. Database detection

- Look for a DB driver import/connection string (`sqlite3.connect(...)`, `new sqlite3.Database(...)`, `create_engine(...)`, `mongoose.connect(...)`).
- Determine whether persistence is via raw SQL strings, a query builder, or an ORM (SQLAlchemy models, Sequelize models, Prisma schema).
- Enumerate table/collection names from `CREATE TABLE` statements, ORM model classes (`db.Model` subclasses, `sequelize.define`), or schema files.
- Note whether the DB is file-based, in-memory, or external — this affects how Phase 3 validation is run (an in-memory DB resets on every boot, which is fine for validation but must be flagged as a finding if used as if it were persistent).

## 7. Current architecture mapping

Classify the current shape using these buckets (pick the closest, describe deviations):

- **Monolithic / single-file**: essentially all logic (routing, business rules, persistence) lives in one or two files.
- **Ad-hoc multi-file, no layering**: split into files by technical accident (e.g. `controllers.py` + `models.py` + `database.py`) but each file still mixes concerns that don't belong together (e.g. "models.py" contains raw SQL *and* is the only place validation-adjacent logic lives).
- **Partially layered**: there's a recognizable `models/`, `routes/`, `services/` structure, but responsibilities still leak across boundaries (routes doing business logic, models the only thing with correct boundaries).
- **MVC-aligned**: models, views/routes, and controllers are each doing only their job, config and error handling are centralized.

Describe *why* you picked that bucket in one line — this becomes the `Architecture:` line of the Phase 1 summary, e.g. "Monolítica — tudo em 4 arquivos, sem separação de camadas" or "Parcialmente organizada — models/routes/services existem mas lógica de negócio vaza para as routes".

## 8. Counting source files

Count only files you actually analyzed as application source (exclude generated DB files, lockfiles, virtualenvs, `node_modules`, `.git`, caches, and this skill's own directory). State the count and roughly how many lines of code it represents — this number must match what Phase 2 references when citing files.
