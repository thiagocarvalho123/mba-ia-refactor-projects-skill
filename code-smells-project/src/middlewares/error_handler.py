import logging

from flask import jsonify

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(_e):
        return jsonify({"sucesso": False, "erro": "Recurso não encontrado"}), 404

    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.error("Erro não tratado", exc_info=e)
        return jsonify({"sucesso": False, "erro": str(e)}), 500
