================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:      Flask 3.0.0
Dependencies:  flask-sqlalchemy 3.1.1, flask-cors 4.0.0, marshmallow 3.20.1 (unused), requests 2.31.0, python-dotenv 1.0.0 (unused)
Domain:        Task Manager API (tarefas, usuários, categorias, relatórios)
Architecture:  Parcialmente em camadas — já existem pastas models/, routes/, services/, utils/ (base MVC melhor do que os projetos 1 e 2), mas as rotas concentram toda a validação e regra de negócio (que deveria estar em controllers/services), utils/helpers.py define uma função de validação (`process_task_data`) e constantes que nunca são usadas pelas rotas (que duplicam a mesma lógica inline), e services/notification_service.py define uma classe que não é importada/instanciada em lugar nenhum do app.
Source files:  11 files analyzed (app.py, database.py, seed.py, models/task.py, models/user.py, models/category.py, routes/task_routes.py, routes/user_routes.py, routes/report_routes.py, services/notification_service.py, utils/helpers.py — ~1160 linhas)
DB tables:     tasks, users, categories
================================

================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask (parcialmente em camadas)
Files:   11 analyzed | ~1160 lines of code

## Summary
CRITICAL: 3 | HIGH: 4 | MEDIUM: 3 | LOW: 2

## Findings

### [CRITICAL] Senhas com Hash MD5 Não Salgado (AP-04 + API Depreciada)
File: models/user.py:3, 27-32
Description: `set_password`/`check_password` usam `hashlib.md5(pwd.encode()).hexdigest()` — MD5 é criptograficamente quebrado e, sem salt, é trivialmente revertível via rainbow tables.
Impact: Um vazamento do banco expõe a senha real de todos os usuários com esforço mínimo de quebra.
Recommendation: Aplicar RP-04 — migrar para `werkzeug.security.generate_password_hash`/`check_password_hash` (PBKDF2) ou `bcrypt`.

### [CRITICAL] Segredos Hardcoded (Chave de Sessão e Credenciais SMTP) (AP-01)
File: app.py:13; services/notification_service.py:9-10
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'` está fixo no código; `NotificationService` também traz `email_user`/`email_password` ('taskmanager@gmail.com'/'senha123') hardcoded — e essa classe nem chega a ser instanciada em nenhum lugar do app (código morto que já nasce vazando uma credencial).
Impact: Qualquer acesso ao repositório expõe a chave de sessão da aplicação e uma credencial de e-mail, mesmo que o recurso de notificação nunca tenha sido de fato ativado.
Recommendation: Aplicar RP-01 — mover para variáveis de ambiente; remover ou reativar `NotificationService` de forma consciente (ver finding de código morto abaixo).

### [CRITICAL] Hash de Senha Devolvido em Respostas da API (AP-04)
File: models/user.py:16-25 (to_dict); routes/user_routes.py:33 (get_user), 85 (create_user), 129 (update_user), 209 (login)
Description: `User.to_dict()` inclui o campo `password` (o hash MD5) em toda resposta que serializa um usuário — `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login` devolvem o hash da senha no JSON.
Impact: Qualquer chamador da API (mesmo sem acesso ao banco) recebe o hash da senha de qualquer usuário consultado, habilitando ataque offline de força bruta/rainbow table.
Recommendation: Aplicar RP-04 — remover `password` da serialização pública; se necessário internamente, usar um método de serialização separado que nunca é exposto pela API.

### [HIGH] Token de Autenticação Falso e Nunca Verificado (AP-08)
File: routes/user_routes.py:210
Description: `POST /login` devolve `'token': 'fake-jwt-token-' + str(user.id)` — um valor previsível e forjável — e nenhuma rota do sistema (`grep` por verificação de token retorna vazio) checa esse ou qualquer outro token antes de servir a requisição.
Impact: Autenticação é apenas teatro: qualquer cliente pode forjar um token válido para qualquer `user_id`, e mesmo sem token nenhum, toda rota (incluindo criar/editar/deletar usuários e tasks) responde normalmente.
Recommendation: Aplicar RP-08 — emitir um token real (JWT assinado ou sessão) e adicionar um middleware de autenticação que valida o token em toda rota que precisa de usuário autenticado, com checagem de `role` (`is_admin()`) nas rotas administrativas.

### [HIGH] Regra de Negócio e Validação Completas Dentro das Rotas (AP-06)
File: routes/task_routes.py:86-154 (create_task), 156-223 (update_task); routes/user_routes.py:42-90 (create_user), 92-132 (update_user)
Description: Apesar de o projeto já ter pastas `models/`, `services/`, `utils/`, as rotas de tasks e usuários contêm toda a validação de campos (tamanho de título, faixa de prioridade, formato de e-mail, regras de status/role) e a orquestração de persistência diretamente no handler HTTP, sem delegar a um controller/service.
Impact: Nenhuma dessas regras pode ser testada ou reutilizada fora do contexto de uma requisição Flask; os handlers crescem a cada nova regra de negócio.
Recommendation: Aplicar RP-06 — extrair para `controllers/task_controller.py`/`controllers/user_controller.py`, mantendo a rota apenas como tradução HTTP.

