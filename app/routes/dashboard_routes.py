from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from app.models.user_model import User
from app.models.compra_model import Compra
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func, extract

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
def dashboard():
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))
    
    try:
        # Parámetros de filtro
        periodo = request.args.get('periodo', 'mes')
        moneda = request.args.get('moneda', 'COP')
        tasa_usd = 4200
        
        # Calcular fechas
        hoy = datetime.now()
        if periodo == 'hoy':
            fecha_inicio = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
        elif periodo == 'semana':
            fecha_inicio = hoy - timedelta(days=hoy.weekday())
            fecha_inicio = fecha_inicio.replace(hour=0, minute=0, second=0, microsecond=0)
        elif periodo == 'anio':
            fecha_inicio = hoy.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            fecha_inicio = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Variables por defecto
        total_users = User.query.count()
        total_compras = Compra.query.filter(Compra.fecha >= fecha_inicio).count()
        suma_compras = db.session.query(func.sum(Compra.total)).filter(
            Compra.fecha >= fecha_inicio
        ).scalar() or 0
        
        total_ventas = 0
        suma_ventas = 0
        total_productos = 0
        stock_critico = 0
        stock_bajo = 0
        ordenes_pendientes = 0
        productos_mas_vendidos = []
        clientes_principales = []
        compras_por_mes = []
        ventas_por_mes = []
        margen = 0
        
        # VENTAS
        try:
            from app.models.venta_model import Venta, Cliente, DetalleVenta
            from app.models.inventario_model import Producto
            
            total_ventas = Venta.query.filter(
                Venta.estado == 'completada',
                Venta.fecha >= fecha_inicio
            ).count()
            
            suma_ventas = db.session.query(func.sum(Venta.total)).filter(
                Venta.estado == 'completada',
                Venta.fecha >= fecha_inicio
            ).scalar() or 0
            
            # Top 5 productos más vendidos
            try:
                productos_vendidos = db.session.query(
                    Producto.nombre,
                    func.sum(DetalleVenta.cantidad).label('total_vendido')
                ).join(
                    DetalleVenta, Producto.id == DetalleVenta.producto_id
                ).join(
                    Venta, DetalleVenta.venta_id == Venta.id
                ).filter(
                    Venta.estado == 'completada',
                    Venta.fecha >= fecha_inicio
                ).group_by(
                    Producto.nombre
                ).order_by(
                    func.sum(DetalleVenta.cantidad).desc()
                ).limit(5).all()
                
                productos_mas_vendidos = [
                    {
                        'nombre': p[0][:20] + '...' if len(p[0]) > 20 else p[0],
                        'cantidad': int(p[1])
                    } for p in productos_vendidos
                ]
            except Exception as e:
                print(f"Error productos vendidos: {e}")
            
            # Top 5 clientes principales
            try:
                clientes_top = db.session.query(
                    Cliente.nombre,
                    func.sum(Venta.total).label('total_gastado')
                ).join(
                    Venta, Cliente.id == Venta.cliente_id
                ).filter(
                    Venta.estado == 'completada',
                    Venta.fecha >= fecha_inicio
                ).group_by(
                    Cliente.nombre
                ).order_by(
                    func.sum(Venta.total).desc()
                ).limit(5).all()
                
                clientes_principales = [
                    {
                        'nombre': c[0][:25] + '...' if len(c[0]) > 25 else c[0],
                        'total': float(c[1])
                    } for c in clientes_top
                ]
            except Exception as e:
                print(f"Error clientes principales: {e}")
            
            # Ventas por mes (últimos 6 meses)
            try:
                seis_meses_atras = hoy - timedelta(days=180)
                ventas_mensuales = db.session.query(
                    extract('month', Venta.fecha).label('mes'),
                    extract('year', Venta.fecha).label('anio'),
                    func.sum(Venta.total).label('total')
                ).filter(
                    Venta.estado == 'completada',
                    Venta.fecha >= seis_meses_atras
                ).group_by(
                    'mes', 'anio'
                ).order_by(
                    'anio', 'mes'
                ).all()
                
                ventas_por_mes = [
                    {
                        'mes': f"{int(v[1])}-{int(v[0]):02d}",
                        'total': float(v[2])
                    } for v in ventas_mensuales
                ]
            except Exception as e:
                print(f"Error ventas mensuales: {e}")
                
        except ImportError as e:
            print(f"Error al importar modelos de ventas: {e}")
        except Exception as e:
            print(f"Error general en ventas: {e}")
        
        # INVENTARIO
        try:
            from app.models.inventario_model import Producto
            total_productos = Producto.query.count()
            stock_critico = Producto.query.filter(Producto.cantidad <= 5).count()
            stock_bajo = Producto.query.filter(
                Producto.cantidad > 5,
                Producto.cantidad <= 10
            ).count()
        except Exception as e:
            print(f"Error inventario: {e}")
        
        # ÓRDENES
        try:
            from app.models.orden_model import OrdenCompra
            ordenes_pendientes = OrdenCompra.query.filter_by(estado='pendiente').count()
        except Exception as e:
            print(f"Error órdenes: {e}")
        
        # Compras por mes (últimos 6 meses)
        try:
            seis_meses_atras = hoy - timedelta(days=180)
            compras_mensuales = db.session.query(
                extract('month', Compra.fecha).label('mes'),
                extract('year', Compra.fecha).label('anio'),
                func.sum(Compra.total).label('total')
            ).filter(
                Compra.fecha >= seis_meses_atras
            ).group_by(
                'mes', 'anio'
            ).order_by(
                'anio', 'mes'
            ).all()
            
            compras_por_mes = [
                {
                    'mes': f"{int(c[1])}-{int(c[0]):02d}",
                    'total': float(c[2])
                } for c in compras_mensuales
            ]
        except Exception as e:
            print(f"Error compras mensuales: {e}")
        
        # Conversión de moneda
        if moneda == 'USD':
            suma_compras = suma_compras / tasa_usd
            suma_ventas = suma_ventas / tasa_usd
            for c in clientes_principales:
                c['total'] = c['total'] / tasa_usd
            for v in ventas_por_mes:
                v['total'] = v['total'] / tasa_usd
            for c in compras_por_mes:
                c['total'] = c['total'] / tasa_usd
        
        # Calcular margen
        if suma_ventas > 0:
            margen = ((suma_ventas - suma_compras) / suma_ventas) * 100
        
        return render_template('dashboard.html',
                             total_users=total_users,
                             total_compras=total_compras,
                             suma_compras=suma_compras,
                             total_ventas=total_ventas,
                             suma_ventas=suma_ventas,
                             total_productos=total_productos,
                             stock_critico=stock_critico,
                             stock_bajo=stock_bajo,
                             ordenes_pendientes=ordenes_pendientes,
                             margen=margen,
                             productos_mas_vendidos=productos_mas_vendidos,
                             clientes_principales=clientes_principales,
                             compras_por_mes=compras_por_mes,
                             ventas_por_mes=ventas_por_mes,
                             periodo=periodo,
                             moneda=moneda)
    
    except Exception as e:
        print(f"ERROR CRÍTICO DASHBOARD: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Error al cargar dashboard: {str(e)}', 'danger')
        
        # Retornar valores por defecto
        return render_template('dashboard.html',
                             total_users=0,
                             total_compras=0,
                             suma_compras=0,
                             total_ventas=0,
                             suma_ventas=0,
                             total_productos=0,
                             stock_critico=0,
                             stock_bajo=0,
                             ordenes_pendientes=0,
                             margen=0,
                             productos_mas_vendidos=[],
                             clientes_principales=[],
                             compras_por_mes=[],
                             ventas_por_mes=[],
                             periodo='mes',
                             moneda='COP')