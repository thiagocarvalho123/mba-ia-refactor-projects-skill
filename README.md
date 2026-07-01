# Skill `refactor-arch` — Refatoração Arquitetural Automatizada

> Entrega do desafio "Criação de Skills — Refatoração Arquitetural Automatizada" do MBA. O enunciado original do desafio está preservado no histórico do git (commit `6d1ce62`); este arquivo é a documentação da solução, conforme pedido no enunciado.

**Ferramenta usada:** Claude Code (`.claude/skills/refactor-arch/`).

---

## A) Análise Manual

Antes de construir a skill, os 3 projetos foram lidos arquivo a arquivo para entender os problemas reais que a skill precisaria detectar. Os achados completos (com arquivo/linha exatos, impacto e recomendação) estão nos relatórios de auditoria em `reports/audit-project-{1,2,3}.md` — a auditoria automatizada da Fase 2 da skill reproduziu e formalizou essa análise manual. Abaixo, um resumo por projeto.

### Projeto 1 — `code-smells-project` (Python/Flask, monólito de 4 arquivos)

| Severidade | Achado | Por que importa |
|---|---|---|
| CRITICAL | SQL Injection — todo `models.py` concatena strings SQL com input da request (`"...WHERE id = " + str(id)`) | Qualquer endpoint que repassa entrada do usuário é explorável para ler/alterar/apagar dados; login pode ser contornado com `' OR '1'='1` |
| CRITICAL | `/admin/reset-db` e `/admin/query` sem autenticação, o segundo executa SQL arbitrário do corpo da requisição | Qualquer pessoa com a URL apaga o banco inteiro ou roda comandos SQL arbitrários |
| CRITICAL | Senhas gravadas e comparadas em texto plano, e devolvidas no JSON de `/usuarios` | Um vazamento do banco (ou uma simples chamada à API) expõe a senha real de todo usuário |
| HIGH | `/health` devolve `secret_key` e `debug: true` no JSON de resposta | Endpoint público vaza a chave de assinatura da aplicação |
| MEDIUM | N+1 queries ao listar pedidos (cursor aninhado por pedido → por item → por produto) | Custo cresce linearmente com pedidos × itens, sem uso de `JOIN` |
| MEDIUM | Nenhum endpoint de listagem pagina resultados | Resposta e custo de query crescem sem limite |
| LOW | Listas de categorias válidas e limites de tamanho hardcoded inline, duplicáveis a cada endpoint | Mudar a regra exige lembrar de atualizar todo lugar onde foi copiada |
| LOW | Logging inteiro via `print()` | Sem níveis/timestamps, impossível filtrar em produção |

### Projeto 2 — `ecommerce-api-legacy` (Node.js/Express, "God Class" `AppManager`)

| Severidade | Achado | Por que importa |
|---|---|---|
| CRITICAL | Credenciais e chave de gateway de pagamento hardcoded em `utils.js` (`pk_live_...`) | Vazamento do repositório expõe uma chave que parece ser de produção |
| CRITICAL | `badCrypto()` não é hash — é Base64 repetido e cortado, reversível sem força bruta | Falsa sensação de segurança: senha é recuperável trivialmente se o banco vazar |
| CRITICAL | Número completo de cartão e chave do gateway logados em `console.log` a cada checkout | Violação direta de PCI-DSS |
| CRITICAL | `DELETE /api/users/:id` sem autenticação e sem limpar matrículas/pagamentos relacionados | Qualquer um apaga qualquer usuário e corrompe integridade referencial do banco |
| HIGH | `GET /api/admin/financial-report` sem autenticação devolve faturamento e PII de alunos | Dados financeiros e pessoais publicamente acessíveis |
| MEDIUM | Estado global mutável (`globalCache`, `totalRevenue`) escrito por qualquer requisição | Condição de corrida / vazamento de dados entre usuários sob concorrência |
| MEDIUM | API `sqlite3` em estilo callback + banco só em memória (API obsoleta) | Callback hell e nenhuma persistência real entre execuções |
| LOW | Variáveis de uma/duas letras no checkout (`u`, `e`, `p`, `cc`) | Cada leitura exige redescobrir o significado pelo contexto |

### Projeto 3 — `task-manager-api` (Python/Flask, já parcialmente em camadas)

