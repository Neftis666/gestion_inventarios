from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from app.models.user_role_model import User
from app import db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Por favor llena todos los campos.', 'danger')
            return redirect(url_for('auth.register'))
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('El usuario ya existe.', 'warning')
            return redirect(url_for('auth.register'))
        
        new_user = User(username=username, email=f'{username}@temp.com', role_id=1)
        new_user.set_password(password)
           
        db.session.add(new_user)
        db.session.commit()
        
        flash('Usuario registrado exitosamente. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            flash('Usuario o contraseña incorrectos.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Guardar información del usuario en sesión
        session['user_id'] = user.id
        session['username'] = user.username
        session['full_name'] = user.full_name
        session['role_id'] = user.role_id
        session['role_name'] = user.role.name
        session['role_display'] = user.role.display_name
        
        # Guardar todos los permisos en sesión
        session['permissions'] = {
            'can_create': user.role.can_create,
            'can_edit': user.role.can_edit,
            'can_delete': user.role.can_delete,
            'can_view': user.role.can_view,
            'can_manage_users': user.role.can_manage_users,
            'can_assign_roles': user.role.can_assign_roles,
            'can_approve_orders': user.role.can_approve_orders,
            'can_create_tasks': user.role.can_create_tasks,
            'can_complete_tasks': user.role.can_complete_tasks,
            'can_access_reports': user.role.can_access_reports,
            'can_access_full_reports': user.role.can_access_full_reports,
            'can_create_orders': user.role.can_create_orders,
            'can_edit_orders': user.role.can_edit_orders,
            'can_create_inventory': user.role.can_create_inventory,
            'can_edit_inventory': user.role.can_edit_inventory,
            'can_create_barcode': user.role.can_create_barcode,
            'can_edit_barcode': user.role.can_edit_barcode,
        }
        
        session.permanent = True
        
        flash(f'¡Bienvenido {user.full_name or user.username}!', 'success')
        return redirect(url_for('dashboard.dashboard'))
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada exitosamente.', 'info')
    return redirect(url_for('auth.login'))
