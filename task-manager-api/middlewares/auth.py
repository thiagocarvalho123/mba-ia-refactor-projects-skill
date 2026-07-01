from functools import wraps

from flask import current_app, g, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from models.user import User

TOKEN_MAX_AGE = 60 * 60 * 24  # 24h
TOKEN_SALT = 'auth-token'


def _serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt=TOKEN_SALT)


def generate_token(user):
    return _serializer().dumps({'user_id': user.id, 'role': user.role})


def _authenticate():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None, (jsonify({'error': 'Token de autenticação ausente'}), 401)

    token = auth_header[len('Bearer '):]
    try:
        payload = _serializer().loads(token, max_age=TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None, (jsonify({'error': 'Token inválido ou expirado'}), 401)

    user = User.query.get(payload.get('user_id'))
    if not user or not user.active:
        return None, (jsonify({'error': 'Usuário inválido ou inativo'}), 401)

    return user, None


def require_auth(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        user, error = _authenticate()
        if error:
            return error
        g.current_user = user
        return view_func(*args, **kwargs)
    return wrapper


def require_admin(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        user, error = _authenticate()
        if error:
            return error
        if user.role != 'admin':
            return jsonify({'error': 'Acesso restrito a administradores'}), 403
        g.current_user = user
        return view_func(*args, **kwargs)
    return wrapper