| Severidade | Achado | Por que importa |
|---|---|---|
| CRITICAL | Senhas com hash MD5 não salgado (`hashlib.md5`) | MD5 é revertível via rainbow table; sem salt, ainda pior |
| CRITICAL | `SECRET_KEY` hardcoded em `app.py` e credenciais SMTP hardcoded em código morto (`notification_service.py`, nunca importado) | Segredos versionados mesmo em um recurso nunca ativado |
| CRITICAL | `User.to_dict()` devolve o hash da senha em toda resposta que serializa um usuário | Qualquer chamador da API recebe o hash da senha para ataque offline |
| HIGH | `POST /login` devolve `'fake-jwt-token-' + user.id`, e nenhuma rota verifica token algum | Autenticação é só teatro — toda rota aceita qualquer requisição, autenticada ou não |
| HIGH | Cálculo de "atrasada" duplicado em 3+ lugares nas rotas, em vez de usar `Task.is_overdue()` que já existe no model | Um `models/task.py` já com os métodos certos, mas ignorado pelas rotas |
| MEDIUM | N+1: relatório de produtividade roda uma query por usuário dentro de um loop Python | Custo O(usuários) a mais a cada chamada do relatório mais usado do sistema |
| MEDIUM | Nenhum endpoint de listagem pagina resultados | Resposta cresce sem limite |
| LOW | `utils/helpers.py` define constantes (`VALID_STATUSES`, `MAX_TITLE_LENGTH`...) que nenhuma rota usa — as rotas repetem os mesmos literais | Fonte "oficial" da regra não é a fonte real usada pelo código |

---

## B) Construção da Skill

A skill vive em `.claude/skills/refactor-arch/` (obrigatória em `code-smells-project/`, depois copiada verbatim para os outros dois projetos) e é composta por:

```
.claude/skills/refactor-arch/
├── SKILL.md                              # o "prompt" — as 3 fases, o que fazer em cada uma
└── references/
    ├── project-analysis.md               # heurísticas de detecção (Fase 1)
    ├── anti-patterns-catalog.md          # catálogo de anti-patterns + APIs depreciadas (Fase 2)
    ├── report-template.md                # formato fixo do relatório de auditoria (Fase 2)
    ├── architecture-guidelines.md        # regras do MVC alvo (Fase 3)
    └── refactoring-playbook.md           # 18 padrões de transformação antes/depois (Fase 3)
```

**Decisões de design:**

- **`SKILL.md` como orquestrador fino.** Ele não contém heurísticas de detecção nem exemplos de código — só define a sequência das 3 fases, os banners de saída exigidos, o gate de confirmação obrigatório entre a Fase 2 e a Fase 3, e a instrução explícita de carregar cada arquivo de `references/` antes de agir. Todo o conhecimento de domínio (o "como" detectar/corrigir) vive nos arquivos de referência, para que o `SKILL.md` permaneça curto e sirva de índice.
- **Catálogo de anti-patterns com 18 entradas, distribuídas por severidade** (5 CRITICAL, 5 HIGH, 4 MEDIUM, 4 LOW — AP-01 a AP-18), acima do mínimo de 8 pedido. Cada entrada tem sinais de detecção concretos e acionáveis (ex.: "string SQL montada com `+` usando input da request", não "SQL ruim"). Incluí uma tabela dedicada de **APIs depreciadas/obsoletas** (MD5 para senha, `app.run(debug=True)` fixo, API de callback do `sqlite3`, crypto caseira via Base64) — cada uma das 3 execuções reais encontrou pelo menos uma entrada dessa tabela.
- **Playbook com 18 padrões RP-01..RP-18, um para cada AP**, cada um com exemplo de código antes/depois em pseudocódigo agnóstico de linguagem — acima do mínimo de 8 pedido.
- **Agnosticismo de tecnologia** garantido de duas formas: (1) nada em `SKILL.md` ou nos `references/` cita Python, Flask, JavaScript, nomes de tabela ou de rota — todo fato específico de projeto só existe no output da Fase 1/2, nunca nas instruções da skill; (2) as `architecture-guidelines.md` definem responsabilidades por camada (Config/Models/Views-Routes/Controllers/Middlewares) em vez de nomes de pasta fixos, com uma regra explícita de migração — **"Adapt, don't template"**: se o projeto já tem `models/`, `routes/`, `services/` (caso do projeto 3), a skill deve evoluir essa estrutura em vez de inventar uma estrutura paralela.
- **Gate de confirmação humano é hard-coded como obrigatório** no `SKILL.md` ("Stop. Ask explicitly... Do not touch a single file... until the human responds affirmatively"), não uma sugestão — foi respeitado nas 3 execuções via prompt de confirmação explícito antes de qualquer alteração de arquivo.

**Desafios encontrados:**

