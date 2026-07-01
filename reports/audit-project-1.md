================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:      Flask 3.1.1
Dependencies:  flask-cors 5.0.1
Domain:        E-commerce API (produtos, pedidos, usuários)
Architecture:  Monolítica — tudo em 4 arquivos, sem separação de camadas. app.py mistura roteamento com endpoints administrativos de SQL cru; controllers.py mistura validação HTTP com regra de negócio; models.py concentra acesso a dados de 4 domínios via SQL concatenado; database.py expõe uma conexão global.
Source files:  4 files analyzed (app.py, controllers.py, models.py, database.py — ~784 linhas)
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================

================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~784 lines of code

## Summary
CRITICAL: 5 | HIGH: 3 | MEDIUM: 3 | LOW: 2

## Findings

### [CRITICAL] SQL Injection (AP-02)
File: models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155-166, 174, 188, 192, 206, 220, 224, 279-281, 289-297
Description: Toda a camada de dados constrói SQL por concatenação de strings com valores vindos diretamente da request (ex.: `"SELECT * FROM produtos WHERE id = " + str(id)`, `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"`). Não há nenhum uso de parâmetros (`?`) em nenhuma das ~15 funções do arquivo.
Impact: Qualquer endpoint que repassa entrada do usuário para essas funções (login, busca de produtos, criação de produto/usuário/pedido) é explorável para ler, alterar ou apagar qualquer dado do banco, e o login pode ser contornado com uma injeção clássica (`' OR '1'='1`).
Recommendation: Aplicar RP-02 (parametrizar todas as queries) em cada função de models.py.

### [CRITICAL] Endpoints Administrativos Sem Autenticação Executando SQL Arbitrário (AP-05)
File: app.py:47-78
Description: `/admin/reset-db` apaga todas as tabelas e `/admin/query` executa qualquer string SQL enviada no corpo da requisição (`cursor.execute(query)`), ambos sem qualquer verificação de autenticação/autorização.
Impact: Qualquer pessoa com a URL pode apagar o banco inteiro ou executar comandos SQL arbitrários (leitura, alteração, exclusão de qualquer tabela) — comprometimento total dos dados.
Recommendation: Aplicar RP-05 — remover o endpoint de query arbitrária e proteger `/admin/*` com middleware de autenticação/autorização (`require_admin`).

### [CRITICAL] Chave Secreta Hardcoded (AP-01)
File: app.py:7
Description: `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` está fixo no código-fonte.
Impact: Qualquer pessoa com acesso ao repositório (inclusive histórico do git) tem a chave de sessão/assinatura da aplicação, permitindo forjar sessões/cookies assinados.
Recommendation: Aplicar RP-01 — mover para variável de ambiente com valor de desenvolvimento seguro como default.

### [CRITICAL] Senhas em Texto Plano Armazenadas e Expostas (AP-04)
File: models.py:72-131 (criar_usuario, get_todos_usuarios, get_usuario_por_id, login_usuario); controllers.py:128-144 (listar_usuarios, buscar_usuario)
Description: Senhas são gravadas e comparadas em texto plano (`INSERT INTO usuarios (..., senha) VALUES (..., '" + senha + "')`, `WHERE senha = '" + senha + "'`), e os endpoints de listagem/consulta de usuário devolvem o campo `senha` no JSON de resposta.
Impact: Um vazamento do banco expõe a senha real de todos os usuários (sem nenhuma barreira de hashing), e qualquer chamada a `/usuarios` já vaza as senhas em texto plano pela própria API.
Recommendation: Aplicar RP-04 — hashear com `werkzeug.security.generate_password_hash`/`check_password_hash` e excluir a senha/hash de qualquer serialização voltada à API.

### [CRITICAL] God Module — models.py concentra 4 domínios (AP-03)
File: models.py:1-315
Description: Um único arquivo contém toda a lógica de acesso a dados (SQL cru), sem qualquer separação, para produtos, usuários, pedidos e itens_pedido — 315 linhas, ~15 funções não relacionadas entre si exceto por estarem no mesmo arquivo.
Impact: Impossível testar ou alterar a lógica de um domínio isoladamente; qualquer mudança tem alto risco de efeito colateral em domínios não relacionados.
Recommendation: Aplicar RP-03 — dividir em `models/produto_model.py`, `models/usuario_model.py`, `models/pedido_model.py`.

