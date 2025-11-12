from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
import os

# Inicializar extensiones
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    CORS(app, supports_credentials=True)

    # Configuración general
    app.config['SECRET_KEY'] = 'clave_super_segura_cambiar_en_produccion'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql+pymysql://admin:adminpass@mysql_db:3306/plataforma_db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    

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
    # 📦 Contexto de aplicación
    # ==============================
    with app.app_context():
        # Importar modelos dentro del contexto
        from app.models import user_model, role_model, compra_model
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

        # ==============================
        # 📂 Registrar Blueprints (rutas)
        # ==============================
        from app.routes.auth_routes import auth_bp
        from app.routes.dashboard_routes import dashboard_bp
        from app.routes.compras_routes import compras_bp
        from app.routes.inventario_routes import inventario_bp
        from app.routes.ventas_routes import ventas_bp
        from app.routes.reportes_routes import reportes_bp
        from app.routes.ordenes_routes import ordenes_bp

        app.register_blueprint(auth_bp)
        app.register_blueprint(dashboard_bp)
        app.register_blueprint(compras_bp)
        app.register_blueprint(inventario_bp)
        app.register_blueprint(ventas_bp)
        app.register_blueprint(reportes_bp)
        app.register_blueprint(ordenes_bp)

        # Crear tablas en caso de que no existan
        db.create_all()

    return app
