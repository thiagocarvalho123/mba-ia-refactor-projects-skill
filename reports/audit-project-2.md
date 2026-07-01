================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (Node.js)
Framework:      Express 4.18.2
Dependencies:  sqlite3 5.1.6
Domain:        LMS (Learning Management System) — cursos, matrículas, checkout/pagamento ("Frankenstein LMS")
Architecture:  Monolítica — entry point (src/app.js) instancia uma única classe "God Class" (AppManager) que concentra inicialização de banco, definição de rotas e toda a regra de negócio via callbacks aninhados; utils.js mistura configuração sensível com funções utilitárias e estado global mutável.
Source files:  3 files analyzed (src/app.js, src/AppManager.js, src/utils.js — ~183 linhas)
DB tables:     users, courses, enrollments, payments, audit_logs (SQLite em memória, recriado a cada boot)
================================

================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   Node.js + Express
Files:   3 analyzed | ~183 lines of code

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 3 | LOW: 2

## Findings

### [CRITICAL] Credenciais e Chaves Hardcoded (AP-01)
File: src/utils.js:2-6
Description: `config` expõe `dbUser`, `dbPass` ("senha_super_secreta_prod_123"), `paymentGatewayKey` ("pk_live_1234567890abcdef") e `smtpUser` como literais de string direto no código-fonte.
Impact: Qualquer pessoa com acesso ao repositório (inclusive histórico do git) tem acesso a uma chave de gateway de pagamento que parece de produção (`pk_live_...`) e a credenciais de banco/SMTP.
Recommendation: Aplicar RP-01 — mover para variáveis de ambiente, sem valores reais versionados.

### [CRITICAL] Função de "Hash" de Senha Forjada / Crypto Caseira (AP-04 + API Depreciada)
File: src/utils.js:17-23; src/AppManager.js:68
Description: `badCrypto()` não é um hash — é 10.000 repetições de `Buffer.from(pwd).toString('base64').substring(0,2)` cortadas em 10 caracteres. Como a saída é puramente derivada de uma codificação Base64 (reversível), a "senha" pode ser recuperada com engenharia reversa trivial, sem força bruta.
Impact: Compromisso total de qualquer senha armazenada assim que o banco vazar; falsa sensação de segurança pior do que não hashear (o time acredita estar protegido).
Recommendation: Aplicar RP-04 — substituir por `bcrypt`/`crypto.scrypt` (ver tabela de APIs depreciadas: nunca inventar primitivas de criptografia).

