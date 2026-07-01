# Playbook de Refatoração

Knowledge base for **Phase 3**. One concrete transformation per anti-pattern in the catalog (`RP-xx` ids match `AP-xx`). Examples are shown in Python and/or JavaScript — translate the *shape* of the transformation to whatever language Phase 1 detected; the point is the structural move, not the specific syntax.

---

### RP-01 · Extract Config to Environment Variables (fixes AP-01)

```python
# Before — app.py
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"

# After — src/config/settings.py
import os
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-insecure-default-change-me")
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

# src/app.py
from config.settings import SECRET_KEY, DEBUG
app.config["SECRET_KEY"] = SECRET_KEY
```
```javascript
// Before — utils.js
const config = { dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_..." };

// After — src/config/index.js
module.exports = {
  dbPass: process.env.DB_PASS || "dev-local-password",
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || "pk_test_dev_default",
};
```

### RP-02 · Parameterized Queries / ORM (fixes AP-02)

```python
# Before — models.py
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))

# After — models/produto_model.py
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
```

### RP-03 · Split God Module by Domain (fixes AP-03)

```
# Before
models.py            # produtos + usuarios + pedidos + itens_pedido, 315 lines

# After
src/models/produto_model.py
src/models/usuario_model.py
src/models/pedido_model.py
```
Each new module owns only its entity's queries and shape; shared helpers (e.g. a `get_connection()`) move to `src/config/database.py` and are imported, not duplicated.

### RP-04 · Proper Password Hashing + Safe Serialization (fixes AP-04)

```python
# Before — models/user.py
def set_password(self, pwd):
    self.password = hashlib.md5(pwd.encode()).hexdigest()

def to_dict(self):
    return {..., "password": self.password}

# After
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, pwd):
    self.password_hash = generate_password_hash(pwd)

def check_password(self, pwd):
    return check_password_hash(self.password_hash, pwd)

def to_dict(self):
    return {"id": self.id, "name": self.name, "email": self.email, "role": self.role}
    # password_hash intentionally excluded from any API-facing serialization
```

### RP-05 · Auth-Gated Admin Routes (fixes AP-05)

```python
# Before — app.py
@app.route("/admin/query", methods=["POST"])
def executar_query():
    query = request.get_json().get("sql", "")
    cursor.execute(query)   # arbitrary client-supplied SQL

# After — remove the raw-query endpoint entirely (no legitimate client use case
# justifies executing arbitrary SQL from a request body); for endpoints that
# must remain admin-only, gate them behind middleware:

# src/middlewares/auth.py
def require_admin(handler):
    @wraps(handler)
    def wrapper(*args, **kwargs):
        user = get_authenticated_user(request)
        if not user or not user.is_admin():
            return jsonify({"erro": "Não autorizado"}), 403
        return handler(*args, **kwargs)
    return wrapper

# src/controllers/admin_controller.py
@require_admin
def reset_database(): ...
```

### RP-06 · Extract Business Logic to Controller (fixes AP-06)

```javascript
// Before — route handler computing everything inline
app.post('/api/checkout', (req, res) => {
  // 40 lines of course lookup, user creation, payment status, enrollment, audit log...
});

// After — src/routes/checkout.routes.js
router.post('/checkout', (req, res) => checkoutController.processCheckout(req, res));

// src/controllers/checkout.controller.js
async function processCheckout(req, res) {
  const result = await checkoutService.checkout(req.body);
  return res.status(result.status).json(result.body);
}
```

### RP-07 · Dependency Injection Instead of Global Singleton (fixes AP-07)

```python
# Before — database.py
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(db_path)
    return db_connection

# After — src/config/database.py exposes a factory; src/app.py (composition
# root) creates the connection/session once and passes it into the pieces
# that need it (Flask's `db.init_app(app)` app-context pattern, or an
# explicit constructor argument) instead of every module reaching into a
# bare global.
```

### RP-08 · Real Auth Token Issuance + Verification (fixes AP-08)

