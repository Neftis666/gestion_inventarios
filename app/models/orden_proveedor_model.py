from app import db
from datetime import datetime


class OrdenProveedor(db.Model):
    __tablename__ = 'ordenes_proveedor'

    id = db.Column(db.Integer, primary_key=True)
    numero_orden = db.Column(db.String(50), unique=True, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_emision = db.Column(db.Date, nullable=True)

    # Proveedor (puede ser de lista o manual)
    proveedor_id = db.Column(db.Integer, nullable=True)  # Si viene de la lista
    proveedor = db.Column(db.String(200), nullable=False)  # Nombre siempre guardado
    direccion_proveedor = db.Column(db.String(200), nullable=True)
    telefono_proveedor = db.Column(db.String(30), nullable=True)

    # Datos adicionales
    numero_orden_cliente = db.Column(db.String(100), nullable=True)
    sucursal_cliente = db.Column(db.String(200), nullable=True)

    # Totales
    subtotal = db.Column(db.Float, nullable=False, default=0)
    iva = db.Column(db.Float, nullable=False, default=0)
    descuento = db.Column(db.Float, default=0)
    total = db.Column(db.Float, nullable=False, default=0)

    # Control
    estado = db.Column(db.String(20), default='pendiente')  # pendiente/aprobada/completada/cancelada
    elaborado_por = db.Column(db.String(100), nullable=True)
    verificado_por = db.Column(db.String(100), nullable=True)
    observaciones = db.Column(db.Text, nullable=True)

    detalles = db.relationship('DetalleOrdenProveedor', backref='orden', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<OrdenProveedor {self.numero_orden}>'


class DetalleOrdenProveedor(db.Model):
    __tablename__ = 'detalles_orden_proveedor'

    id = db.Column(db.Integer, primary_key=True)
    orden_id = db.Column(db.Integer, db.ForeignKey('ordenes_proveedor.id'), nullable=False)
    producto_descripcion = db.Column(db.String(200), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    unidad_medida = db.Column(db.String(20), default='UND')
    precio_unitario = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<DetalleOrdenProveedor {self.orden_id}>'
