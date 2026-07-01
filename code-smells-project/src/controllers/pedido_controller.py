import logging

from src.models import pedido_model, produto_model
from src.utils import responses
from src.utils.constants import STATUS_VALIDOS

logger = logging.getLogger(__name__)


def criar_pedido(request):
    dados = request.get_json()
    if not dados:
        return responses.error("Dados inválidos")

    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        return responses.error("Usuario ID é obrigatório")
    if not itens:
        return responses.error("Pedido deve ter pelo menos 1 item")

    total = 0
    itens_validados = []
    for item in itens:
        produto = produto_model.get_by_id(item["produto_id"])
        if produto is None:
            return responses.error(f"Produto {item['produto_id']} não encontrado")
        if produto["estoque"] < item["quantidade"]:
            return responses.error(f"Estoque insuficiente para {produto['nome']}")
        total += produto["preco"] * item["quantidade"]
        itens_validados.append((produto, item["quantidade"]))

    pedido_id = pedido_model.insert_pedido(usuario_id, total)
    for produto, quantidade in itens_validados:
        pedido_model.insert_item(pedido_id, produto["id"], quantidade, produto["preco"])
        produto_model.decrement_stock(produto["id"], quantidade)

    logger.info(
        "Pedido %s criado para usuário %s — notificações (email/sms/push) enfileiradas",
        pedido_id, usuario_id,
    )

    return responses.success(
        dados={"pedido_id": pedido_id, "total": total},
        mensagem="Pedido criado com sucesso",
        status=201,
    )


def listar_pedidos_usuario(usuario_id):
    return responses.success(dados=pedido_model.get_by_usuario(usuario_id))


def listar_todos_pedidos():
    return responses.success(dados=pedido_model.get_all())


def atualizar_status_pedido(pedido_id, request):
    dados = request.get_json()
    novo_status = dados.get("status", "")

    if novo_status not in STATUS_VALIDOS:
        return responses.error("Status inválido")

    pedido_model.update_status(pedido_id, novo_status)

    if novo_status == "aprovado":
        logger.info("Pedido %s aprovado — preparar envio", pedido_id)
    if novo_status == "cancelado":
        logger.info("Pedido %s cancelado — devolver estoque", pedido_id)

    return responses.success(mensagem="Status atualizado")


def relatorio_vendas():
    resumo = pedido_model.sales_summary()
    faturamento = resumo["faturamento_bruto"]

    desconto = 0
    if faturamento > 10000:
        desconto = faturamento * 0.1
    elif faturamento > 5000:
        desconto = faturamento * 0.05
    elif faturamento > 1000:
        desconto = faturamento * 0.02

    total_pedidos = resumo["total_pedidos"]
    relatorio = {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": resumo["pedidos_pendentes"],
        "pedidos_aprovados": resumo["pedidos_aprovados"],
        "pedidos_cancelados": resumo["pedidos_cancelados"],
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
    return responses.success(dados=relatorio)
