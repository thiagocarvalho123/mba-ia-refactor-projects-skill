from functools import wraps

from flask import jsonify, request

from src.config.settings import ADMIN_TOKEN


def require_admin(handler):
    @wraps(handler)
    def wrapper(*args, **kwargs):
        token = request.headers.get("X-Admin-Token", "")
        if token != ADMIN_TOKEN:
            return jsonify({"sucesso": False, "erro": "Não autorizado"}), 403
        return handler(*args, **kwargs)

    return wrapper
