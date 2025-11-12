from app import db
from datetime import datetime

class Bitacora(db.Model):
    __tablename__ = 'bitacora'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(100), nullable=False)
    accion = db.Column(db.String(50), nullable=False)  # login, logout, crear, editar, eliminar, exportar
    modulo = db.Column(db.String(50), nullable=False)  # dashboard, compras, ventas, inventario, ordenes, reportes
    descripcion = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    fecha = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<Bitacora {self.usuario} - {self.accion}>'
    
    @staticmethod
    def registrar(usuario, accion, modulo, descripcion='', ip=''):
        """Método estático para registrar eventos fácilmente"""
        try:
            evento = Bitacora(
                usuario=usuario,
                accion=accion,
                modulo=modulo,
                descripcion=descripcion,
                ip_address=ip
            )
            db.session.add(evento)
            db.session.commit()
        except Exception as e:
            print(f"Error al registrar en bitácora: {e}")
            db.session.rollback()