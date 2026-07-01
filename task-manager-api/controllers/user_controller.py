from database import db
from middlewares.auth import generate_token
from models.task import Task
from models.user import User
from utils.helpers import validate_email
from utils.logger import logger

MIN_PASSWORD_LENGTH = 4
VALID_ROLES = ['user', 'admin', 'manager']


def list_users():
    users = User.query.all()
    result = []
    for u in users:
        data = u.to_dict()
        data['task_count'] = len(u.tasks)
        result.append(data)
    return result, 200


def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return {'error': 'Usuário não encontrado'}, 404

    data = user.to_dict()
    data['tasks'] = [t.to_dict() for t in Task.query.filter_by(user_id=user_id).all()]
    return data, 200


def create_user(data):
    if not data:
        return {'error': 'Dados inválidos'}, 400

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')

    if not name:
        return {'error': 'Nome é obrigatório'}, 400
    if not email:
        return {'error': 'Email é obrigatório'}, 400
    if not password:
        return {'error': 'Senha é obrigatória'}, 400
    if not validate_email(email):
        return {'error': 'Email inválido'}, 400
    if len(password) < MIN_PASSWORD_LENGTH:
        return {'error': f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres'}, 400

    if User.query.filter_by(email=email).first():
        return {'error': 'Email já cadastrado'}, 409
    if role not in VALID_ROLES:
        return {'error': 'Role inválido'}, 400

    user = User()
    user.name = name
    user.email = email
    user.set_password(password)
    user.role = role

    try:
        db.session.add(user)
        db.session.commit()
        logger.info(f"Usuário criado: {user.id} - {user.name}")
        return user.to_dict(), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar usuário: {e}")
        return {'error': 'Erro ao criar usuário'}, 500


def update_user(user_id, data, current_user):
    user = User.query.get(user_id)
    if not user:
        return {'error': 'Usuário não encontrado'}, 404
    if not data:
        return {'error': 'Dados inválidos'}, 400

    is_self = current_user.id == user.id
    is_admin = current_user.role == 'admin'
    if not is_self and not is_admin:
        return {'error': 'Você só pode editar seu próprio perfil'}, 403
    if ('role' in data or 'active' in data) and not is_admin:
        return {'error': 'Apenas administradores podem alterar role/active'}, 403

    if 'name' in data:
        user.name = data['name']

    if 'email' in data:
        if not validate_email(data['email']):
            return {'error': 'Email inválido'}, 400
        existing = User.query.filter_by(email=data['email']).first()
        if existing and existing.id != user_id:
            return {'error': 'Email já cadastrado'}, 409
        user.email = data['email']

    if 'password' in data:
        if len(data['password']) < MIN_PASSWORD_LENGTH:
            return {'error': 'Senha muito curta'}, 400
        user.set_password(data['password'])

    if 'role' in data:
        if data['role'] not in VALID_ROLES:
            return {'error': 'Role inválido'}, 400
        user.role = data['role']

    if 'active' in data:
        user.active = data['active']

    try:
        db.session.commit()
        return user.to_dict(), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar usuário {user_id}: {e}")
        return {'error': 'Erro ao atualizar'}, 500


def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return {'error': 'Usuário não encontrado'}, 404

    tasks = Task.query.filter_by(user_id=user_id).all()
    for t in tasks:
        db.session.delete(t)

    try:
        db.session.delete(user)
        db.session.commit()
        logger.info(f"Usuário deletado: {user_id}")
        return {'message': 'Usuário deletado com sucesso'}, 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao deletar usuário {user_id}: {e}")
        return {'error': 'Erro ao deletar'}, 500


def get_user_tasks(user_id):
    user = User.query.get(user_id)
    if not user:
        return {'error': 'Usuário não encontrado'}, 404

    tasks = Task.query.filter_by(user_id=user_id).all()
    return [t.to_dict() for t in tasks], 200


def login(data):
    if not data:
        return {'error': 'Dados inválidos'}, 400

    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return {'error': 'Email e senha são obrigatórios'}, 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return {'error': 'Credenciais inválidas'}, 401
    if not user.active:
        return {'error': 'Usuário inativo'}, 403

    return {
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': generate_token(user),
    }, 200
