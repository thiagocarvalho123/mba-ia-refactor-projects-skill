from datetime import datetime, timedelta

from sqlalchemy import case, func

from database import db
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import calculate_percentage


def summary_report():
    total_tasks = Task.query.count()
    total_users = User.query.count()
    total_categories = Category.query.count()

    pending = Task.query.filter_by(status='pending').count()
    in_progress = Task.query.filter_by(status='in_progress').count()
    done = Task.query.filter_by(status='done').count()
    cancelled = Task.query.filter_by(status='cancelled').count()

    p1 = Task.query.filter_by(priority=1).count()
    p2 = Task.query.filter_by(priority=2).count()
    p3 = Task.query.filter_by(priority=3).count()
    p4 = Task.query.filter_by(priority=4).count()
    p5 = Task.query.filter_by(priority=5).count()

    now = datetime.utcnow()
    overdue_tasks = Task.query.filter(
        Task.due_date.isnot(None),
        Task.due_date < now,
        Task.status.notin_(['done', 'cancelled'])
    ).all()
    overdue_list = [{
        'id': t.id,
        'title': t.title,
        'due_date': str(t.due_date),
        'days_overdue': (now - t.due_date).days
    } for t in overdue_tasks]

    seven_days_ago = now - timedelta(days=7)
    recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()
    recent_done = Task.query.filter(
        Task.status == 'done',
        Task.updated_at >= seven_days_ago
    ).count()

    productivity_rows = db.session.query(
        User.id,
        User.name,
        func.count(Task.id),
        func.sum(case((Task.status == 'done', 1), else_=0))
    ).outerjoin(Task, Task.user_id == User.id).group_by(User.id, User.name).all()

    user_stats = []
    for user_id, user_name, total, completed in productivity_rows:
        completed = completed or 0
        user_stats.append({
            'user_id': user_id,
            'user_name': user_name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': calculate_percentage(completed, total)
        })

    report = {
        'generated_at': str(now),
        'overview': {
            'total_tasks': total_tasks,
            'total_users': total_users,
            'total_categories': total_categories,
        },
        'tasks_by_status': {
            'pending': pending,
            'in_progress': in_progress,
            'done': done,
            'cancelled': cancelled,
        },
        'tasks_by_priority': {
            'critical': p1,
            'high': p2,
            'medium': p3,
            'low': p4,
            'minimal': p5,
        },
        'overdue': {
            'count': len(overdue_list),
            'tasks': overdue_list,
        },
        'recent_activity': {
            'tasks_created_last_7_days': recent_tasks,
            'tasks_completed_last_7_days': recent_done,
        },
        'user_productivity': user_stats,
    }

    return report, 200


def user_report(user_id):
    user = User.query.get(user_id)
    if not user:
        return {'error': 'Usuário não encontrado'}, 404

    tasks = Task.query.filter_by(user_id=user_id).all()
    total = len(tasks)
    done = sum(1 for t in tasks if t.status == 'done')
    pending = sum(1 for t in tasks if t.status == 'pending')
    in_progress = sum(1 for t in tasks if t.status == 'in_progress')
    cancelled = sum(1 for t in tasks if t.status == 'cancelled')
    high_priority = sum(1 for t in tasks if t.priority <= 2)
    overdue = sum(1 for t in tasks if t.is_overdue())

    report = {
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
        },
        'statistics': {
            'total_tasks': total,
            'done': done,
            'pending': pending,
            'in_progress': in_progress,
            'cancelled': cancelled,
            'overdue': overdue,
            'high_priority': high_priority,
            'completion_rate': calculate_percentage(done, total)
        }
    }

    return report, 200
