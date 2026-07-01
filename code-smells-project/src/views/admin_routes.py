from flask import Blueprint

from src.controllers import admin_controller as ctrl
from src.middlewares.auth import require_admin

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/health", methods=["GET"])
def health_check():
    return ctrl.health_check()


@admin_bp.route("/admin/reset-db", methods=["POST"])
@require_admin
def reset_database():
    return ctrl.reset_database()
