from src.config.database import get_db


def _row_to_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "preco": row["preco"],
        "estoque": row["estoque"],
        "categoria": row["categoria"],
        "ativo": row["ativo"],
        "criado_em": row["criado_em"],
    }


def get_all(page=1, per_page=20):
    db = get_db()
    offset = (page - 1) * per_page
    cursor = db.execute("SELECT * FROM produtos LIMIT ? OFFSET ?", (per_page, offset))
    return [_row_to_dict(row) for row in cursor.fetchall()]


def get_by_id(id):
    db = get_db()
    row = db.execute("SELECT * FROM produtos WHERE id = ?", (id,)).fetchone()
    return _row_to_dict(row) if row else None


def create(nome, descricao, preco, estoque, categoria):
    db = get_db()
    cursor = db.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    db.commit()
    return cursor.lastrowid


def update(id, nome, descricao, preco, estoque, categoria):
    db = get_db()
    db.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, id),
    )
    db.commit()
    return True


def delete(id):
    db = get_db()
    db.execute("DELETE FROM produtos WHERE id = ?", (id,))
    db.commit()
    return True


def search(termo, categoria=None, preco_min=None, preco_max=None):
    db = get_db()
    query = "SELECT * FROM produtos WHERE 1=1"
    params = []
    if termo:
        query += " AND (nome LIKE ? OR descricao LIKE ?)"
        params.extend([f"%{termo}%", f"%{termo}%"])
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    if preco_min is not None:
        query += " AND preco >= ?"
        params.append(preco_min)
    if preco_max is not None:
        query += " AND preco <= ?"
        params.append(preco_max)

    cursor = db.execute(query, params)
    return [_row_to_dict(row) for row in cursor.fetchall()]


def decrement_stock(id, quantidade):
    db = get_db()
    db.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (quantidade, id))
    db.commit()
