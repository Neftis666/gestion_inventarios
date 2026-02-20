from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from app.models.orden_proveedor_model import OrdenProveedor, DetalleOrdenProveedor
from app import db
from datetime import datetime
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4

ordenes_proveedor_bp = Blueprint('ordenes_proveedor', __name__, url_prefix='/ordenes-proveedor')


def get_proveedores():
    """Intenta obtener proveedores de la tabla si existe"""
    try:
        from app.models.proveedor_model import Proveedor
        return Proveedor.query.filter_by(estado='activo').order_by(Proveedor.nombre).all()
    except Exception:
        return []


@ordenes_proveedor_bp.route('/')
def listar_ordenes():
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))

    search = request.args.get('search', '')
    estado = request.args.get('estado', '')
    fecha_desde = request.args.get('fecha_desde', '')
    fecha_hasta = request.args.get('fecha_hasta', '')

    query = OrdenProveedor.query

    if search:
        query = query.filter(
            (OrdenProveedor.numero_orden.like(f'%{search}%')) |
            (OrdenProveedor.proveedor.like(f'%{search}%'))
        )

    if estado:
        query = query.filter_by(estado=estado)

    if fecha_desde:
        query = query.filter(OrdenProveedor.fecha >= datetime.strptime(fecha_desde, '%Y-%m-%d'))

    if fecha_hasta:
        query = query.filter(OrdenProveedor.fecha <= datetime.strptime(fecha_hasta, '%Y-%m-%d'))

    ordenes = query.order_by(OrdenProveedor.fecha.desc()).all()

    total_ordenes = OrdenProveedor.query.count()
    pendientes = OrdenProveedor.query.filter_by(estado='pendiente').count()
    completadas = OrdenProveedor.query.filter_by(estado='completada').count()
    canceladas = OrdenProveedor.query.filter_by(estado='cancelada').count()

    return render_template('ordenes_proveedor/listar.html',
                           ordenes=ordenes,
                           total_ordenes=total_ordenes,
                           pendientes=pendientes,
                           completadas=completadas,
                           canceladas=canceladas,
                           search=search,
                           estado_filtro=estado,
                           fecha_desde=fecha_desde,
                           fecha_hasta=fecha_hasta)


