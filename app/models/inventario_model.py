from app import db
from datetime import datetime

class Producto(db.Model):
    __tablename__ = 'productos'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    serial = db.Column(db.String(100), nullable=True)
    costo_unitario = db.Column(db.Float, nullable=False)
    cantidad = db.Column(db.Integer, default=0)
    estado = db.Column(db.String(20), default='disponible')  # disponible, prestado, dañado
    categoria = db.Column(db.String(100), nullable=True)
    fecha_ingreso = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación con movimientos
    movimientos = db.relationship('MovimientoInventario', backref='producto', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Producto {self.codigo} - {self.nombre}>'

    @property
    def nivel_stock(self):
        """Retorna el nivel de stock: suficiente, bajo, critico"""
        if self.cantidad > 10:
            return 'suficiente'
        elif self.cantidad > 5:
            return 'bajo'
        else:
            return 'critico'


class MovimientoInventario(db.Model):
    __tablename__ = 'movimientos_inventario'

    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # entrada, salida, ajuste, prestamo
    cantidad = db.Column(db.Integer, nullable=False)
    cantidad_anterior = db.Column(db.Integer, nullable=False)
    cantidad_nueva = db.Column(db.Integer, nullable=False)
    motivo = db.Column(db.String(200), nullable=True)
    usuario = db.Column(db.String(100), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Movimiento {self.tipo} - Producto {self.producto_id}>'