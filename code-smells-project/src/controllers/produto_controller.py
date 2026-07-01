import logging

from src.models import produto_model
from src.utils import responses
from src.utils.constants import CATEGORIAS_VALIDAS, MAX_NOME_LENGTH, MIN_NOME_LENGTH
from src.utils.pagination import parse_pagination

logger = logging.getLogger(__name__)


def _validar_produto(dados):
    if not dados:
        return "Dados inválidos"
    if "nome" not in dados:
        return "Nome é obrigatório"
    if "preco" not in dados:
        return "Preço é obrigatório"
    if "estoque" not in dados:
        return "Estoque é obrigatório"
    if dados["preco"] < 0:
        return "Preço não pode ser negativo"
    if dados["estoque"] < 0:
        return "Estoque não pode ser negativo"
    if len(dados["nome"]) < MIN_NOME_LENGTH:
        return "Nome muito curto"
    if len(dados["nome"]) > MAX_NOME_LENGTH:
        return "Nome muito longo"
    categoria = dados.get("categoria", "geral")
    if categoria not in CATEGORIAS_VALIDAS:
        return f"Categoria inválida. Válidas: {CATEGORIAS_VALIDAS}"
    return None


def listar_produtos(request):
    page, per_page = parse_pagination(request)
    return responses.success(dados=produto_model.get_all(page, per_page))


def buscar_produto(id):
    produto = produto_model.get_by_id(id)
    if produto:
        return responses.success(dados=produto)
    return responses.error("Produto não encontrado", 404)


def criar_produto(request):
    dados = request.get_json()
    erro = _validar_produto(dados)
    if erro:
        return responses.error(erro)

    id = produto_model.create(
        nome=dados["nome"],
        descricao=dados.get("descricao", ""),
        preco=dados["preco"],
        estoque=dados["estoque"],
        categoria=dados.get("categoria", "geral"),
    )
    logger.info("Produto criado com ID: %s", id)
    return responses.success(dados={"id": id}, mensagem="Produto criado", status=201)


def atualizar_produto(id, request):
    produto_existente = produto_model.get_by_id(id)
    if not produto_existente:
        return responses.error("Produto não encontrado", 404)

    dados = request.get_json()
    erro = _validar_produto(dados)
    if erro:
        return responses.error(erro)

    produto_model.update(
        id,
        nome=dados["nome"],
        descricao=dados.get("descricao", ""),
        preco=dados["preco"],
        estoque=dados["estoque"],
        categoria=dados.get("categoria", "geral"),
    )
    return responses.success(mensagem="Produto atualizado")


def deletar_produto(id):
    produto = produto_model.get_by_id(id)
    if not produto:
        return responses.error("Produto não encontrado", 404)

    produto_model.delete(id)
    logger.info("Produto %s deletado", id)
    return responses.success(mensagem="Produto deletado")


def buscar_produtos(request):
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria", None)
    preco_min = request.args.get("preco_min", None)
    preco_max = request.args.get("preco_max", None)

    if preco_min:
        preco_min = float(preco_min)
    if preco_max:
        preco_max = float(preco_max)

    resultados = produto_model.search(termo, categoria, preco_min, preco_max)
    return responses.success(dados=resultados, extra={"total": len(resultados)})
