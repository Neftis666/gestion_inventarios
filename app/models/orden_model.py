from app import db
from datetime import datetime

class OrdenCompra(db.Model):
    __tablename__ = 'ordenes_compra'

    id = db.Column(db.Integer, primary_key=True)
    numero_orden = db.Column(db.String(50), unique=True, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    proveedor = db.Column(db.String(200), nullable=False)
    direccion_proveedor = db.Column(db.String(200), nullable=True)
    telefono_proveedor = db.Column(db.String(20), nullable=True)
    subtotal = db.Column(db.Float, nullable=False)
    iva = db.Column(db.Float, nullable=False)
    descuento = db.Column(db.Float, default=0)
    total = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(20), default='pendiente')
    elaborado_por = db.Column(db.String(100), nullable=False)
    verificado_por = db.Column(db.String(100), nullable=True)
    observaciones = db.Column(db.Text, nullable=True)
    
    detalles = db.relationship('DetalleOrden', backref='orden', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<OrdenCompra {self.numero_orden}>'


class DetalleOrden(db.Model):
    __tablename__ = 'detalles_orden'

    id = db.Column(db.Integer, primary_key=True)
    orden_id = db.Column(db.Integer, db.ForeignKey('ordenes_compra.id'), nullable=False)
    producto_descripcion = db.Column(db.String(200), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    unidad_medida = db.Column(db.String(20), default='UND')
    precio_unitario = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<DetalleOrden {self.orden_id}>'

# ✅ Alias para compatibilidad con las rutas existentes
Orden = OrdenCompra
