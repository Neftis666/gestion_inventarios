from app import db
from datetime import datetime


class Proveedor(db.Model):
    __tablename__ = 'proveedores'

    id = db.Column(db.Integer, primary_key=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    # Información básica
    nombre = db.Column(db.String(200), nullable=False)
    nit = db.Column(db.String(50), nullable=True, unique=True)
    tipo = db.Column(db.String(20), default='Nacional')  # Nacional / Internacional

    # Contacto
    direccion = db.Column(db.String(200), nullable=True)
    telefono = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    contacto_nombre = db.Column(db.String(100), nullable=True)

    # Estado
    estado = db.Column(db.String(20), default='activo')  # activo / inactivo

    # Información adicional
    observaciones = db.Column(db.Text, nullable=True)
    registrado_por = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f'<Proveedor {self.nombre}>'