- **Projeto 3 já tinha camadas parciais** (`models/`, `routes/`, `services/`, `utils/`), mas com toda a regra de negócio e validação ainda duplicada dentro das rotas, e um `services/notification_service.py` inteiramente morto carregando um segredo hardcoded. A regra "adapt, don't template" evitou o erro óbvio de jogar fora uma estrutura já razoável — em vez disso, a Fase 3 adicionou apenas as camadas que faltavam (`config/`, `controllers/`, `middlewares/`) e passou a *usar* código que já existia (`Task.is_overdue()`, `process_task_data()`, constantes de `helpers.py`) em vez de duplicá-lo de novo.
- **Preservar contrato público vs. corrigir falha de segurança real.** A regra de migração do `architecture-guidelines.md` permite quebrar comportamento quando o comportamento original *é* a falha de segurança auditada (ex.: projeto 2 deixava dados órfãos ao deletar usuário; projeto 3 não verificava token algum). Cada uma dessas mudanças foi documentada explicitamente na mensagem de commit do projeto correspondente, não escondida.
- **Ambiente com proxy corporativo hardcoded no `npm` global** quebrou silenciosamente toda instalação de pacote no projeto 2 (erro genérico "Exit handler never called!", sem menção ao proxy). Resolvido contornando por comando (`--proxy null --https-proxy null --registry https://registry.npmjs.org/`) sem tocar na configuração global do usuário.

---

## C) Resultados

### Resumo das auditorias (Fase 2)

| Projeto | Stack | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|---|
| 1 — code-smells-project | Python/Flask | 5 | 3 | 3 | 2 | 13 |
| 2 — ecommerce-api-legacy | Node.js/Express | 4 | 4 | 3 | 2 | 13 |
| 3 — task-manager-api | Python/Flask (parcialmente em camadas) | 3 | 4 | 3 | 2 | 12 |

Relatórios completos: [`reports/audit-project-1.md`](reports/audit-project-1.md), [`reports/audit-project-2.md`](reports/audit-project-2.md), [`reports/audit-project-3.md`](reports/audit-project-3.md).

### Antes / Depois da estrutura

**Projeto 1** — de 4 arquivos (`app.py`, `controllers.py`, `models.py`, `database.py`) para:
```
src/
├── app.py (composition root)
├── config/{settings,database}.py
├── models/{produto,usuario,pedido}_model.py
├── views/{produto,usuario,pedido,admin}_routes.py
├── controllers/{produto,usuario,pedido,admin}_controller.py
├── middlewares/{auth,error_handler}.py
└── utils/{constants,pagination,responses}.py
```

**Projeto 2** — de 3 arquivos (`app.js`, `AppManager.js` "God Class", `utils.js`) para:
```
src/
├── app.js (composition root)
├── config/{settings,database}.js
├── models/{user,course,enrollment,payment,audit_log,report}_model.js
├── routes/{checkout,admin}_routes.js
├── controllers/{checkout,report,user}_controller.js
├── middlewares/{auth,error_handler}.js
└── utils/{crypto,card,logger}.js
```

**Projeto 3** — evoluiu a estrutura parcial já existente (`models/`, `routes/`, `services/`, `utils/`) em vez de recriá-la:
```
task-manager-api/
├── app.py (composition root)
├── config/settings.py                    # NOVO
├── controllers/                          # NOVO — lógica extraída das rotas
│   ├── task_controller.py
│   ├── user_controller.py
│   ├── report_controller.py
│   └── category_controller.py
├── middlewares/{auth,error_handler}.py   # NOVO
├── models/{task,user,category}.py        # mantidos, corrigidos (hash de senha, to_dict)
├── routes/{task,user,report}_routes.py   # mantidos, agora finos
├── utils/{helpers,logger}.py             # logger novo; helpers agora usado de verdade
└── services/                             # notification_service.py removido (morto + segredo hardcoded)
```

### Checklist de validação (preenchido para os 3 projetos)

**Fase 1 — Análise**
- [x] Linguagem detectada corretamente (Python nos projetos 1/3, JavaScript no projeto 2)
- [x] Framework detectado corretamente (Flask 3.1.1/3.0.0, Express 4.18.2)
- [x] Domínio da aplicação descrito corretamente (e-commerce, LMS/checkout, task manager)
- [x] Número de arquivos analisados condiz com a realidade (4, 3, 11 arquivos respectivamente)

**Fase 2 — Auditoria**
- [x] Relatório segue o template definido em `report-template.md`
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (13, 13 e 12 respectivamente)
- [x] Detecção de APIs deprecated incluída (MD5, `debug=True`, sqlite3 callback API, badCrypto)
- [x] Skill pausa e pede confirmação antes da Fase 3 (confirmado via prompt explícito nos 3 projetos)

