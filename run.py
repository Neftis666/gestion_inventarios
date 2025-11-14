# run.py
import os
from app import create_app, db

# Crear la aplicación
app = create_app()

if __name__ == '__main__':
    # Información de debug
    env = os.getenv('FLASK_ENV', 'development')
    port = int(os.getenv('PORT', 5000))
    
    print("=" * 60)
    print(f"🚀 Iniciando aplicación")
    print(f"📍 Entorno: {env}")
    print(f"🔌 Puerto: {port}")
    print(f"🗄️  Railway: {'SÍ' if os.getenv('MYSQLHOST') else 'NO (Docker Compose)'}")
    print("=" * 60)
    
    # Iniciar servidor
    app.run(
        host='0.0.0.0',
        port=port,
        debug=(env == 'development')
    )