from src.config.database import get_db


def _pedido_base(row):
    return {
        "id": row["id"],
        "usuario_id": row["usuario_id"],
        "status": row["status"],
        "total": row["total"],
        "criado_em": row["criado_em"],
        "itens": [],
    }


def _attach_itens(db, pedidos_by_id):
    if not pedidos_by_id:
        return
    ids = list(pedidos_by_id.keys())
    placeholders = ",".join("?" for _ in ids)
    cursor = db.execute(
        f"""
        SELECT ip.pedido_id, ip.produto_id, ip.quantidade, ip.preco_unitario, p.nome AS produto_nome
        FROM itens_pedido ip
        LEFT JOIN produtos p ON p.id = ip.produto_id
        WHERE ip.pedido_id IN ({placeholders})
        """,
        ids,
    )
    for row in cursor.fetchall():
        pedidos_by_id[row["pedido_id"]]["itens"].append({
            "produto_id": row["produto_id"],
            "produto_nome": row["produto_nome"] or "Desconhecido",
            "quantidade": row["quantidade"],
            "preco_unitario": row["preco_unitario"],
        })


def get_all():
    db = get_db()
    rows = db.execute("SELECT * FROM pedidos").fetchall()
    pedidos_by_id = {row["id"]: _pedido_base(row) for row in rows}
    _attach_itens(db, pedidos_by_id)
    return list(pedidos_by_id.values())


def get_by_usuario(usuario_id):
    db = get_db()
    rows = db.execute("SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,)).fetchall()
    pedidos_by_id = {row["id"]: _pedido_base(row) for row in rows}
    _attach_itens(db, pedidos_by_id)
    return list(pedidos_by_id.values())


def insert_pedido(usuario_id, total):
    db = get_db()
    cursor = db.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
        (usuario_id, total),
    )
    db.commit()
    return cursor.lastrowid


def insert_item(pedido_id, produto_id, quantidade, preco_unitario):
    db = get_db()
    db.execute(
        "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
        (pedido_id, produto_id, quantidade, preco_unitario),
    )
    db.commit()


def update_status(pedido_id, status):
    db = get_db()
    db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id))
    db.commit()


def sales_summary():
    db = get_db()
    total_pedidos = db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
    faturamento = db.execute("SELECT SUM(total) FROM pedidos").fetchone()[0] or 0
    pendentes = db.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'pendente'").fetchone()[0]
    aprovados = db.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'aprovado'").fetchone()[0]
    cancelados = db.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'cancelado'").fetchone()[0]
    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": faturamento,
        "pedidos_pendentes": pendentes,
        "pedidos_aprovados": aprovados,
        "pedidos_cancelados": cancelados,
    }
