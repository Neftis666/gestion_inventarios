from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models.user_role_model import User, Role
from app import db

users_bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')

# Decorador para verificar permisos de admin
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión.', 'warning')
            return redirect(url_for('auth.login'))
        
        permissions = session.get('permissions', {})
        if not permissions.get('can_manage_users', False):
            flash('No tienes permiso para acceder a esta sección.', 'danger')
            return redirect(url_for('dashboard.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function


# ==================== USUARIOS ====================

@users_bp.route('/')
@admin_required
def listar_usuarios():
    """Lista todos los usuarios"""
    usuarios = User.query.all()
    return render_template('usuarios/listar.html', usuarios=usuarios)


@users_bp.route('/crear', methods=['GET', 'POST'])
@admin_required
def crear_usuario():
    """Crear nuevo usuario"""
    roles = Role.query.all()
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        role_id = request.form.get('role_id')
        is_active = request.form.get('is_active') == 'on'
        
        # Validaciones
        if not username or not email or not password or not role_id:
            flash('Por favor llena todos los campos obligatorios.', 'danger')
            return render_template('usuarios/crear.html', roles=roles)
        
        # Verificar si ya existe
        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe.', 'warning')
            return render_template('usuarios/crear.html', roles=roles)
        
        if User.query.filter_by(email=email).first():
            flash('El email ya está registrado.', 'warning')
            return render_template('usuarios/crear.html', roles=roles)
        
        # Crear usuario
        nuevo_usuario = User(
            username=username,
            email=email,
            full_name=full_name,
            phone=phone,
            role_id=int(role_id),
            is_active=is_active
        )
        nuevo_usuario.set_password(password)
        
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        flash(f'Usuario "{username}" creado exitosamente.', 'success')
        return redirect(url_for('usuarios.listar_usuarios'))
    
    return render_template('usuarios/crear.html', roles=roles)


@users_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@admin_required
def editar_usuario(id):
    """Editar usuario existente"""
    usuario = User.query.get_or_404(id)
    roles = Role.query.all()
    
    if request.method == 'POST':
        usuario.username = request.form.get('username')
        usuario.email = request.form.get('email')
        usuario.full_name = request.form.get('full_name')
        usuario.phone = request.form.get('phone')
        usuario.role_id = int(request.form.get('role_id'))
        usuario.is_active = request.form.get('is_active') == 'on'
        
        # Cambiar contraseña solo si se proporciona una nueva
        new_password = request.form.get('password')
        if new_password:
            usuario.set_password(new_password)
        
        db.session.commit()
        
        flash(f'Usuario "{usuario.username}" actualizado exitosamente.', 'success')
        return redirect(url_for('usuarios.listar_usuarios'))
    
    return render_template('usuarios/editar.html', usuario=usuario, roles=roles)


@users_bp.route('/eliminar/<int:id>', methods=['POST'])
@admin_required
def eliminar_usuario(id):
    """Eliminar usuario"""
    usuario = User.query.get_or_404(id)
    
    # No permitir eliminar el propio usuario
    if usuario.id == session.get('user_id'):
        flash('No puedes eliminar tu propio usuario.', 'danger')
        return redirect(url_for('usuarios.listar_usuarios'))
    
    username = usuario.username
    db.session.delete(usuario)
    db.session.commit()
    
    flash(f'Usuario "{username}" eliminado exitosamente.', 'success')
    return redirect(url_for('usuarios.listar_usuarios'))


@users_bp.route('/toggle/<int:id>', methods=['POST'])
@admin_required
def toggle_usuario(id):
    """Activar/Desactivar usuario"""
    usuario = User.query.get_or_404(id)
    
    if usuario.id == session.get('user_id'):
        flash('No puedes desactivar tu propio usuario.', 'danger')
        return redirect(url_for('usuarios.listar_usuarios'))
    
    usuario.is_active = not usuario.is_active
    db.session.commit()
    
    estado = "activado" if usuario.is_active else "desactivado"
    flash(f'Usuario "{usuario.username}" {estado} exitosamente.', 'success')
    return redirect(url_for('usuarios.listar_usuarios'))


# ==================== ROLES ====================

@users_bp.route('/roles')
@admin_required
def listar_roles():
    """Lista todos los roles y sus permisos"""
    roles = Role.query.all()
    return render_template('usuarios/roles.html', roles=roles)


@users_bp.route('/roles/editar/<int:id>', methods=['GET', 'POST'])
@admin_required
def editar_rol(id):
    """Editar permisos de un rol"""
    rol = Role.query.get_or_404(id)
    
    if request.method == 'POST':
        # Actualizar permisos
        rol.display_name = request.form.get('display_name')
        rol.description = request.form.get('description')
        
        # Permisos generales
        rol.can_create = request.form.get('can_create') == 'on'
        rol.can_edit = request.form.get('can_edit') == 'on'
        rol.can_delete = request.form.get('can_delete') == 'on'
        rol.can_view = request.form.get('can_view') == 'on'
        
        # Permisos específicos
        rol.can_manage_users = request.form.get('can_manage_users') == 'on'
        rol.can_assign_roles = request.form.get('can_assign_roles') == 'on'
        rol.can_approve_orders = request.form.get('can_approve_orders') == 'on'
        rol.can_create_tasks = request.form.get('can_create_tasks') == 'on'
        rol.can_complete_tasks = request.form.get('can_complete_tasks') == 'on'
        rol.can_access_reports = request.form.get('can_access_reports') == 'on'
        rol.can_access_full_reports = request.form.get('can_access_full_reports') == 'on'
        
        # Permisos por módulo
        rol.can_create_orders = request.form.get('can_create_orders') == 'on'
        rol.can_edit_orders = request.form.get('can_edit_orders') == 'on'
        rol.can_create_inventory = request.form.get('can_create_inventory') == 'on'
        rol.can_edit_inventory = request.form.get('can_edit_inventory') == 'on'
        rol.can_create_barcode = request.form.get('can_create_barcode') == 'on'
        rol.can_edit_barcode = request.form.get('can_edit_barcode') == 'on'
        
        db.session.commit()
        
        flash(f'Rol "{rol.display_name}" actualizado exitosamente.', 'success')
        return redirect(url_for('usuarios.listar_roles'))
    
    return render_template('usuarios/editar_rol.html', rol=rol)
