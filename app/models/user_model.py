from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class Role(db.Model):
    """Modelo de Roles del sistema"""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Permisos generales
    can_create = db.Column(db.Boolean, default=False)
    can_edit = db.Column(db.Boolean, default=False)
    can_delete = db.Column(db.Boolean, default=False)
    can_view = db.Column(db.Boolean, default=True)
    
    # Permisos específicos
    can_manage_users = db.Column(db.Boolean, default=False)
    can_assign_roles = db.Column(db.Boolean, default=False)
    can_approve_orders = db.Column(db.Boolean, default=False)
    can_create_tasks = db.Column(db.Boolean, default=False)
    can_complete_tasks = db.Column(db.Boolean, default=False)
    can_access_reports = db.Column(db.Boolean, default=False)
    can_access_full_reports = db.Column(db.Boolean, default=False)
    
    # Permisos por módulo
    can_create_orders = db.Column(db.Boolean, default=False)
    can_edit_orders = db.Column(db.Boolean, default=False)
    can_create_inventory = db.Column(db.Boolean, default=False)
    can_edit_inventory = db.Column(db.Boolean, default=False)
    can_create_barcode = db.Column(db.Boolean, default=False)
    can_edit_barcode = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con usuarios
    users = db.relationship('User', backref='role', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'permissions': {
                'can_create': self.can_create,
                'can_edit': self.can_edit,
                'can_delete': self.can_delete,
                'can_view': self.can_view,
                'can_manage_users': self.can_manage_users,
                'can_assign_roles': self.can_assign_roles,
                'can_approve_orders': self.can_approve_orders,
                'can_create_tasks': self.can_create_tasks,
                'can_complete_tasks': self.can_complete_tasks,
                'can_access_reports': self.can_access_reports,
                'can_access_full_reports': self.can_access_full_reports,
                'can_create_orders': self.can_create_orders,
                'can_edit_orders': self.can_edit_orders,
                'can_create_inventory': self.can_create_inventory,
                'can_edit_inventory': self.can_edit_inventory,
                'can_create_barcode': self.can_create_barcode,
                'can_edit_barcode': self.can_edit_barcode,
            }
        }
    
    def __repr__(self):
        return f'<Role {self.display_name}>'


class User(db.Model):
    """Modelo de Usuario del sistema"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Información personal
    full_name = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    
    # Estado y rol
    is_active = db.Column(db.Boolean, default=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    
    # Auditoría
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relaciones
    tasks_assigned = db.relationship('Task', foreign_keys='Task.assigned_to_id', 
                                    backref='assigned_to', lazy=True)
    tasks_created = db.relationship('Task', foreign_keys='Task.created_by_id', 
                                   backref='created_by_user', lazy=True)
    
    def set_password(self, password):
        """Encripta y guarda la contraseña"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica si la contraseña es correcta"""
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, permission_name):
        """Verifica si el usuario tiene un permiso específico"""
        if not self.role:
            return False
        return getattr(self.role, permission_name, False)
    
    def can_access_module(self, module_name):
        """Verifica si puede acceder a un módulo específico"""
        module_permissions = {
            'ordenes': self.role.can_create_orders or self.role.can_edit_orders,
            'inventario': self.role.can_create_inventory or self.role.can_edit_inventory,
            'barcode': self.role.can_create_barcode or self.role.can_edit_barcode,
            'reportes': self.role.can_access_reports,
            'usuarios': self.role.can_manage_users,
        }
        return module_permissions.get(module_name, self.role.can_view)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'phone': self.phone,
            'is_active': self.is_active,
            'role': self.role.to_dict() if self.role else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'


class Task(db.Model):
    """Modelo de Tareas/Asignaciones"""
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Tipo de tarea
    task_type = db.Column(db.String(50), nullable=False)  # 'entrega', 'revision_inventario', 'informe'
    
    # Asignación
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Tiempos
    due_date = db.Column(db.DateTime, nullable=False)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Estado
    status = db.Column(db.String(20), default='pendiente')  # 'pendiente', 'en_progreso', 'completada', 'cancelada'
    priority = db.Column(db.String(20), default='media')  # 'baja', 'media', 'alta', 'urgente'
    
    # Resultados
    completion_notes = db.Column(db.Text)
    photo_path = db.Column(db.String(500))  # Para fotos de entregas
    
    # Relación con órdenes (opcional)
    order_id = db.Column(db.Integer, nullable=True)
    
    def is_overdue(self):
        """Verifica si la tarea está vencida"""
        if self.status in ['completada', 'cancelada']:
            return False
        return datetime.utcnow() > self.due_date
    
    def days_remaining(self):
        """Calcula días restantes"""
        if self.status in ['completada', 'cancelada']:
            return 0
        delta = self.due_date - datetime.utcnow()
        return max(0, delta.days)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'task_type': self.task_type,
            'assigned_to': self.assigned_to.username if self.assigned_to else None,
            'assigned_to_name': self.assigned_to.full_name if self.assigned_to else None,
            'created_by': self.created_by_user.username if self.created_by_user else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'status': self.status,
            'priority': self.priority,
            'completion_notes': self.completion_notes,
            'photo_path': self.photo_path,
            'order_id': self.order_id,
            'is_overdue': self.is_overdue(),
            'days_remaining': self.days_remaining()
        }
    
    def __repr__(self):
        return f'<Task {self.title} - {self.status}>'


class OrderApproval(db.Model):
    """Modelo para aprobaciones de órdenes de compra"""
    __tablename__ = 'order_approvals'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, nullable=False)  # ID de la orden en tu sistema
    order_number = db.Column(db.String(50), nullable=False)
    
    # Estado de aprobación
    status = db.Column(db.String(20), default='pendiente')  # 'pendiente', 'aprobada', 'rechazada', 'info_solicitada'
    
    # Comercial que creó la orden
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Astrid que aprueba/rechaza
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Comentarios
    comments = db.Column(db.Text)
    requested_info = db.Column(db.Text)  # Información adicional solicitada
    
    # Fechas
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    
    # Relaciones
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='orders_created')
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_id], backref='orders_reviewed')
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'order_number': self.order_number,
            'status': self.status,
            'created_by': self.created_by.username if self.created_by else None,
            'reviewed_by': self.reviewed_by.username if self.reviewed_by else None,
            'comments': self.comments,
            'requested_info': self.requested_info,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None
        }
    
    def __repr__(self):
        return f'<OrderApproval {self.order_number} - {self.status}>'
