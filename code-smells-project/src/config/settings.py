import os

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-insecure-default-change-me")
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
DB_PATH = os.environ.get("DB_PATH", "loja.db")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "dev-only-admin-token-change-me")
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5000"))