### [CRITICAL] Dados Sensíveis de Pagamento Logados (AP-10)
File: src/AppManager.js:45
Description: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` grava o número completo do cartão de crédito **e** a chave do gateway de pagamento em texto plano no log a cada checkout.
Impact: Qualquer sistema de agregação de logs (ou acesso ao servidor) expõe dados de cartão de titular — violação direta de PCI-DSS — e a chave secreta do gateway.
Recommendation: Aplicar RP-10 — nunca logar PAN completo (mascarar, ex.: `**** **** **** 4444`) nem segredos de configuração.

### [CRITICAL] Endpoint Destrutivo Sem Autenticação Corrompe Integridade Referencial (AP-05)
File: src/AppManager.js:131-137
Description: `DELETE /api/users/:id` apaga o usuário sem qualquer verificação de autenticação/autorização, e não remove `enrollments`/`payments` relacionados — o próprio código reconhece isso na mensagem de retorno ("mas as matrículas e pagamentos ficaram sujos no banco").
Impact: Qualquer pessoa com a URL pode apagar qualquer usuário e deixar o banco em estado inconsistente (matrículas/pagamentos órfãos), quebrando relatórios e possivelmente permitindo reuso indevido de IDs.
Recommendation: Aplicar RP-05 — proteger a rota com middleware de autenticação/autorização e, ao excluir, tratar (cascata ou soft delete) os registros dependentes.

### [HIGH] Relatório Financeiro/PII Exposto Sem Autenticação (AP-05)
File: src/AppManager.js:80-129
Description: `GET /api/admin/financial-report` devolve faturamento por curso e nome/e-mail de cada aluno matriculado sem qualquer checagem de autenticação/autorização.
Impact: Dados financeiros e PII de alunos ficam publicamente acessíveis a qualquer um que descubra a URL.
Recommendation: Aplicar RP-05 — proteger todas as rotas `/api/admin/*` com middleware de autenticação/autorização.

### [HIGH] N+1 Queries em Callbacks Aninhados (AP-11)
File: src/AppManager.js:83-127
Description: Para montar o relatório, o código busca todos os cursos e, para cada curso, busca matrículas; para cada matrícula, dispara mais duas queries aninhadas (usuário e pagamento) — 4 níveis de callbacks, com o número de queries crescendo como O(cursos × matrículas).
Impact: Gargalo de performance severo assim que o volume de dados crescer; código quase impossível de acompanhar por causa do aninhamento ("callback hell").
Recommendation: Aplicar RP-11 — substituir por uma única query com `JOIN` entre courses, enrollments, users e payments (ou migrar para uma API baseada em Promises/async-await).

### [HIGH] God Class — AppManager Concentra Banco, Rotas e Toda a Regra de Negócio (AP-03)
File: src/AppManager.js:1-141
Description: Uma única classe é responsável por inicializar o schema do banco (`initDb`), registrar todas as rotas HTTP (`setupRoutes`) e executar toda a lógica de checkout, relatório e exclusão de usuário — sem nenhuma separação entre camadas.
Impact: Impossível testar qualquer regra de negócio isoladamente do Express; qualquer mudança em uma rota arrisca efeito colateral nas demais por compartilharem a mesma classe e a mesma conexão `this.db`.
Recommendation: Aplicar RP-03 — dividir em `models/` (acesso a dados por domínio), `controllers/` (orquestração) e `config/database.js` (conexão).

### [HIGH] Regra de Negócio Completa Dentro do Handler de Rota (AP-06)
File: src/AppManager.js:28-78
Description: O handler de `POST /api/checkout` contém validação de entrada, consulta de curso, consulta/criação de usuário, hashing de senha, decisão de aprovação de pagamento (`cc.startsWith("4")`), criação de matrícula, criação de pagamento e escrita de log de auditoria — tudo em uma única função anônima fortemente aninhada.
Impact: Nenhuma dessas regras pode ser reutilizada ou testada sem simular uma requisição Express completa; a função é praticamente ilegível.
Recommendation: Aplicar RP-06 — extrair para `controllers/checkout_controller.js`, mantendo a rota apenas como tradução HTTP.

### [MEDIUM] Estado Global Mutável (AP-09)
File: src/utils.js:9-10, 12-15
Description: `globalCache` e `totalRevenue` são variáveis mutáveis no escopo do módulo, escritas por `logAndCache()` a partir de qualquer requisição, sem nenhum escopo por requisição ou usuário.
Impact: Sob concorrência, requisições de usuários diferentes leem/escrevem o mesmo estado compartilhado (condição de corrida, vazamento de dados de cache entre usuários).
Recommendation: Aplicar RP-09 — remover o cache de módulo ad hoc ou substituí-lo por um armazenamento com escopo/TTL adequado (ex.: um cache real com chave por requisição).

### [MEDIUM] API sqlite3 em Estilo Callback + Banco Apenas em Memória (Deprecated/Obsolete API)
File: src/AppManager.js:1, 7, 12-21, 37-77, 83-127, 133
Description: Todo o acesso a dados usa a API de callback do pacote `sqlite3` (`db.run(sql, cb)`, `db.get(sql, cb)`, `db.all(sql, cb)`), e o banco é `:memory:` — todos os dados (incluindo cursos e matrículas seed) são perdidos a cada reinício do processo.
Impact: Pirâmides de callback (ver findings acima) e nenhuma persistência real entre execuções, inviabilizando o uso em qualquer ambiente que não seja demonstração local.
Recommendation: Conforme a tabela de APIs depreciadas do catálogo, migrar para a API baseada em Promises do `sqlite3`, `better-sqlite3` (síncrono) ou um ORM assíncrono, e apontar para um arquivo `.db` persistente configurável por variável de ambiente.

### [LOW] Nomenclatura Pouco Descritiva (AP-16)
File: src/AppManager.js:29-33
Description: Variáveis de entrada do checkout usam nomes de uma ou duas letras sem relação óbvia com o domínio: `u`, `e`, `p`, `cid`, `cc` para usuário, e-mail, senha, id do curso e cartão.
Impact: Cada leitura do código exige redescobrir o significado de cada variável a partir do contexto.
Recommendation: Aplicar RP-16 — renomear para `username`, `email`, `password`, `courseId`, `cardNumber`.

### [LOW] Contrato de Resposta Inconsistente (AP-12)
File: src/AppManager.js:35, 38, 41, 48, 51, 55, 60, 70, 135
Description: Alguns erros retornam texto plano via `res.status(...).send("...")` (ex.: "Bad Request", "Curso não encontrado") enquanto sucessos retornam JSON via `res.json(...)`/`res.status(200).json(...)` — não há um envelope de resposta único.
Impact: Clientes da API precisam tratar dois formatos de resposta diferentes dependendo do caminho de erro, dificultando integração e testes automatizados.
Recommendation: Aplicar RP-12 — padronizar todas as respostas (sucesso e erro) em um envelope JSON único.

================================
Total: 13 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
