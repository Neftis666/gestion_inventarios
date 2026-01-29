from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from app.models.orden_model import OrdenCompra, DetalleOrden
from app.services.pdf_generator import generate_purchase_order_pdf
from app import db
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

ordenes_bp = Blueprint('ordenes', __name__, url_prefix='/ordenes')

@ordenes_bp.route('/')
def listar_ordenes():
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))
    
    search = request.args.get('search', '')
    estado = request.args.get('estado', '')
    fecha_desde = request.args.get('fecha_desde', '')
    fecha_hasta = request.args.get('fecha_hasta', '')
    
    query = OrdenCompra.query
    
    if search:
        query = query.filter(
            (OrdenCompra.numero_orden.like(f'%{search}%')) |
            (OrdenCompra.proveedor.like(f'%{search}%'))
        )
    
    if estado:
        query = query.filter_by(estado=estado)
    
    if fecha_desde:
        query = query.filter(OrdenCompra.fecha >= datetime.strptime(fecha_desde, '%Y-%m-%d'))
    
    if fecha_hasta:
        query = query.filter(OrdenCompra.fecha <= datetime.strptime(fecha_hasta, '%Y-%m-%d'))
    
    ordenes = query.order_by(OrdenCompra.fecha.desc()).all()
    
    total_ordenes = OrdenCompra.query.count()
    pendientes = OrdenCompra.query.filter_by(estado='pendiente').count()
    completadas = OrdenCompra.query.filter_by(estado='completada').count()
    canceladas = OrdenCompra.query.filter_by(estado='cancelada').count()
    
    return render_template('ordenes/listar.html',
                         ordenes=ordenes,
                         total_ordenes=total_ordenes,
                         pendientes=pendientes,
                         completadas=completadas,
                         canceladas=canceladas,
                         search=search,
                         estado_filtro=estado,
                         fecha_desde=fecha_desde,
                         fecha_hasta=fecha_hasta)

@ordenes_bp.route('/nueva', methods=['GET', 'POST'])
def nueva_orden():
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        try:
            # Campos del cliente (antes proveedor)
            proveedor = request.form.get('proveedor')  # Mantener nombre interno
            direccion_proveedor = request.form.get('direccion_proveedor')
            telefono_proveedor = request.form.get('telefono_proveedor')
            
            # Nuevos campos
            fecha_emision_str = request.form.get('fecha_emision')
            numero_orden_cliente = request.form.get('numero_orden_cliente')
            sucursal_cliente = request.form.get('sucursal_cliente')
            observaciones = request.form.get('observaciones')
            
            # Convertir fecha de emisión
            fecha_emision = None
            if fecha_emision_str:
                try:
                    fecha_emision = datetime.strptime(fecha_emision_str, '%Y-%m-%d').date()
                except:
                    fecha_emision = datetime.now().date()
            
            productos = request.form.getlist('producto[]')
            cantidades = request.form.getlist('cantidad[]')
            unidades = request.form.getlist('unidad[]')
            precios = request.form.getlist('precio[]')
            
            iva_porcentaje = float(request.form.get('iva', 19))
            descuento = float(request.form.get('descuento', 0))
            
            if not productos:
                flash('Debes agregar al menos un producto.', 'danger')
                return redirect(url_for('ordenes.nueva_orden'))
            
            ultima_orden = OrdenCompra.query.order_by(OrdenCompra.id.desc()).first()
            if ultima_orden:
                ultimo_num = int(ultima_orden.numero_orden.split('-')[-1])
                numero_orden = f"OC-{datetime.now().year}-{ultimo_num + 1:04d}"
            else:
                numero_orden = f"OC-{datetime.now().year}-0001"
            
            subtotal = 0
            detalles = []
            
            for i, producto in enumerate(productos):
                if not producto.strip():
                    continue
                    
                cantidad = int(cantidades[i])
                unidad = unidades[i]
                precio = float(precios[i])
                
                subtotal_detalle = cantidad * precio
                subtotal += subtotal_detalle
                
                detalles.append({
                    'descripcion': producto,
                    'cantidad': cantidad,
                    'unidad': unidad,
                    'precio': precio,
                    'subtotal': subtotal_detalle
                })
            
            iva = subtotal * (iva_porcentaje / 100)
            total = subtotal + iva - descuento
            
            nueva_orden = OrdenCompra(
                numero_orden=numero_orden,
                proveedor=proveedor,
                direccion_proveedor=direccion_proveedor,
                telefono_proveedor=telefono_proveedor,
                fecha_emision=fecha_emision,
                numero_orden_cliente=numero_orden_cliente,
                sucursal_cliente=sucursal_cliente,
                subtotal=subtotal,
                iva=iva,
                descuento=descuento,
                total=total,
                elaborado_por=session.get('username'),
                observaciones=observaciones
            )
            
            db.session.add(nueva_orden)
            db.session.flush()
            
            for detalle_data in detalles:
                detalle = DetalleOrden(
                    orden_id=nueva_orden.id,
                    producto_descripcion=detalle_data['descripcion'],
                    cantidad=detalle_data['cantidad'],
                    unidad_medida=detalle_data['unidad'],
                    precio_unitario=detalle_data['precio'],
                    subtotal=detalle_data['subtotal']
                )
                db.session.add(detalle)
            
            db.session.commit()
            
            flash(f'Orden de compra {numero_orden} creada exitosamente.', 'success')
            return redirect(url_for('ordenes.detalle_orden', id=nueva_orden.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear orden: {str(e)}', 'danger')
            return redirect(url_for('ordenes.nueva_orden'))
    
    return render_template('ordenes/nueva.html')

@ordenes_bp.route('/detalle/<int:id>')
def detalle_orden(id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))
    
    orden = OrdenCompra.query.get_or_404(id)
    return render_template('ordenes/detalle.html', orden=orden)

@ordenes_bp.route('/cambiar-estado/<int:id>', methods=['POST'])
def cambiar_estado(id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))
    
    try:
        orden = OrdenCompra.query.get_or_404(id)
        nuevo_estado = request.form.get('estado')
        
        if nuevo_estado in ['pendiente', 'aprobada', 'completada', 'cancelada']:
            orden.estado = nuevo_estado
            if nuevo_estado == 'aprobada' and not orden.verificado_por:
                orden.verificado_por = session.get('username')
            db.session.commit()
            flash(f'Estado actualizado a: {nuevo_estado}', 'success')
        else:
            flash('Estado no válido.', 'danger')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar estado: {str(e)}', 'danger')
    
    return redirect(url_for('ordenes.detalle_orden', id=id))

