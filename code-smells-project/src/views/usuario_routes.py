from flask import Blueprint, request

from src.controllers import usuario_controller as ctrl

usuario_bp = Blueprint("usuarios", __name__)


@usuario_bp.route("/usuarios", methods=["GET"])
def listar_usuarios():
    return ctrl.listar_usuarios(request)


@usuario_bp.route("/usuarios/<int:id>", methods=["GET"])
def buscar_usuario(id):
    return ctrl.buscar_usuario(id)


@usuario_bp.route("/usuarios", methods=["POST"])
def criar_usuario():
    return ctrl.criar_usuario(request)


@usuario_bp.route("/login", methods=["POST"])
def login():
    return ctrl.login(request)
