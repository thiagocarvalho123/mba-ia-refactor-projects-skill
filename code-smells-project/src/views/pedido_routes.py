from flask import Blueprint, request

from src.controllers import pedido_controller as ctrl

pedido_bp = Blueprint("pedidos", __name__)


@pedido_bp.route("/pedidos", methods=["POST"])
def criar_pedido():
    return ctrl.criar_pedido(request)


@pedido_bp.route("/pedidos", methods=["GET"])
def listar_todos_pedidos():
    return ctrl.listar_todos_pedidos()


@pedido_bp.route("/pedidos/usuario/<int:usuario_id>", methods=["GET"])
def listar_pedidos_usuario(usuario_id):
    return ctrl.listar_pedidos_usuario(usuario_id)


@pedido_bp.route("/pedidos/<int:pedido_id>/status", methods=["PUT"])
def atualizar_status_pedido(pedido_id):
    return ctrl.atualizar_status_pedido(pedido_id, request)


@pedido_bp.route("/relatorios/vendas", methods=["GET"])
def relatorio_vendas():
    return ctrl.relatorio_vendas()