@ordenes_bp.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_orden(id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))
    
    try:
        orden = OrdenCompra.query.get_or_404(id)
        
        # Validar si la orden puede ser eliminada
        if orden.estado == 'completada':
            flash('No se puede eliminar una orden completada.', 'warning')
            return redirect(url_for('ordenes.listar_ordenes'))
        
        numero_orden = orden.numero_orden
        
        # Eliminar detalles primero
        DetalleOrden.query.filter_by(orden_id=id).delete()
        
        # Eliminar orden
        db.session.delete(orden)
        db.session.commit()
        
        flash(f'Orden {numero_orden} eliminada exitosamente.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar orden: {str(e)}', 'danger')
    
    return redirect(url_for('ordenes.listar_ordenes'))

@ordenes_bp.route('/generar-pdf/<int:id>')
def generar_pdf(id):
    """Genera PDF ejecutivo de la orden de compra"""
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))
    
    try:
        # Obtener la orden con sus detalles
        orden = OrdenCompra.query.get_or_404(id)
        
        # Crear buffer para el PDF
        buffer = BytesIO()
        
        # Generar PDF usando el servicio
        generate_purchase_order_pdf(orden, buffer)
        
        # Posicionar el buffer al inicio
        buffer.seek(0)
        
        # Enviar el archivo PDF
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f'orden_{orden.numero_orden}.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        flash(f'Error al generar PDF: {str(e)}', 'danger')
        return redirect(url_for('ordenes.detalle_orden', id=id))

@ordenes_bp.route('/reporte', methods=['GET'])
def reporte_ordenes():
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))

    ordenes = OrdenCompra.query.all()
    total_ordenes = len(ordenes)
    total_monto = sum(o.total for o in ordenes if hasattr(o, 'total') and o.total)

    return render_template('ordenes/reporte.html', ordenes=ordenes, total_ordenes=total_ordenes, total_monto=total_monto)

@ordenes_bp.route('/reporte/pdf', methods=['GET'])
def generar_reporte_pdf():
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))

    ordenes = OrdenCompra.query.order_by(OrdenCompra.fecha.desc()).all()
    total_ordenes = len(ordenes)
    total_monto = sum(o.total for o in ordenes if o.total)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=40, rightMargin=40, topMargin=60, bottomMargin=40)

    styles = getSampleStyleSheet()
    elementos = []

    titulo = Paragraph("<b>REPORTE DE ORDENES DE COMPRA</b>", styles['Title'])
    empresa = Paragraph("<b>Plataforma Butacors</b> - Sistema de Gestion Comercial", styles['Normal'])
    fecha_gen = Paragraph(f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal'])

    elementos.extend([titulo, empresa, fecha_gen, Spacer(1, 12)])

    resumen = [["Total de Ordenes", total_ordenes], ["Monto Total Acumulado", f"${total_monto:,.2f}"]]
    tabla_resumen = Table(resumen, colWidths=[200, 200])
    tabla_resumen.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black)
    ]))
    elementos.extend([tabla_resumen, Spacer(1, 20)])

    data = [["N° Orden", "Proveedor", "Fecha", "Estado", "Total"]]

    for o in ordenes:
        data.append([
            o.numero_orden or "—",
            o.proveedor or "—",
            o.fecha.strftime("%d/%m/%Y") if o.fecha else "—",
            o.estado.capitalize() if o.estado else "—",
            f"${o.total:,.2f}" if o.total else "$0.00"
        ])

    tabla = Table(data, colWidths=[100, 200, 100, 100, 100])
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
    ]))
    elementos.append(tabla)

    elementos.extend([
        Spacer(1, 25),
        Paragraph(f"<i>Reporte generado por: {session.get('username', '—')}</i>", styles['Normal']),
        Paragraph("<i>© Plataforma Butacors</i>", styles['Normal'])
    ])

    doc.build(elementos)
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True, download_name=f'reporte_ordenes_{datetime.now().strftime("%Y%m%d")}.pdf', mimetype='application/pdf')
