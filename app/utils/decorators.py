from functools import wraps
from flask import session, redirect, url_for, flash, jsonify, request
from app.models.user_role_model import User

def login_required(f):
    """
    Decorador para requerir que el usuario esté autenticado
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión primero.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def permission_required(permission_name):
    """
    Decorador para requerir un permiso específico
    
    Uso:
        @permission_required('can_create')
        def create_product():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Debes iniciar sesión primero.', 'warning')
                return redirect(url_for('auth.login'))
            
            user = User.query.get(session['user_id'])
            if not user or not user.is_active:
                flash('Usuario no encontrado o inactivo.', 'danger')
                return redirect(url_for('auth.login'))
            
            if not user.has_permission(permission_name):
                flash('No tienes permisos para realizar esta acción.', 'danger')
                return redirect(url_for('dashboard.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def role_required(*role_names):
    """
    Decorador para requerir uno o más roles específicos
    
    Uso:
        @role_required('ADMINISTRADOR', 'ASTRID')
        def manage_users():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Debes iniciar sesión primero.', 'warning')
                return redirect(url_for('auth.login'))
            
            user = User.query.get(session['user_id'])
            if not user or not user.is_active:
                flash('Usuario no encontrado o inactivo.', 'danger')
                return redirect(url_for('auth.login'))
            
            if user.role.name not in role_names:
                flash(f'Esta acción requiere el rol: {", ".join(role_names)}', 'danger')
                return redirect(url_for('dashboard.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def api_permission_required(permission_name):
    """
    Decorador para APIs que requieren un permiso específico
    Retorna JSON en lugar de redirigir
    
    Uso:
        @api_permission_required('can_create')
        def api_create_product():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({
                    'success': False,
                    'message': 'Autenticación requerida'
                }), 401
            
            user = User.query.get(session['user_id'])
            if not user or not user.is_active:
                return jsonify({
                    'success': False,
                    'message': 'Usuario no válido'
                }), 401
            
            if not user.has_permission(permission_name):
                return jsonify({
                    'success': False,
                    'message': f'No tienes permiso: {permission_name}'
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def api_role_required(*role_names):
    """
    Decorador para APIs que requieren roles específicos
    Retorna JSON en lugar de redirigir
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({
                    'success': False,
                    'message': 'Autenticación requerida'
                }), 401
            
            user = User.query.get(session['user_id'])
            if not user or not user.is_active:
                return jsonify({
                    'success': False,
                    'message': 'Usuario no válido'
                }), 401
            
            if user.role.name not in role_names:
                return jsonify({
                    'success': False,
                    'message': f'Rol requerido: {", ".join(role_names)}'
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_current_user():
    """
    Obtiene el usuario actual de la sesión
    Retorna None si no hay sesión activa
    """
    if 'user_id' not in session:
        return None
    return User.query.get(session['user_id'])


def check_module_access(module_name):
    """
    Verifica si el usuario actual puede acceder a un módulo
    
    Uso en templates:
        {% if check_module_access('inventario') %}
            <a href="/inventario">Inventario</a>
        {% endif %}
    """
    user = get_current_user()
    if not user:
        return False
    return user.can_access_module(module_name)


# Contexto global para templates
def inject_permissions():
    """
    Inyecta funciones de permisos en todos los templates
    Agregar en __init__.py:
        @app.context_processor
        def utility_processor():
            return inject_permissions()
    """
    return {
        'get_current_user': get_current_user,
        'check_module_access': check_module_access,
        'has_permission': lambda perm: get_current_user().has_permission(perm) if get_current_user() else False
    }
