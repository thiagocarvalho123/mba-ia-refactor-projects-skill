from datetime import datetime

from sqlalchemy.orm import joinedload

from database import db
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import process_task_data
from utils.logger import logger

PER_PAGE_DEFAULT = 20


def _paginated(pagination, items):
    return {
        'items': items,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'total': pagination.total,
        'pages': pagination.pages,
    }


def list_tasks(page=1, per_page=PER_PAGE_DEFAULT):
    pagination = Task.query.options(
        joinedload(Task.user), joinedload(Task.category)
    ).paginate(page=page, per_page=per_page, error_out=False)

    items = []
    for t in pagination.items:
        data = t.to_dict()
        data['user_name'] = t.user.name if t.user else None
        data['category_name'] = t.category.name if t.category else None
        items.append(data)

    return _paginated(pagination, items), 200


def get_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return {'error': 'Task não encontrada'}, 404
    return task.to_dict(), 200


def create_task(data):
    if not data:
        return {'error': 'Dados inválidos'}, 400

    if not data.get('title'):
        return {'error': 'Título é obrigatório'}, 400

    payload = {
        'title': data.get('title'),
        'description': data.get('description', ''),
        'status': data.get('status', 'pending'),
        'priority': data.get('priority', 3),
    }
    if 'due_date' in data:
        payload['due_date'] = data.get('due_date')
    if 'tags' in data:
        payload['tags'] = data.get('tags')

    parsed, error = process_task_data(payload)
    if error:
        return {'error': error}, 400

    user_id = data.get('user_id')
    category_id = data.get('category_id')

    if user_id and not User.query.get(user_id):
        return {'error': 'Usuário não encontrado'}, 404
    if category_id and not Category.query.get(category_id):
        return {'error': 'Categoria não encontrada'}, 404

    task = Task()
    task.title = parsed['title']
    task.description = parsed.get('description', '')
    task.status = parsed.get('status', 'pending')
    task.priority = parsed.get('priority', 3)
    task.user_id = user_id
    task.category_id = category_id
    if 'due_date' in parsed:
        task.due_date = parsed['due_date']
    if 'tags' in parsed:
        task.tags = parsed['tags']

    try:
        db.session.add(task)
        db.session.commit()
        logger.info(f"Task criada: {task.id} - {task.title}")
        return task.to_dict(), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar task: {e}")
        return {'error': 'Erro ao criar task'}, 500


def update_task(task_id, data):
    task = Task.query.get(task_id)
    if not task:
        return {'error': 'Task não encontrada'}, 404
    if not data:
        return {'error': 'Dados inválidos'}, 400

    parsed, error = process_task_data(data, existing_task=task)
    if error:
        return {'error': error}, 400

    if 'user_id' in data:
        if data['user_id'] and not User.query.get(data['user_id']):
            return {'error': 'Usuário não encontrado'}, 404
        task.user_id = data['user_id']

    if 'category_id' in data:
        if data['category_id'] and not Category.query.get(data['category_id']):
            return {'error': 'Categoria não encontrada'}, 404
        task.category_id = data['category_id']

    for field in ('title', 'description', 'status', 'priority', 'due_date', 'tags'):
        if field in parsed:
            setattr(task, field, parsed[field])

    task.updated_at = datetime.utcnow()

    try:
        db.session.commit()
        logger.info(f"Task atualizada: {task.id}")
        return task.to_dict(), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar task {task_id}: {e}")
        return {'error': 'Erro ao atualizar'}, 500


def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return {'error': 'Task não encontrada'}, 404

    try:
        db.session.delete(task)
        db.session.commit()
        logger.info(f"Task deletada: {task_id}")
        return {'message': 'Task deletada com sucesso'}, 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao deletar task {task_id}: {e}")
        return {'error': 'Erro ao deletar'}, 500


def search_tasks(args):
    query = args.get('q', '')
    status = args.get('status', '')
    priority = args.get('priority', '')
    user_id = args.get('user_id', '')
    page = args.get('page', 1, type=int)
    per_page = args.get('per_page', PER_PAGE_DEFAULT, type=int)

    tasks_query = Task.query

    if query:
        tasks_query = tasks_query.filter(
            db.or_(
                Task.title.like(f'%{query}%'),
                Task.description.like(f'%{query}%')
            )
        )
    if status:
        tasks_query = tasks_query.filter(Task.status == status)
    if priority:
        tasks_query = tasks_query.filter(Task.priority == int(priority))
    if user_id:
        tasks_query = tasks_query.filter(Task.user_id == int(user_id))

    pagination = tasks_query.paginate(page=page, per_page=per_page, error_out=False)
    items = [t.to_dict() for t in pagination.items]
    return _paginated(pagination, items), 200


def task_stats():
    total = Task.query.count()
    pending = Task.query.filter_by(status='pending').count()
    in_progress = Task.query.filter_by(status='in_progress').count()
    done = Task.query.filter_by(status='done').count()
    cancelled = Task.query.filter_by(status='cancelled').count()

    overdue_count = Task.query.filter(
        Task.due_date.isnot(None),
        Task.due_date < datetime.utcnow(),
        Task.status.notin_(['done', 'cancelled'])
    ).count()

    stats = {
        'total': total,
        'pending': pending,
        'in_progress': in_progress,
        'done': done,
        'cancelled': cancelled,
        'overdue': overdue_count,
        'completion_rate': round((done / total) * 100, 2) if total > 0 else 0
    }
    return stats, 200
