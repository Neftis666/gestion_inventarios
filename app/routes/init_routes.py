"""
Ruta temporal para inicializar la base de datos desde el navegador
⚠️ ELIMINAR DESPUÉS DE USAR
"""
from flask import Blueprint, jsonify
from app import db
from app.models.user_role_model import Role, User

init_bp = Blueprint('init', __name__, url_prefix='/init')

@init_bp.route('/create-tables')
def create_tables():
    """
    Crea todas las tablas
    Acceder a: /init/create-tables
    """
    try:
        db.create_all()
        return jsonify({
            'success': True,
            'message': 'Tablas creadas exitosamente'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@init_bp.route('/recreate-tables')
def recreate_tables():
    """
    Elimina y recrea todas las tablas
    ⚠️ CUIDADO: Esto borra todos los datos
    Acceder a: /init/recreate-tables
    """
    try:
        db.drop_all()
        db.create_all()
        return jsonify({
            'success': True,
            'message': 'Tablas recreadas exitosamente (todos los datos fueron eliminados)'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@init_bp.route('/init-roles')
def init_roles():
    """
    Inicializa los roles del sistema
    Acceder a: /init/init-roles
    """
    try:
        # Eliminar roles existentes
        Role.query.delete()
        
        # Crear roles
        admin_role = Role(
            name='ADMINISTRADOR',
            display_name='Administrador',
            description='Acceso total al sistema',
            can_create=True,
            can_edit=True,
            can_delete=True,
            can_view=True,
            can_manage_users=True,
            can_assign_roles=True,
            can_approve_orders=True,
            can_create_tasks=True,
            can_complete_tasks=True,
            can_access_reports=True,
            can_access_full_reports=True,
            can_create_orders=True,
            can_edit_orders=True,
            can_create_inventory=True,
            can_edit_inventory=True,
            can_create_barcode=True,
            can_edit_barcode=True
        )
        
        astrid_role = Role(
            name='ASTRID',
            display_name='Astrid',
            description='Permisos avanzados',
            can_create=True,
            can_edit=True,
            can_delete=False,
            can_view=True,
            can_manage_users=False,
            can_assign_roles=False,
            can_approve_orders=True,
            can_create_tasks=True,
            can_complete_tasks=False,
            can_access_reports=True,
            can_access_full_reports=True,
            can_create_orders=True,
            can_edit_orders=True,
            can_create_inventory=True,
            can_edit_inventory=True,
            can_create_barcode=True,
            can_edit_barcode=True
        )
        
        juan_role = Role(
            name='JUAN_ANDRES',
            display_name='Juan Andrés',
            description='Permisos intermedios',
            can_create=False,
            can_edit=True,
            can_delete=False,
            can_view=True,
            can_manage_users=False,
            can_assign_roles=False,
            can_approve_orders=False,
            can_create_tasks=False,
            can_complete_tasks=True,
            can_access_reports=True,
            can_access_full_reports=False,
            can_create_orders=False,
            can_edit_orders=False,
            can_create_inventory=True,
            can_edit_inventory=True,
            can_create_barcode=True,
            can_edit_barcode=True
        )
        
        comercial_role = Role(
            name='COMERCIAL',
            display_name='Comercial',
            description='Permisos limitados',
            can_create=False,
            can_edit=False,
            can_delete=False,
            can_view=True,
            can_manage_users=False,
            can_assign_roles=False,
            can_approve_orders=False,
            can_create_tasks=False,
            can_complete_tasks=False,
            can_access_reports=True,
            can_access_full_reports=False,
            can_create_orders=True,
            can_edit_orders=False,
            can_create_inventory=False,
            can_edit_inventory=False,
            can_create_barcode=False,
            can_edit_barcode=False
        )
        
        db.session.add_all([admin_role, astrid_role, juan_role, comercial_role])
        db.session.commit()
        
        # Crear usuario admin
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@butacors.com',
                full_name='Administrador del Sistema',
                role_id=admin_role.id,
                is_active=True
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Roles creados exitosamente',
            'roles': ['ADMINISTRADOR', 'ASTRID', 'JUAN_ANDRES', 'COMERCIAL'],
            'admin_user': {
                'username': 'admin',
                'password': 'admin123',
                'note': '⚠️ CAMBIAR CONTRASEÑA EN PRODUCCIÓN'
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
