from flask import Blueprint, request

from src.controllers import produto_controller as ctrl

produto_bp = Blueprint("produtos", __name__)


@produto_bp.route("/produtos", methods=["GET"])
def listar_produtos():
    return ctrl.listar_produtos(request)


@produto_bp.route("/produtos/busca", methods=["GET"])
def buscar_produtos():
    return ctrl.buscar_produtos(request)


@produto_bp.route("/produtos/<int:id>", methods=["GET"])
def buscar_produto(id):
    return ctrl.buscar_produto(id)


@produto_bp.route("/produtos", methods=["POST"])
def criar_produto():
    return ctrl.criar_produto(request)


@produto_bp.route("/produtos/<int:id>", methods=["PUT"])
def atualizar_produto(id):
    return ctrl.atualizar_produto(id, request)


@produto_bp.route("/produtos/<int:id>", methods=["DELETE"])
def deletar_produto(id):
    return ctrl.deletar_produto(id)
