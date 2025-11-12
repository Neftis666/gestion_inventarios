from flask import Flask, redirect
from app import create_app  # Importa la factory de Flask

app = create_app()

# Imprimir todas las rutas definidas todas 
print("Rutas disponibles en Flask:")
for rule in app.url_map.iter_rules():
    print(f"{rule.endpoint} - {rule}")
    
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