**Fase 3 — Refatoração**
- [x] Estrutura de diretórios segue padrão MVC
- [x] Configuração extraída para módulo de config (sem hardcoded) — confirmado via grep pelos segredos originais, zero ocorrências fora de config/defaults de dev
- [x] Models criados/corrigidos para abstrair dados
- [x] Views/Routes separadas para roteamento
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado (middleware único por projeto)
- [x] Entry point claro (composition root único)
- [x] Aplicação inicia sem erros (validado via boot real + `curl` nos 3 projetos)
- [x] Endpoints originais respondem corretamente

### Logs de validação (resumo)

**Projeto 1** — `curl` contra todos os endpoints CRUD de produtos/usuários/pedidos, login, `/health` (não vaza mais `secret_key`/`debug`), `/admin/reset-db` (403 sem token, 200 com token), `/admin/query` removido (404), tentativa de SQL injection na URL retorna 404 em vez de 500.

**Projeto 2** — checkout (sucesso, recusa, curso inexistente, campos faltando), `/api/admin/financial-report` (403 sem token / 200 com token, mesmos números do relatório original agora via `JOIN`), `DELETE /api/users/:id` (403 sem token / com token agora faz cascade de matrículas e pagamentos — antes deixava dados órfãos), rota 404 retorna JSON.

**Projeto 3** — servidor sobe, `seed.py` popula 3 usuários / 4 categorias / 10 tasks; `POST /tasks` sem token → 401; com token → 201; `DELETE /users/2` sem token admin → 401, com token de usuário não-admin → 403, com token admin → 200 (cascade de tasks confirmado: total caiu de 11 para 8 após deletar um usuário com 3 tasks); `GET /reports/summary` reproduz os mesmos números do loop original, agora via `GROUP BY`; `POST /categories` com cor inválida → 400; rota inexistente → JSON 404; login com senha errada → 401; nenhuma resposta de usuário inclui o hash da senha.

### Observações sobre comportamento em stacks diferentes

A mesma skill, sem nenhuma alteração em `SKILL.md` ou nos `references/`, produziu resultados coerentes em Python/Flask monolítico (projeto 1), Node.js/Express orientado a classe única (projeto 2) e Python/Flask parcialmente em camadas (projeto 3). A diferença mais visível entre execuções não foi o *que* a skill procurou (o catálogo de 18 anti-patterns é o mesmo), mas o *volume de mudança estrutural* na Fase 3: os projetos 1 e 2 exigiram criar toda a árvore de diretórios do zero, enquanto o projeto 3 exigiu principalmente extrair lógica de dentro de arquivos que já estavam nos lugares certos — validando a regra "adapt, don't template" do guia de arquitetura.

---

## D) Como Executar

### Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) instalado e autenticado
- Python 3.11+ e `pip` (projetos 1 e 3)
- Node.js 18+ e `npm` (projeto 2)

### Rodar a skill em cada projeto

```bash
# Projeto 1 — Python/Flask
cd code-smells-project
claude "/refactor-arch"

# Projeto 2 — Node.js/Express (skill já copiada para .claude/skills/refactor-arch/)
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3 — Python/Flask parcialmente em camadas (skill já copiada)
cd ../task-manager-api
claude "/refactor-arch"
```

Em cada execução, revise o relatório impresso ao final da Fase 2 e responda `y` ao prompt `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` para prosseguir com a Fase 3.

### Como validar que a refatoração funcionou

**Projeto 1:**
```bash
cd code-smells-project
python -m venv .venv && .venv/Scripts/activate  # ou source .venv/bin/activate no Linux/Mac
pip install -r requirements.txt
python src/app.py
# em outro terminal:
curl http://127.0.0.1:5000/health
curl http://127.0.0.1:5000/produtos
```

**Projeto 2:**
```bash
cd ecommerce-api-legacy
npm install
node src/app.js
# em outro terminal:
curl http://127.0.0.1:3000/api/admin/financial-report   # 403 sem X-Admin-Token
```

**Projeto 3:**
```bash
cd task-manager-api
python -m venv .venv && .venv/Scripts/activate
pip install -r requirements.txt
python seed.py
python app.py
# em outro terminal:
curl http://127.0.0.1:5000/health
curl http://127.0.0.1:5000/tasks
curl -X POST http://127.0.0.1:5000/login -H "Content-Type: application/json" -d '{"email":"joao@email.com","password":"1234"}'
```

Os relatórios de auditoria já gerados estão em `reports/`, e o código refatorado de cada projeto já está commitado no histórico do git.