@ordenes_proveedor_bp.route('/nueva', methods=['GET', 'POST'])
def nueva_orden():
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))

    proveedores_lista = get_proveedores()

    if request.method == 'POST':
        try:
            # Proveedor: de lista o manual
            proveedor_id = request.form.get('proveedor_id')
            proveedor_manual = request.form.get('proveedor_manual', '').strip()

            if proveedor_id and proveedor_id != '0':
                # Viene de la lista desplegable
                from app.models.proveedor_model import Proveedor
                prov = Proveedor.query.get(proveedor_id)
                proveedor_nombre = prov.nombre if prov else proveedor_manual
                direccion = prov.direccion if prov else ''
                telefono = prov.telefono if prov else ''
            else:
                # Manual
                proveedor_nombre = proveedor_manual
                direccion = request.form.get('direccion_proveedor', '')
                telefono = request.form.get('telefono_proveedor', '')

            if not proveedor_nombre:
                flash('Debes indicar el proveedor.', 'danger')
                return render_template('ordenes_proveedor/nueva.html', proveedores=proveedores_lista)

            fecha_emision_str = request.form.get('fecha_emision')
            fecha_emision = None
            if fecha_emision_str:
                try:
                    fecha_emision = datetime.strptime(fecha_emision_str, '%Y-%m-%d').date()
                except Exception:
                    fecha_emision = datetime.now().date()

            numero_orden_cliente = request.form.get('numero_orden_cliente')
            sucursal_cliente = request.form.get('sucursal_cliente')
            observaciones = request.form.get('observaciones')

            productos = request.form.getlist('producto[]')
            cantidades = request.form.getlist('cantidad[]')
            unidades = request.form.getlist('unidad[]')
            precios = request.form.getlist('precio[]')
            iva_porcentaje = float(request.form.get('iva', 19))
            descuento = float(request.form.get('descuento', 0))

            if not productos or all(p.strip() == '' for p in productos):
                flash('Debes agregar al menos un producto.', 'danger')
                return render_template('ordenes_proveedor/nueva.html', proveedores=proveedores_lista)

            # Generar número de orden
            ultima = OrdenProveedor.query.order_by(OrdenProveedor.id.desc()).first()
            if ultima:
                ultimo_num = int(ultima.numero_orden.split('-')[-1])
                numero_orden = f"OP-{datetime.now().year}-{ultimo_num + 1:04d}"
            else:
                numero_orden = f"OP-{datetime.now().year}-0001"

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

            nueva = OrdenProveedor(
                numero_orden=numero_orden,
                proveedor_id=int(proveedor_id) if proveedor_id and proveedor_id != '0' else None,
                proveedor=proveedor_nombre,
                direccion_proveedor=direccion,
                telefono_proveedor=telefono,
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

            db.session.add(nueva)
            db.session.flush()

            for d in detalles:
                detalle = DetalleOrdenProveedor(
                    orden_id=nueva.id,
                    producto_descripcion=d['descripcion'],
                    cantidad=d['cantidad'],
                    unidad_medida=d['unidad'],
                    precio_unitario=d['precio'],
                    subtotal=d['subtotal']
                )
                db.session.add(detalle)

            db.session.commit()
            flash(f'Orden {numero_orden} creada exitosamente.', 'success')
            return redirect(url_for('ordenes_proveedor.detalle_orden', id=nueva.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear orden: {str(e)}', 'danger')

    return render_template('ordenes_proveedor/nueva.html', proveedores=proveedores_lista)


@ordenes_proveedor_bp.route('/detalle/<int:id>')
def detalle_orden(id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))

    orden = OrdenProveedor.query.get_or_404(id)
    return render_template('ordenes_proveedor/detalle.html', orden=orden)


@ordenes_proveedor_bp.route('/cambiar-estado/<int:id>', methods=['POST'])
def cambiar_estado(id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))

    try:
        orden = OrdenProveedor.query.get_or_404(id)
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

    return redirect(url_for('ordenes_proveedor.detalle_orden', id=id))


@ordenes_proveedor_bp.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_orden(id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))

    try:
        orden = OrdenProveedor.query.get_or_404(id)

        if orden.estado == 'completada':
            flash('No se puede eliminar una orden completada.', 'warning')
            return redirect(url_for('ordenes_proveedor.listar_ordenes'))

        numero_orden = orden.numero_orden
        DetalleOrdenProveedor.query.filter_by(orden_id=id).delete()
        db.session.delete(orden)
        db.session.commit()
        flash(f'Orden {numero_orden} eliminada exitosamente.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar: {str(e)}', 'danger')

    return redirect(url_for('ordenes_proveedor.listar_ordenes'))


@ordenes_proveedor_bp.route('/reporte/pdf')
def reporte_pdf():
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))

    ordenes = OrdenProveedor.query.order_by(OrdenProveedor.fecha.desc()).all()
    total_ordenes = len(ordenes)
    total_monto = sum(o.total for o in ordenes if o.total)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            leftMargin=40, rightMargin=40, topMargin=60, bottomMargin=40)
    styles = getSampleStyleSheet()
    elementos = []

    titulo = Paragraph("<b>REPORTE DE ÓRDENES DE PROVEEDORES</b>", styles['Title'])
    fecha_gen = Paragraph(f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')} | Por: {session.get('username', '—')}", styles['Normal'])
    elementos.extend([titulo, fecha_gen, Spacer(1, 12)])

    resumen = [["Total Órdenes", total_ordenes], ["Monto Total", f"${total_monto:,.2f}"]]
    tabla_resumen = Table(resumen, colWidths=[200, 200])
    tabla_resumen.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
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
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")])
    ]))
    elementos.append(tabla)

    doc.build(elementos)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True,
                     download_name=f'reporte_ordenes_proveedor_{datetime.now().strftime("%Y%m%d")}.pdf',
                     mimetype='application/pdf')
