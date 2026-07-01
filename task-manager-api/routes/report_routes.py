from flask import Blueprint, jsonify, request

from controllers import category_controller, report_controller
from middlewares.auth import require_admin, require_auth

report_bp = Blueprint('reports', __name__)


@report_bp.route('/reports/summary', methods=['GET'])
def summary_report():
    body, status = report_controller.summary_report()
    return jsonify(body), status


@report_bp.route('/reports/user/<int:user_id>', methods=['GET'])
def user_report(user_id):
    body, status = report_controller.user_report(user_id)
    return jsonify(body), status


@report_bp.route('/categories', methods=['GET'])
def get_categories():
    body, status = category_controller.list_categories()
    return jsonify(body), status


@report_bp.route('/categories', methods=['POST'])
@require_auth
def create_category():
    body, status = category_controller.create_category(request.get_json(silent=True))
    return jsonify(body), status


@report_bp.route('/categories/<int:cat_id>', methods=['PUT'])
@require_auth
def update_category(cat_id):
    body, status = category_controller.update_category(cat_id, request.get_json(silent=True))
    return jsonify(body), status


@report_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
@require_admin
def delete_category(cat_id):
    body, status = category_controller.delete_category(cat_id)
    return jsonify(body), status
