from app import db
from datetime import datetime

class Compra(db.Model):
    __tablename__ = 'compras'

    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    proveedor = db.Column(db.String(100), nullable=False)
    numero_factura = db.Column(db.String(50), nullable=False, unique=True)
    tipo_compra = db.Column(db.String(20), nullable=False)  # Nacional o Internacional
    producto = db.Column(db.String(100), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)
    iva = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    documento = db.Column(db.String(255), nullable=True)
