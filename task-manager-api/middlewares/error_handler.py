from flask import jsonify
from werkzeug.exceptions import HTTPException

from utils.logger import logger


def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        return jsonify({'error': err.description}), err.code

    @app.errorhandler(Exception)
    def handle_exception(err):
        logger.error(f"Erro não tratado: {err}")
        return jsonify({'error': 'Erro interno'}), 500
