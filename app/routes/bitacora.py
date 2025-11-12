from flask import Blueprint, jsonify # type: ignore
from flask_jwt_extended import jwt_required, get_jwt_identity # type: ignore
from app.models.models import Bitacora, User, db # type: ignore

bitacora_bp = Blueprint("bitacora", __name__, url_prefix="/bitacora")

@bitacora_bp.route("/", methods=["GET"])
@jwt_required()
def get_bitacora():
    user = get_jwt_identity()

    # Solo los administradores pueden ver toda la bitácora
    if user["role"] != "admin":
        return jsonify({"msg": "Acceso denegado"}), 403

    registros = Bitacora.query.order_by(Bitacora.timestamp.desc()).all()
    result = [
        {
            "usuario": User.query.get(r.user_id).username,
            "accion": r.action,
            "modulo": r.module,
            "fecha": r.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }
        for r in registros
    ]
    return jsonify(result), 200
