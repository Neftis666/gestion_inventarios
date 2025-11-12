from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from app.models.venta_model import Venta, Cliente, DetalleVenta
from app.models.inventario_model import Producto, MovimientoInventario
from app import db
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

ventas_bp = Blueprint('ventas', __name__, url_prefix='/ventas')

@ventas_bp.route('/')
def listar_ventas():
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))
    
    search = request.args.get('search', '')
    fecha_desde = request.args.get('fecha_desde', '')
    fecha_hasta = request.args.get('fecha_hasta', '')
    
    query = Venta.query
    
    if search:
        query = query.join(Cliente).filter(
            (Venta.numero_factura.like(f'%{search}%')) |
            (Cliente.nombre.like(f'%{search}%')) |
            (Cliente.documento.like(f'%{search}%'))
        )
    
    if fecha_desde:
        query = query.filter(Venta.fecha >= datetime.strptime(fecha_desde, '%Y-%m-%d'))
    
    if fecha_hasta:
        query = query.filter(Venta.fecha <= datetime.strptime(fecha_hasta, '%Y-%m-%d'))
    
    ventas = query.order_by(Venta.fecha.desc()).all()
    
    total_ventas = Venta.query.filter_by(estado='completada').count()
    suma_total = db.session.query(db.func.sum(Venta.total)).filter_by(estado='completada').scalar() or 0
    ventas_hoy = Venta.query.filter(
        Venta.fecha >= datetime.now().replace(hour=0, minute=0, second=0),
        Venta.estado == 'completada'
    ).count()
    
    return render_template('ventas/listar.html',
                         ventas=ventas,
                         total_ventas=total_ventas,
                         suma_total=suma_total,
                         ventas_hoy=ventas_hoy,
                         search=search,
                         fecha_desde=fecha_desde,
                         fecha_hasta=fecha_hasta)

@ventas_bp.route('/nueva', methods=['GET', 'POST'])
def nueva_venta():
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        try:
            cliente_id = int(request.form.get('cliente_id'))
            productos_ids = request.form.getlist('producto_id[]')
            cantidades = request.form.getlist('cantidad[]')
            precios = request.form.getlist('precio[]')
            iva_porcentaje = float(request.form.get('iva', 19))
            descuento = float(request.form.get('descuento', 0))
            
            if not productos_ids:
                flash('Debes agregar al menos un producto.', 'danger')
                return redirect(url_for('ventas.nueva_venta'))
            
            ultima_venta = Venta.query.order_by(Venta.id.desc()).first()
            if ultima_venta:
                ultimo_num = int(ultima_venta.numero_factura.split('-')[-1])
                numero_factura = f"VEN-{datetime.now().year}-{ultimo_num + 1:04d}"
            else:
                numero_factura = f"VEN-{datetime.now().year}-0001"
            
            subtotal = 0
            detalles = []
            
            for i, prod_id in enumerate(productos_ids):
                producto = Producto.query.get(int(prod_id))
                cantidad = int(cantidades[i])
                precio = float(precios[i])
                
                if producto.cantidad < cantidad:
                    flash(f'Stock insuficiente para {producto.nombre}. Disponible: {producto.cantidad}', 'danger')
                    return redirect(url_for('ventas.nueva_venta'))
                
                subtotal_detalle = cantidad * precio
                subtotal += subtotal_detalle
                
                detalles.append({
                    'producto': producto,
                    'cantidad': cantidad,
                    'precio_unitario': precio,
                    'subtotal': subtotal_detalle
                })
            
            iva = subtotal * (iva_porcentaje / 100)
            total = subtotal + iva - descuento
            
            nueva_venta = Venta(
                numero_factura=numero_factura,
                cliente_id=cliente_id,
                subtotal=subtotal,
                iva=iva,
                descuento=descuento,
                total=total,
                vendedor=session.get('username')
            )
            
            db.session.add(nueva_venta)
            db.session.flush()
            
            for detalle_data in detalles:
                detalle = DetalleVenta(
                    venta_id=nueva_venta.id,
                    producto_id=detalle_data['producto'].id,
                    cantidad=detalle_data['cantidad'],
                    precio_unitario=detalle_data['precio_unitario'],
                    subtotal=detalle_data['subtotal']
                )
                db.session.add(detalle)
                
                producto = detalle_data['producto']
                cantidad_anterior = producto.cantidad
                producto.cantidad -= detalle_data['cantidad']
                
                movimiento = MovimientoInventario(
                    producto_id=producto.id,
                    tipo='salida',
                    cantidad=detalle_data['cantidad'],
                    cantidad_anterior=cantidad_anterior,
                    cantidad_nueva=producto.cantidad,
                    motivo=f'Venta {numero_factura}',
                    usuario=session.get('username')
                )
                db.session.add(movimiento)
            
            db.session.commit()
            
            flash(f'Venta {numero_factura} registrada exitosamente. Total: ${total:,.2f}', 'success')
            return redirect(url_for('ventas.detalle_venta', id=nueva_venta.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar venta: {str(e)}', 'danger')
            return redirect(url_for('ventas.nueva_venta'))
    
    clientes = Cliente.query.order_by(Cliente.nombre).all()
    productos = Producto.query.filter(Producto.cantidad > 0, Producto.estado == 'disponible').order_by(Producto.nombre).all()
    
    return render_template('ventas/nueva.html', clientes=clientes, productos=productos)

@ventas_bp.route('/detalle/<int:id>')
def detalle_venta(id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))
    
    venta = Venta.query.get_or_404(id)
    return render_template('ventas/detalle.html', venta=venta)

@ventas_bp.route('/anular/<int:id>', methods=['POST'])
def anular_venta(id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))
    
    try:
        venta = Venta.query.get_or_404(id)
        
        if venta.estado == 'anulada':
            flash('Esta venta ya está anulada.', 'warning')
            return redirect(url_for('ventas.listar_ventas'))
        
        for detalle in venta.detalles:
            producto = detalle.producto
            cantidad_anterior = producto.cantidad
            producto.cantidad += detalle.cantidad
            
            movimiento = MovimientoInventario(
                producto_id=producto.id,
                tipo='entrada',
                cantidad=detalle.cantidad,
                cantidad_anterior=cantidad_anterior,
                cantidad_nueva=producto.cantidad,
                motivo=f'Anulación venta {venta.numero_factura}',
                usuario=session.get('username')
            )
            db.session.add(movimiento)
        
        venta.estado = 'anulada'
        db.session.commit()
        
        flash(f'Venta {venta.numero_factura} anulada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al anular: {str(e)}', 'danger')
    
    return redirect(url_for('ventas.listar_ventas'))