### [HIGH] Chave Secreta e Flag de Debug Vazadas na Resposta de /health (AP-10)
File: controllers.py:264-292
Description: `health_check()` devolve no JSON de resposta `"debug": True` e `"secret_key": "minha-chave-super-secreta-123"` — dados internos sensíveis expostos em um endpoint público de status.
Impact: Qualquer chamada não autenticada a `/health` vaza a secret key da aplicação e confirma que debug está ativo (o que também vaza stack traces detalhados em erros 500).
Recommendation: Aplicar RP-10 — remover completamente dados sensíveis da resposta; `/health` deve responder apenas com status operacional.

### [HIGH] Fat Controllers — Regras de Negócio e Validação Dentro do Handler HTTP (AP-06)
File: controllers.py:24-62 (criar_produto), controllers.py:188-220 (criar_pedido)
Description: Validação de campos, regras de negócio (lista de categorias válidas embutida, cálculo/checagem via `models.criar_pedido`) e até disparo de notificações (`print("ENVIANDO EMAIL...")`, `print("ENVIANDO SMS...")`) estão todos dentro da função que também monta a resposta HTTP.
Impact: Regras de negócio não podem ser reaproveitadas nem testadas sem simular uma request Flask completa; o handler cresce sem limite a cada nova regra.
Recommendation: Aplicar RP-06 — extrair a orquestração para `controllers/pedido_controller.py`/`controllers/produto_controller.py`, mantendo a view apenas com tradução HTTP.

### [HIGH] Acoplamento Forte a Conexão Global (AP-07)
File: database.py:4, 7-11
Description: `db_connection` é uma variável global de módulo, populada de forma lazy e reutilizada por qualquer parte do código via `get_db()` — não há injeção de dependência nem controle de ciclo de vida.
Impact: Impossível substituir a conexão por um dublê de teste; estado compartilhado implicitamente por toda a aplicação.
Recommendation: Aplicar RP-07 — mover a criação da conexão para o composition root (`src/app.py`) e injetar onde necessário.

### [MEDIUM] N+1 Queries ao Listar Pedidos (AP-11)
File: models.py:171-233 (get_pedidos_usuario, get_todos_pedidos)
Description: Para cada pedido, o código abre um segundo cursor para buscar os itens, e para cada item abre um terceiro cursor para buscar o nome do produto — três níveis de queries aninhadas em loop, em vez de um `JOIN`.
Impact: O número de queries cresce linearmente com pedidos × itens; gargalo de performance real assim que o volume de dados crescer.
Recommendation: Aplicar RP-11 — substituir por uma única query com `LEFT JOIN` entre pedidos, itens_pedido e produtos.

### [MEDIUM] Debug Mode Habilitado no Entry Point (Deprecated/Unsafe Practice)
File: app.py:8, 88
Description: `app.config["DEBUG"] = True` e `app.run(..., debug=True)` fixos no código, sem depender de variável de ambiente.
Impact: Em qualquer execução (inclusive acidental em produção), erros expõem stack traces completos e o debugger interativo do Werkzeug fica acessível.
Recommendation: Ler `DEBUG` de variável de ambiente com default `False`, conforme a tabela de APIs depreciadas/práticas obsoletas do catálogo.

### [MEDIUM] Ausência de Paginação nos Endpoints de Listagem (AP-14)
File: controllers.py:5-13 (listar_produtos), controllers.py:128-134 (listar_usuarios); models.py:4-22, 72-87
Description: `get_todos_produtos`/`get_todos_usuarios` executam `SELECT *` sem `LIMIT`/`OFFSET` e retornam todas as linhas de uma vez.
Impact: Tamanho de resposta e custo da query crescem sem limite conforme a base cresce.
Recommendation: Aplicar RP-14 — adicionar parâmetros `page`/`per_page` nos endpoints de listagem.

### [LOW] Lista de Categorias e Limites Hardcoded Inline (AP-15)
File: controllers.py:47-50, 52-54
Description: `categorias_validas = ["informatica", "moveis", ...]` e limites de tamanho de nome (`200`, `2`) estão soltos inline dentro da função, duplicáveis a cada novo endpoint que precisar da mesma regra.
Impact: Se a lista de categorias válidas mudar, é preciso lembrar de atualizar em todos os pontos onde foi copiada.
Recommendation: Aplicar RP-15 — mover para constantes nomeadas em um módulo compartilhado.

### [LOW] Logging via print() (AP-17)
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250
Description: Toda a aplicação usa `print(...)` para logar sucesso e erro, sem níveis, timestamps ou estrutura.
Impact: Impossível filtrar por severidade ou integrar com agregação de logs em produção.
Recommendation: Aplicar RP-17 — substituir por um logger estruturado (`logging`).

================================
Total: 13 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
