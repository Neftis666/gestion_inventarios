"""
Script para inicializar los roles del sistema
Ejecutar: python scripts/init_roles.py
"""
from app import create_app, db
from app.models.user_role_model import Role, User

def init_roles():
    app = create_app()
    
    with app.app_context():
        print("🔧 Inicializando roles del sistema...")
        
        # Eliminar roles existentes si los hay
        Role.query.delete()
        
        # 1. ROL: ADMINISTRADOR
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
        
        # 2. ROL: ASTRID
        astrid_role = Role(
            name='ASTRID',
            display_name='Astrid',
            description='Permisos avanzados - Creación, edición, asignación de tareas y aprobación de órdenes',
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
        
        # 3. ROL: JUAN ANDRÉS
        juan_role = Role(
            name='JUAN_ANDRES',
            display_name='Juan Andrés',
            description='Permisos intermedios - Edición, completar tareas, crear/editar en inventario y códigos',
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
        
        # 4. ROL: COMERCIAL
        comercial_role = Role(
            name='COMERCIAL',
            display_name='Comercial',
            description='Permisos limitados - Solo visualización y creación de órdenes de compra',
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
        
        # Guardar roles
        db.session.add_all([admin_role, astrid_role, juan_role, comercial_role])
        db.session.commit()
        
        print("✅ Roles creados exitosamente:")
        print(f"   - {admin_role.display_name}")
        print(f"   - {astrid_role.display_name}")
        print(f"   - {juan_role.display_name}")
        print(f"   - {comercial_role.display_name}")
        
        # Crear usuario administrador inicial si no existe
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@butacors.com',
                full_name='Administrador del Sistema',
                role_id=admin_role.id,
                is_active=True
            )
            admin_user.set_password('admin123')  # Cambiar en producción
            db.session.add(admin_user)
            db.session.commit()
            print(f"\n✅ Usuario administrador creado:")
            print(f"   Username: admin")
            print(f"   Password: admin123")
            print(f"   ⚠️  IMPORTANTE: Cambiar la contraseña en producción")
        else:
            print(f"\n✅ Usuario administrador ya existe: {admin_user.username}")

if __name__ == '__main__':
    init_roles()
    print("\n🎉 ¡Inicialización completada!")
