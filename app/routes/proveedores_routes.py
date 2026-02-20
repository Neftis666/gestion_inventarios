from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from app.models.proveedor_model import Proveedor
from app import db
from datetime import datetime
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4

proveedores_bp = Blueprint('proveedores', __name__, url_prefix='/proveedores')


@proveedores_bp.route('/')
def listar_proveedores():
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))

    search = request.args.get('search', '')
    estado = request.args.get('estado', '')
    tipo = request.args.get('tipo', '')

    query = Proveedor.query

    if search:
        query = query.filter(
            (Proveedor.nombre.like(f'%{search}%')) |
            (Proveedor.nit.like(f'%{search}%')) |
            (Proveedor.email.like(f'%{search}%'))
        )

    if estado:
        query = query.filter_by(estado=estado)

    if tipo:
        query = query.filter_by(tipo=tipo)

    proveedores = query.order_by(Proveedor.fecha_registro.desc()).all()

    total_proveedores = Proveedor.query.count()
    activos = Proveedor.query.filter_by(estado='activo').count()
    inactivos = Proveedor.query.filter_by(estado='inactivo').count()
    nacionales = Proveedor.query.filter_by(tipo='Nacional').count()

    return render_template('proveedores/listar.html',
                           proveedores=proveedores,
                           total_proveedores=total_proveedores,
                           activos=activos,
                           inactivos=inactivos,
                           nacionales=nacionales,
                           search=search,
                           estado_filtro=estado,
                           tipo_filtro=tipo)


@proveedores_bp.route('/nuevo', methods=['GET', 'POST'])
def nuevo_proveedor():
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        try:
            nombre = request.form.get('nombre')
            nit = request.form.get('nit')
            tipo = request.form.get('tipo', 'Nacional')
            direccion = request.form.get('direccion')
            telefono = request.form.get('telefono')
            email = request.form.get('email')
            contacto_nombre = request.form.get('contacto_nombre')
            observaciones = request.form.get('observaciones')

            if not nombre:
                flash('El nombre del proveedor es obligatorio.', 'danger')
                return redirect(url_for('proveedores.nuevo_proveedor'))

            # Verificar NIT duplicado
            if nit:
                existente = Proveedor.query.filter_by(nit=nit).first()
                if existente:
                    flash(f'Ya existe un proveedor con el NIT {nit}.', 'danger')
                    return redirect(url_for('proveedores.nuevo_proveedor'))

            proveedor = Proveedor(
                nombre=nombre,
                nit=nit,
                tipo=tipo,
                direccion=direccion,
                telefono=telefono,
                email=email,
                contacto_nombre=contacto_nombre,
                observaciones=observaciones,
                registrado_por=session.get('username')
            )

            db.session.add(proveedor)
            db.session.commit()

            flash(f'Proveedor "{nombre}" creado exitosamente.', 'success')
            return redirect(url_for('proveedores.listar_proveedores'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear proveedor: {str(e)}', 'danger')
            return redirect(url_for('proveedores.nuevo_proveedor'))

    return render_template('proveedores/nuevo.html')


@proveedores_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_proveedor(id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))

    proveedor = Proveedor.query.get_or_404(id)

    if request.method == 'POST':
        try:
            nit_nuevo = request.form.get('nit')

            # Verificar NIT duplicado (excluyendo el actual)
            if nit_nuevo:
                existente = Proveedor.query.filter(
                    Proveedor.nit == nit_nuevo,
                    Proveedor.id != id
                ).first()
                if existente:
                    flash(f'Ya existe otro proveedor con el NIT {nit_nuevo}.', 'danger')
                    return redirect(url_for('proveedores.editar_proveedor', id=id))

            proveedor.nombre = request.form.get('nombre')
            proveedor.nit = nit_nuevo
            proveedor.tipo = request.form.get('tipo', 'Nacional')
            proveedor.direccion = request.form.get('direccion')
            proveedor.telefono = request.form.get('telefono')
            proveedor.email = request.form.get('email')
            proveedor.contacto_nombre = request.form.get('contacto_nombre')
            proveedor.estado = request.form.get('estado', 'activo')
            proveedor.observaciones = request.form.get('observaciones')

            db.session.commit()

            flash(f'Proveedor "{proveedor.nombre}" actualizado exitosamente.', 'success')
            return redirect(url_for('proveedores.listar_proveedores'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar proveedor: {str(e)}', 'danger')

    return render_template('proveedores/editar.html', proveedor=proveedor)


@proveedores_bp.route('/detalle/<int:id>')
def detalle_proveedor(id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))

    proveedor = Proveedor.query.get_or_404(id)
    return render_template('proveedores/detalle.html', proveedor=proveedor)


@proveedores_bp.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_proveedor(id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))

    try:
        proveedor = Proveedor.query.get_or_404(id)
        nombre = proveedor.nombre
        db.session.delete(proveedor)
        db.session.commit()
        flash(f'Proveedor "{nombre}" eliminado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar proveedor: {str(e)}', 'danger')

    return redirect(url_for('proveedores.listar_proveedores'))


@proveedores_bp.route('/cambiar-estado/<int:id>', methods=['POST'])
def cambiar_estado(id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))

    try:
        proveedor = Proveedor.query.get_or_404(id)
        nuevo_estado = request.form.get('estado')

        if nuevo_estado in ['activo', 'inactivo']:
            proveedor.estado = nuevo_estado
            db.session.commit()
            flash(f'Estado actualizado a: {nuevo_estado}', 'success')
        else:
            flash('Estado no válido.', 'danger')

    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar estado: {str(e)}', 'danger')

    return redirect(url_for('proveedores.listar_proveedores'))


@proveedores_bp.route('/reporte/pdf')
def reporte_pdf():
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))

    proveedores = Proveedor.query.order_by(Proveedor.nombre).all()
    total = len(proveedores)
    activos = sum(1 for p in proveedores if p.estado == 'activo')

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            leftMargin=40, rightMargin=40,
                            topMargin=60, bottomMargin=40)

    styles = getSampleStyleSheet()
    elementos = []

    titulo = Paragraph("<b>REPORTE DE PROVEEDORES</b>", styles['Title'])
    fecha_gen = Paragraph(f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')} | Por: {session.get('username', '—')}", styles['Normal'])
    elementos.extend([titulo, fecha_gen, Spacer(1, 12)])

    resumen = [["Total Proveedores", total], ["Activos", activos], ["Inactivos", total - activos]]
    tabla_resumen = Table(resumen, colWidths=[200, 100])
    tabla_resumen.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black)
    ]))
    elementos.extend([tabla_resumen, Spacer(1, 20)])

    data = [["Nombre", "NIT", "Tipo", "Teléfono", "Email", "Contacto", "Estado"]]
    for p in proveedores:
        data.append([
            p.nombre or "—",
            p.nit or "—",
            p.tipo or "—",
            p.telefono or "—",
            p.email or "—",
            p.contacto_nombre or "—",
            p.estado.capitalize() if p.estado else "—"
        ])

    tabla = Table(data, colWidths=[130, 80, 70, 80, 120, 100, 60])
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
                     download_name=f'reporte_proveedores_{datetime.now().strftime("%Y%m%d")}.pdf',
                     mimetype='application/pdf')
