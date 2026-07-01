import logging

from src.models import usuario_model
from src.utils import responses
from src.utils.pagination import parse_pagination

logger = logging.getLogger(__name__)


def listar_usuarios(request):
    page, per_page = parse_pagination(request)
    return responses.success(dados=usuario_model.get_all(page, per_page))


def buscar_usuario(id):
    usuario = usuario_model.get_by_id(id)
    if usuario:
        return responses.success(dados=usuario)
    return responses.error("Usuário não encontrado", 404)


def criar_usuario(request):
    dados = request.get_json()
    if not dados:
        return responses.error("Dados inválidos")

    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not nome or not email or not senha:
        return responses.error("Nome, email e senha são obrigatórios")

    id = usuario_model.create(nome, email, senha)
    logger.info("Usuário criado: %s", email)
    return responses.success(dados={"id": id}, status=201)


def login(request):
    dados = request.get_json()
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not email or not senha:
        return responses.error("Email e senha são obrigatórios")

    usuario = usuario_model.verify_credentials(email, senha)
    if usuario:
        logger.info("Login bem-sucedido: %s", email)
        return responses.success(dados=usuario, mensagem="Login OK")

    logger.info("Login falhou: %s", email)
    return responses.error("Email ou senha inválidos", 401)