```python
# Before — routes/user_routes.py
return jsonify({"token": "fake-jwt-token-" + str(user.id)})
# ...and no route ever checks this token.

# After
import jwt
token = jwt.encode({"sub": user.id, "exp": ...}, SECRET_KEY, algorithm="HS256")

# src/middlewares/auth.py
def require_auth(handler):
    @wraps(handler)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization", "").removeprefix("Bearer ")
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except jwt.InvalidTokenError:
            return jsonify({"erro": "Token inválido"}), 401
        request.user_id = payload["sub"]
        return handler(*args, **kwargs)
    return wrapper
```

### RP-09 · Remove Global Mutable State (fixes AP-09)

```javascript
// Before — utils.js
let globalCache = {};
function logAndCache(key, data) { globalCache[key] = data; }

// After — encapsulate in a class/module with a controlled lifecycle,
// or use a real cache (per-request memoization, or an external store like
// Redis) instead of a bare module-level object mutated by every request.
class RequestCache {
  constructor() { this.store = new Map(); }
  set(key, data) { this.store.set(key, data); }
}
module.exports = { RequestCache };
```

### RP-10 · Stop Logging/Returning Sensitive Data (fixes AP-10)

```javascript
// Before
console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);

// After
console.log(`Processando pagamento para matrícula (cartão final ${cc.slice(-4)})`);
// secret keys are never interpolated into log lines at all.
```

### RP-11 · Fix N+1 with Join / Eager Load (fixes AP-11)

```python
# Before — per-order, per-item nested queries
for row in pedidos:
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    for item in itens:
        cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))

# After — one joined query
cursor.execute("""
    SELECT p.*, ip.produto_id, ip.quantidade, ip.preco_unitario, pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = ip.produto_id
""")
```

### RP-12 · Centralized Validation + Consistent Response Envelope (fixes AP-12)

```python
# Before — repeated ad hoc checks and inconsistent shapes per route

# After — src/middlewares/error_handler.py defines one envelope:
def success(data, status=200): return jsonify({"sucesso": True, "dados": data}), status
def error(message, status=400): return jsonify({"sucesso": False, "erro": message}), status
# every controller returns through these two helpers only.
```

### RP-13 · Extract Duplicated Logic to One Function (fixes AP-13)

```python
# Before — the same overdue check copy-pasted in 4 places
if t.due_date and t.due_date < datetime.utcnow() and t.status not in ("done", "cancelled"):
    ...

# After — models/task.py, single source of truth, called everywhere
def is_overdue(self):
    return bool(self.due_date and self.due_date < datetime.utcnow()
                and self.status not in ("done", "cancelled"))
```

### RP-14 · Add Pagination (fixes AP-14)

```python
# Before
tasks = Task.query.all()

# After
page = int(request.args.get("page", 1))
per_page = min(int(request.args.get("per_page", 20)), 100)
tasks = Task.query.paginate(page=page, per_page=per_page, error_out=False).items
```

### RP-15 · Named Constants for Magic Numbers (fixes AP-15)

```python
# Before
if len(nome) > 200: ...

# After — utils/constants.py
MAX_NAME_LENGTH = 200
if len(nome) > MAX_NAME_LENGTH: ...
```

### RP-16 · Descriptive Renames (fixes AP-16)

```javascript
// Before
let u = req.body.usr, e = req.body.eml, p = req.body.pwd, cid = req.body.c_id, cc = req.body.card;

// After
const { usr: userName, eml: email, pwd: password, c_id: courseId, card: cardNumber } = req.body;
```

### RP-17 · Structured Logging (fixes AP-17)

```python
# Before
print("ERRO ao criar produto: " + str(e))

# After
import logging
logger = logging.getLogger(__name__)
logger.error("Erro ao criar produto", exc_info=e)
```

### RP-18 · Narrow Exception Handling (fixes AP-18)

```python
# Before
try:
    ...
except:
    return jsonify({'error': 'Erro interno'}), 500

# After
try:
    ...
except (ValueError, KeyError) as e:
    return jsonify({'error': str(e)}), 400
except SQLAlchemyError as e:
    db.session.rollback()
    logger.error("DB error", exc_info=e)
    return jsonify({'error': 'Erro interno'}), 500
```
