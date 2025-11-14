from flask import Blueprint, jsonify

# Blueprint principal para la ruta raíz
main_bp = Blueprint('home', __name__)

@main_bp.route('/')
def index():
    """Ruta principal - Health check de la API"""
    return jsonify({
        "message": "API de Gestión de Inventarios",
        "status": "running",
        "version": "1.0",
        "endpoints": {
            "auth": "/login, /logout, /register",
            "dashboard": "/dashboard",
            "inventario": "/inventario/*",
            "compras": "/compras/*",
            "ventas": "/ventas/*",
            "ordenes": "/ordenes/*",
            "reportes": "/reportes/*"
        }
    }), 200

@main_bp.route('/health')
def health():
    """Endpoint de salud para monitoreo"""
    return jsonify({
        "status": "healthy",
        "service": "gestion_inventarios"
    }), 200

from flask import Blueprint, jsonify

# Blueprint principal para la ruta raíz
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Ruta principal - Health check de la API"""
    return jsonify({
        "message": "API de Gestión de Inventarios",
        "status": "running",
        "version": "1.0",
        "endpoints": {
            "auth": "/login, /logout, /register",
            "dashboard": "/dashboard",
            "inventario": "/inventario/*",
            "compras": "/compras/*",
            "ventas": "/ventas/*",
            "ordenes": "/ordenes/*",
            "reportes": "/reportes/*"
        }
    }), 200

@main_bp.route('/health')
def health():
    """Endpoint de salud para monitoreo"""
    return jsonify({
        "status": "healthy",
        "service": "gestion_inventarios"
    }), 200