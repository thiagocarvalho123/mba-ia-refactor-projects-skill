from werkzeug.security import check_password_hash, generate_password_hash

from src.config.database import get_db


def _row_to_public_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def get_all(page=1, per_page=20):
    db = get_db()
    offset = (page - 1) * per_page
    cursor = db.execute("SELECT * FROM usuarios LIMIT ? OFFSET ?", (per_page, offset))
    return [_row_to_public_dict(row) for row in cursor.fetchall()]


def get_by_id(id):
    db = get_db()
    row = db.execute("SELECT * FROM usuarios WHERE id = ?", (id,)).fetchone()
    return _row_to_public_dict(row) if row else None


def create(nome, email, senha, tipo="cliente"):
    db = get_db()
    senha_hash = generate_password_hash(senha)
    cursor = db.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo),
    )
    db.commit()
    return cursor.lastrowid


def verify_credentials(email, senha):
    db = get_db()
    row = db.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
    if row and check_password_hash(row["senha"], senha):
        return _row_to_public_dict(row)
    return None
