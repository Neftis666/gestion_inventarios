from flask import Blueprint, redirect, url_for, jsonify, session

main_bp = Blueprint('home', __name__)

@main_bp.route('/')
def index():
    """Ruta principal - Redirige según autenticación"""
    if 'user_id' in session:
        # Si está autenticado, redirige al dashboard
        return redirect(url_for('dashboard.dashboard'))
    else:
        # Si no está autenticado, redirige al login
        return redirect(url_for('auth.login'))

@main_bp.route('/health')
def health():
    """Endpoint de salud para monitoreo"""
    return jsonify({
        "status": "healthy",
        "service": "gestion_inventarios"
    }), 200

@main_bp.route('/api')
def api_info():
    """Información de la API (para pruebas)"""
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