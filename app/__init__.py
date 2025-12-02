from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
import os
from urllib.parse import quote_plus

# Inicializar extensiones
db = SQLAlchemy()
migrate = Migrate()

def get_database_uri():
    """
    Obtiene la URI de base de datos según el entorno.
    """
    # Railway Postgres (recomendado)
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Railway Postgres ya viene listo
        print(f"🔗 Usando DATABASE_URL (Postgres)")
        return database_url
    
    # Fallback a MySQL local
    host = os.getenv('MYSQL_HOST', 'db')
    user = os.getenv('MYSQL_USER', 'admin')
    password = os.getenv('MYSQL_PASSWORD', 'adminpass')
    database = os.getenv('MYSQL_DATABASE', 'plataforma_db')
    port = os.getenv('MYSQL_PORT', '3306')
    
    password_encoded = quote_plus(password)
    
    uri = f"mysql+pymysql://{user}:{password_encoded}@{host}:{port}/{database}"
    print(f"🐳 Conectando a MySQL local: {host}:{port}/{database}")
    return uri

def create_app():
    app = Flask(__name__)
    CORS(app, supports_credentials=True)

    # ============================================
    # ⚙️ CONFIGURACIÓN GENERAL
    # ============================================
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'clave_super_segura_cambiar_en_produccion')
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # 🔥 CAMBIO PRINCIPAL: Usa la función get_database_uri()
    app.config['SQLALCHEMY_DATABASE_URI'] = get_database_uri()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configuración adicional para producción
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,        # Verifica conexiones antes de usarlas
        'pool_recycle': 300,           # Recicla conexiones cada 5 minutos
        'pool_size': 10,
        'max_overflow': 20
    }

    # Inicializar base de datos y migraciones
    db.init_app(app)
    migrate.init_app(app, db)

    # ==============================
    # Filtro personalizado "date"
    # ==============================
    @app.template_filter('date')
    def format_date(value, format="%d/%m/%Y %H:%M"):
        """
        Permite usar {{ variable|date("%d/%m/%Y") }} en plantillas Jinja.
        Si la variable no es una fecha válida, se devuelve tal cual.
        """
        try:
            return value.strftime(format)
        except Exception:
            return value
    
    # ==============================
    # 🔐 Inyectar funciones de permisos en templates
    # ==============================
    @app.context_processor
    def utility_processor():
        """Inyecta funciones útiles en todos los templates"""
        from app.utils.decorators import inject_permissions
        return inject_permissions()

    # ==============================
    # 📦 Contexto de aplicación
    # ==============================
    with app.app_context():
        # Importar modelos existentes dentro del contexto
        try:
            from app.models import compra_model
            print("✅ Modelo de compras cargado")
        except ImportError as e:
            print(f"⚠️ Modelo de compras no encontrado: {e}")
        
        try:
            from app.models import inventario_model
            print("✅ Modelo de inventario cargado")
        except ImportError as e:
            print(f"⚠️ Modelo de inventario no encontrado: {e}")
        
        try:
            from app.models import venta_model
            print("✅ Modelo de ventas cargado")
        except ImportError as e:
            print(f"⚠️ Modelo de ventas no encontrado: {e}")
        
        try:
            from app.models import orden_model
            print("✅ Modelo de órdenes cargado")
        except ImportError as e:
            print(f"⚠️ Modelo de órdenes no encontrado: {e}")
        
        # 🆕 SISTEMA DE ROLES Y USUARIOS
        try:
            from app.models import user_role_model
            print("✅ Modelos de usuarios y roles cargados")
        except ImportError as e:
            print(f"⚠️ Modelos de usuarios y roles no encontrados: {e}")
        
        try:
            from app.models import inventario_model
        except ImportError:
            pass
        try:
            from app.models import venta_model
        except ImportError:
            pass
        try:
            from app.models import orden_model
        except ImportError:
            pass
        
        # 📦 SISTEMA DE CÓDIGOS DE BARRAS: Importar modelos
        try:
            from app.models import product_model
            print("✅ Modelo de productos con códigos de barras cargado")
        except ImportError as e:
            print(f"⚠️ Modelo de productos con códigos de barras no encontrado: {e}")

        # ==============================
        # 📂 Registrar Blueprints (rutas)
        # ==============================
        from app.routes.main_routes import main_bp
        from app.routes.auth_routes import auth_bp
        from app.routes.dashboard_routes import dashboard_bp
        from app.routes.compras_routes import compras_bp
        from app.routes.inventario_routes import inventario_bp
        from app.routes.ventas_routes import ventas_bp
        from app.routes.reportes_routes import reportes_bp
        from app.routes.ordenes_routes import ordenes_bp

        app.register_blueprint(main_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(dashboard_bp)
        app.register_blueprint(compras_bp)
        app.register_blueprint(inventario_bp)
        app.register_blueprint(ventas_bp)
        app.register_blueprint(reportes_bp)
        app.register_blueprint(ordenes_bp)
        
        # 📦 SISTEMA DE CÓDIGOS DE BARRAS: Registrar blueprint
        try:
            from app.routes.barcode_routes import barcode_bp
            app.register_blueprint(barcode_bp)
            print("✅ Blueprint de códigos de barras registrado en /barcode")
        except ImportError as e:
            print(f"⚠️ Blueprint de códigos de barras no encontrado: {e}")

        # Crear tablas en caso de que no existan
        try:
            db.create_all()
            print("✅ Tablas de base de datos creadas/verificadas correctamente")
        except Exception as e:
            print(f"❌ Error al crear tablas: {e}")
# ⚠️ TEMPORAL: Inicialización de base de datos
        try:
            from app.routes.init_routes import init_bp
            app.register_blueprint(init_bp)
            print("⚠️  Blueprint de inicialización registrado (ELIMINAR DESPUÉS DE USAR)")
        except ImportError as e:
            print(f"⚠️ Blueprint de inicialización no encontrado: {e}")
            
    return app