@ventas_bp.route('/generar-pdf/<int:id>')
def generar_pdf(id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))
    
    venta = Venta.query.get_or_404(id)
    
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    p.setFont("Helvetica-Bold", 20)
    p.drawString(1*inch, height - 1*inch, "FACTURA DE VENTA")
    
    p.setFont("Helvetica", 12)
    p.drawString(1*inch, height - 1.5*inch, f"Factura N°: {venta.numero_factura}")
    p.drawString(1*inch, height - 1.8*inch, f"Fecha: {venta.fecha.strftime('%d/%m/%Y %H:%M')}")
    p.drawString(1*inch, height - 2.1*inch, f"Cliente: {venta.cliente.nombre}")
    p.drawString(1*inch, height - 2.4*inch, f"Documento: {venta.cliente.documento}")
    p.drawString(1*inch, height - 2.7*inch, f"Vendedor: {venta.vendedor}")
    
    p.line(1*inch, height - 3*inch, width - 1*inch, height - 3*inch)
    
    p.setFont("Helvetica-Bold", 12)
    p.drawString(1*inch, height - 3.5*inch, "DETALLE DE PRODUCTOS")
    
    y = height - 4*inch
    p.setFont("Helvetica", 10)
    
    for detalle in venta.detalles:
        p.drawString(1*inch, y, f"{detalle.producto.nombre}")
        p.drawString(4*inch, y, f"Cant: {detalle.cantidad}")
        p.drawString(5*inch, y, f"Precio: ${detalle.precio_unitario:,.2f}")
        p.drawString(6.5*inch, y, f"${detalle.subtotal:,.2f}")
        y -= 0.3*inch
    
    y -= 0.3*inch
    p.line(1*inch, y, width - 1*inch, y)
    y -= 0.4*inch
    
    p.setFont("Helvetica", 11)
    p.drawString(5*inch, y, f"Subtotal: ${venta.subtotal:,.2f}")
    y -= 0.3*inch
    p.drawString(5*inch, y, f"IVA: ${venta.iva:,.2f}")
    y -= 0.3*inch
    if venta.descuento > 0:
        p.drawString(5*inch, y, f"Descuento: -${venta.descuento:,.2f}")
        y -= 0.3*inch
    
    p.setFont("Helvetica-Bold", 14)
    p.drawString(5*inch, y, f"TOTAL: ${venta.total:,.2f}")
    
    p.setFont("Helvetica-Oblique", 9)
    p.drawString(1*inch, 1*inch, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f'factura_{venta.numero_factura}.pdf', mimetype='application/pdf')

@ventas_bp.route('/clientes')
def listar_clientes():
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))
    
    clientes = Cliente.query.order_by(Cliente.nombre).all()
    return render_template('ventas/clientes.html', clientes=clientes)

@ventas_bp.route('/clientes/nuevo', methods=['GET', 'POST'])
def nuevo_cliente():
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        try:
            nombre = request.form.get('nombre')
            documento = request.form.get('documento')
            email = request.form.get('email')
            telefono = request.form.get('telefono')
            direccion = request.form.get('direccion')
            
            existe = Cliente.query.filter_by(documento=documento).first()
            if existe:
                flash('El documento ya está registrado.', 'warning')
                return redirect(url_for('ventas.nuevo_cliente'))
            
            nuevo_cliente = Cliente(
                nombre=nombre,
                documento=documento,
                email=email,
                telefono=telefono,
                direccion=direccion
            )
            
            db.session.add(nuevo_cliente)
            db.session.commit()
            
            flash(f'Cliente {nombre} registrado exitosamente.', 'success')
            return redirect(url_for('ventas.listar_clientes'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar cliente: {str(e)}', 'danger')
    
    return render_template('ventas/nuevo_cliente.html')
# ==============================
# 📊 Reporte de Ventas
# ==============================
@ventas_bp.route('/reporte', methods=['GET'])
def reporte_ventas():
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))

    # Puedes mostrar un reporte simple o reutilizar el listado de ventas
    ventas = Venta.query.all()
    total_ventas = len(ventas)
    total_monto = sum(v.total for v in ventas)

    return render_template(
        'ventas/reporte.html',
        ventas=ventas,
        total_ventas=total_ventas,
        total_monto=total_monto
    )
