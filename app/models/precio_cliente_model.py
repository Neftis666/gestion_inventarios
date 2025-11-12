from app import db
from datetime import datetime

class PrecioCliente(db.Model):
    __tablename__ = 'precios_clientes'
    
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    precio_base = db.Column(db.Float, nullable=False)
    precio_con_iva = db.Column(db.Float, nullable=False)
    descuento_porcentaje = db.Column(db.Float, default=0)
    fecha_asignacion = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_por = db.Column(db.String(100))
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True)
    
    # Relaciones
    cliente = db.relationship('Cliente', backref='precios_asignados', lazy=True)
    producto = db.relationship('Producto', backref='precios_por_cliente', lazy=True)
    
    def __repr__(self):
        return f'<PrecioCliente Cliente:{self.cliente_id} Producto:{self.producto_id}>'

class HistorialPrecioCliente(db.Model):
    __tablename__ = 'historial_precios_clientes'
    
    id = db.Column(db.Integer, primary_key=True)
    precio_cliente_id = db.Column(db.Integer, db.ForeignKey('precios_clientes.id'), nullable=False)
    precio_anterior = db.Column(db.Float, nullable=False)
    precio_nuevo = db.Column(db.Float, nullable=False)
    modificado_por = db.Column(db.String(100), nullable=False)
    fecha_modificacion = db.Column(db.DateTime, default=datetime.utcnow)
    motivo = db.Column(db.String(200))
    
    def __repr__(self):
        return f'<HistorialPrecio {self.id}>'