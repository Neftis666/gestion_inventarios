from app import db
from app.models.models import Bitacora

def registrar_accion(user_id, accion, modulo):
    bitacora = Bitacora(user_id=user_id, action=accion, module=modulo)
    db.session.add(bitacora)
    db.session.commit()
