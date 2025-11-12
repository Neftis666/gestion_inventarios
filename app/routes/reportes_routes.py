from flask import Blueprint, render_template, session, redirect, url_for, flash
from app.models.orden_model import OrdenCompra
from app.models.venta_model import Venta
from app.models.compra_model import Compra
from app.models.inventario_model import Producto
from datetime import datetime

reportes_bp = Blueprint('reportes', __name__, url_prefix='/reportes')

@reportes_bp.route('/')
def dashboard_reportes():
    """Dashboard central de reportes"""
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))

    # Totales generales
    total_ordenes = OrdenCompra.query.count()
    total_ventas = Venta.query.count()
    total_compras = Compra.query.count()
    total_productos = Producto.query.count()

    # Totales en dinero
    total_monto_ventas = sum(v.total for v in Venta.query.all())
    total_monto_compras = sum(c.total for c in Compra.query.all())

    # Comparativo ventas vs compras
    comparativo = {
        "labels": ["Ventas", "Compras"],
        "data": [total_monto_ventas, total_monto_compras]
    }

    # Productos más vendidos
    top_productos = [
        {"nombre": "Shampoo Keratina", "ventas": 120},
        {"nombre": "Acondicionador Coco", "ventas": 95},
        {"nombre": "Mascarilla Capilar", "ventas": 85},
        {"nombre": "Aceite de Argán", "ventas": 70},
    ]

    return render_template(
        'reportes/dashboard.html',
        total_ordenes=total_ordenes,
        total_ventas=total_ventas,
        total_compras=total_compras,
        total_productos=total_productos,
        total_monto_ventas=total_monto_ventas,
        total_monto_compras=total_monto_compras,
        comparativo=comparativo,
        top_productos=top_productos
    )
