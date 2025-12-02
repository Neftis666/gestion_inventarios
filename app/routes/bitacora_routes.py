from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from app.models.bitacora_model import Bitacora
from app.models.user_role_model import User
from app import db
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

bitacora_bp = Blueprint('bitacora', __name__, url_prefix='/bitacora')

@bitacora_bp.route('/')
def listar():
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))
    
    # Solo administradores pueden acceder
    user = User.query.get(session['user_id'])
    if user.role != 'admin':
        flash('No tienes permisos para acceder a la bitácora.', 'danger')
        return redirect(url_for('dashboard.dashboard'))
    
    # Filtros
    usuario_filtro = request.args.get('usuario', '')
    modulo_filtro = request.args.get('modulo', '')
    accion_filtro = request.args.get('accion', '')
    fecha_desde = request.args.get('fecha_desde', '')
    fecha_hasta = request.args.get('fecha_hasta', '')
    
    query = Bitacora.query
    
    if usuario_filtro:
        query = query.filter(Bitacora.usuario.like(f'%{usuario_filtro}%'))
    
    if modulo_filtro:
        query = query.filter_by(modulo=modulo_filtro)
    
    if accion_filtro:
        query = query.filter_by(accion=accion_filtro)
    
    if fecha_desde:
        query = query.filter(Bitacora.fecha >= datetime.strptime(fecha_desde, '%Y-%m-%d'))
    
    if fecha_hasta:
        fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d')
        fecha_hasta_dt = fecha_hasta_dt.replace(hour=23, minute=59, second=59)
        query = query.filter(Bitacora.fecha <= fecha_hasta_dt)
    
    # Paginación
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    eventos = query.order_by(Bitacora.fecha.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Estadísticas
    total_eventos = Bitacora.query.count()
    eventos_hoy = Bitacora.query.filter(
        Bitacora.fecha >= datetime.now().replace(hour=0, minute=0, second=0)
    ).count()
    usuarios_activos = db.session.query(Bitacora.usuario).distinct().count()
    
    # Módulos y acciones para filtros
    modulos = ['dashboard', 'compras', 'ventas', 'inventario', 'ordenes', 'reportes', 'precios', 'auth']
    acciones = ['login', 'logout', 'crear', 'editar', 'eliminar', 'exportar', 'ver']
    
    return render_template('bitacora/listar.html',
                         eventos=eventos,
                         total_eventos=total_eventos,
                         eventos_hoy=eventos_hoy,
                         usuarios_activos=usuarios_activos,
                         modulos=modulos,
                         acciones=acciones,
                         usuario_filtro=usuario_filtro,
                         modulo_filtro=modulo_filtro,
                         accion_filtro=accion_filtro,
                         fecha_desde=fecha_desde,
                         fecha_hasta=fecha_hasta)

@bitacora_bp.route('/exportar-pdf')
def exportar_pdf():
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    if user.role != 'admin':
        flash('No tienes permisos.', 'danger')
        return redirect(url_for('dashboard.dashboard'))
    
    # Obtener filtros
    usuario_filtro = request.args.get('usuario', '')
    modulo_filtro = request.args.get('modulo', '')
    fecha_desde = request.args.get('fecha_desde', '')
    fecha_hasta = request.args.get('fecha_hasta', '')
    
    query = Bitacora.query
    
    if usuario_filtro:
        query = query.filter(Bitacora.usuario.like(f'%{usuario_filtro}%'))
    
    if modulo_filtro:
        query = query.filter_by(modulo=modulo_filtro)
    
    if fecha_desde:
        query = query.filter(Bitacora.fecha >= datetime.strptime(fecha_desde, '%Y-%m-%d'))
    
    if fecha_hasta:
        fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d')
        fecha_hasta_dt = fecha_hasta_dt.replace(hour=23, minute=59, second=59)
        query = query.filter(Bitacora.fecha <= fecha_hasta_dt)
    
    eventos = query.order_by(Bitacora.fecha.desc()).limit(500).all()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    
    styles = getSampleStyleSheet()
    elementos = []
    
    titulo = Paragraph("<b>BITACORA DE AUDITORIA</b>", styles['Title'])
    subtitulo = Paragraph(f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')} por {session.get('username')}", styles['Normal'])
    elementos.extend([titulo, subtitulo, Spacer(1, 20)])
    
    data = [["Usuario", "Acción", "Módulo", "Descripción", "Fecha/Hora", "IP"]]
    
    for e in eventos:
        data.append([
            e.usuario or "—",
            e.accion or "—",
            e.modulo or "—",
            (e.descripcion[:30] + '...') if e.descripcion and len(e.descripcion) > 30 else (e.descripcion or "—"),
            e.fecha.strftime("%d/%m/%Y %H:%M:%S") if e.fecha else "—",
            e.ip_address or "—"
        ])
    
    tabla = Table(data, colWidths=[80, 60, 70, 150, 100, 80])
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    
    elementos.append(tabla)
    elementos.extend([
        Spacer(1, 20),
        Paragraph(f"<i>Total de eventos: {len(eventos)}</i>", styles['Normal']),
        Paragraph("<i>© Plataforma Butacors - Reporte de Auditoría</i>", styles['Normal'])
    ])
    
    doc.build(elementos)
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True, download_name=f'bitacora_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf', mimetype='application/pdf')

@bitacora_bp.route('/limpiar', methods=['POST'])
def limpiar():
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    if user.role != 'admin':
        flash('No tienes permisos.', 'danger')
        return redirect(url_for('dashboard.dashboard'))
    
    try:
        dias = int(request.form.get('dias', 90))
        fecha_limite = datetime.now() - timedelta(days=dias)
        
        eliminados = Bitacora.query.filter(Bitacora.fecha < fecha_limite).delete()
        db.session.commit()
        
        # Registrar la limpieza
        Bitacora.registrar(
            usuario=session.get('username'),
            accion='limpiar',
            modulo='bitacora',
            descripcion=f'Eliminados {eliminados} registros antiguos (>{dias} días)',
            ip=request.remote_addr
        )
        
        flash(f'{eliminados} registros antiguos eliminados.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('bitacora.listar'))