### [HIGH] Lógica de Validação Duplicada (Implementada Duas Vezes, uma Delas Morta) (AP-13)
File: utils/helpers.py:57-108 (process_task_data); routes/task_routes.py:96-114, 166-184
Description: `utils/helpers.py` já define `process_task_data()` com toda a validação de task (título, status, prioridade, data, tags) — mas essa função nunca é chamada; `task_routes.py` reimplementa a mesma validação inline, com pequenas divergências (ex.: `process_task_data` normaliza `title.strip()`, a validação inline em `create_task`/`update_task` não).
Impact: Uma correção de regra aplicada em um dos dois lugares não se propaga automaticamente para o outro — já há divergência de comportamento (strip vs. não-strip) entre os dois caminhos.
Recommendation: Aplicar RP-13 — eliminar a duplicação usando `process_task_data` (ou seu equivalente já reescrito no controller) como única fonte de validação, e apagar a versão morta caso o controller a substitua.

### [HIGH] N+1 Queries no Relatório de Produtividade (AP-11)
File: routes/report_routes.py:53-68 (summary_report → user_stats), 30-43 (overdue_list)
Description: Para cada usuário, `summary_report()` dispara uma nova query (`Task.query.filter_by(user_id=u.id).all()`) dentro de um loop Python para calcular total/concluídas; separadamente, a contagem de atrasadas também carrega `Task.query.all()` inteiro na memória e filtra em Python em vez de usar `WHERE`/agregação no banco.
Impact: O relatório mais usado do sistema tem custo O(usuários) em queries adicionais e escaneia todas as tasks em memória a cada chamada — degrada rapidamente com o crescimento da base.
Recommendation: Aplicar RP-11 — substituir por `GROUP BY user_id` com `func.count`/`func.sum` (ou uma única query com `case`/agregação condicional) para produtividade por usuário, e filtrar `due_date`/status diretamente na query para atrasadas.

### [MEDIUM] Ausência de Paginação nos Endpoints de Listagem (AP-14)
File: routes/task_routes.py:11-63 (get_tasks), 240-271 (search_tasks); routes/user_routes.py:10-25 (get_users)
Description: `GET /tasks`, `GET /tasks/search` e `GET /users` executam `Query.all()`/`.all()` sem `limit`/`offset` e devolvem todos os registros de uma vez.
Impact: Tamanho de resposta e custo de query crescem sem limite conforme o volume de tasks/usuários aumenta.
Recommendation: Aplicar RP-14 — adicionar parâmetros `page`/`per_page` (`Query.paginate`) nos três endpoints.

### [MEDIUM] Tratamento de Exceção Genérico Demais (AP-18)
File: routes/task_routes.py:62, 137, 204, 236; routes/user_routes.py:130, 149; routes/report_routes.py:186, 207, 221
Description: Múltiplos blocos usam `except:` puro (sem capturar a exceção nem logar a causa real), devolvendo sempre a mesma mensagem genérica de erro.
Impact: Um bug de programação (ex.: erro de tipo, constraint do banco) é silenciosamente convertido em "Erro ao atualizar"/"Erro ao deletar", sem rastro para debug em produção.
Recommendation: Aplicar RP-18 — capturar exceções específicas, logar `str(e)` com o módulo `logging`, e centralizar esse padrão num error handler.

### [MEDIUM] Modo Debug Fixo no Entry Point (Deprecated/Unsafe Practice)
File: app.py:34
Description: `app.run(debug=True, host='0.0.0.0', port=5000)` está fixo no código, sem depender de variável de ambiente.
Impact: Em qualquer execução (inclusive acidental em produção), erros expõem stack traces completos e o debugger interativo do Werkzeug fica acessível publicamente (`host='0.0.0.0'` combinado com `debug=True` é especialmente perigoso).
Recommendation: Ler `DEBUG` de variável de ambiente com default `False`, conforme a tabela de APIs depreciadas/práticas obsoletas do catálogo.

### [LOW] Constantes Já Definidas, mas Nunca Usadas (AP-15)
File: utils/helpers.py:110-116; routes/task_routes.py:110, 177 (e outros); routes/user_routes.py:71, 120
Description: `utils/helpers.py` já define `VALID_STATUSES`, `VALID_ROLES`, `MAX_TITLE_LENGTH`, `MIN_TITLE_LENGTH`, `MIN_PASSWORD_LENGTH` — mas as rotas ignoram essas constantes e repetem as mesmas listas/números como literais inline em pelo menos 6 lugares diferentes.
Impact: Se uma regra mudar (ex.: novo status válido), é preciso lembrar de atualizar cada ocorrência hardcoded, já que a constante "oficial" não é a fonte real usada pelo código.
Recommendation: Aplicar RP-15 — importar e usar as constantes já existentes em `utils/helpers.py` em vez de repetir os literais.

### [LOW] Logging via print() (AP-17)
File: routes/task_routes.py:149, 153, 219, 234; routes/user_routes.py:83, 89, 147
Description: A aplicação usa `print(...)` para registrar criação/atualização/exclusão e erros, sem níveis, timestamps ou estrutura.
Impact: Impossível filtrar por severidade ou integrar com agregação de logs em produção.
Recommendation: Aplicar RP-17 — substituir por um logger estruturado (`logging`).

================================
Total: 12 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
