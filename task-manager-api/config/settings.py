import os

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-secret-change-me')
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')
DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', '5000'))
