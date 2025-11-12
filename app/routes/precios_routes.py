from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from app.models.precio_cliente_model import PrecioCliente, HistorialPrecioCliente
from app.models.venta_model import Cliente
from app.models.inventario_model import Producto
from app import db
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

precios_bp = Blueprint('precios', __name__, url_prefix='/precios')

@precios_bp.route('/')
def listar_precios():
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))
    
    cliente_id = request.args.get('cliente_id', '')
    producto_id = request.args.get('producto_id', '')
    
    query = PrecioCliente.query.filter_by(activo=True)
    
    if cliente_id:
        query = query.filter_by(cliente_id=int(cliente_id))
    
    if producto_id:
        query = query.filter_by(producto_id=int(producto_id))
    
    precios = query.order_by(PrecioCliente.cliente_id, PrecioCliente.fecha_actualizacion.desc()).all()
    
    clientes = Cliente.query.order_by(Cliente.nombre).all()
    productos = Producto.query.order_by(Producto.nombre).all()
    
    total_precios = PrecioCliente.query.filter_by(activo=True).count()
    clientes_con_precios = db.session.query(PrecioCliente.cliente_id).distinct().count()
    
    return render_template('precios/listar.html',
                         precios=precios,
                         clientes=clientes,
                         productos=productos,
                         total_precios=total_precios,
                         clientes_con_precios=clientes_con_precios,
                         cliente_filtro=cliente_id,
                         producto_filtro=producto_id)

@precios_bp.route('/asignar', methods=['GET', 'POST'])
def asignar_precio():
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        try:
            cliente_id = int(request.form.get('cliente_id'))
            producto_id = int(request.form.get('producto_id'))
            precio_base = float(request.form.get('precio_base'))
            iva_porcentaje = float(request.form.get('iva', 19))
            descuento = float(request.form.get('descuento', 0))
            
            precio_con_iva = precio_base * (1 + iva_porcentaje / 100)
            precio_final = precio_con_iva * (1 - descuento / 100)
            
            # Verificar si ya existe
            existe = PrecioCliente.query.filter_by(
                cliente_id=cliente_id,
                producto_id=producto_id,
                activo=True
            ).first()
            
            if existe:
                # Guardar en historial
                historial = HistorialPrecioCliente(
                    precio_cliente_id=existe.id,
                    precio_anterior=existe.precio_con_iva,
                    precio_nuevo=precio_final,
                    modificado_por=session.get('username'),
                    motivo='Actualización de precio'
                )
                db.session.add(historial)
                
                # Actualizar precio
                existe.precio_base = precio_base
                existe.precio_con_iva = precio_final
                existe.descuento_porcentaje = descuento
                existe.actualizado_por = session.get('username')
                existe.fecha_actualizacion = datetime.utcnow()
                
                mensaje = 'Precio actualizado exitosamente.'
            else:
                # Crear nuevo precio
                nuevo_precio = PrecioCliente(
                    cliente_id=cliente_id,
                    producto_id=producto_id,
                    precio_base=precio_base,
                    precio_con_iva=precio_final,
                    descuento_porcentaje=descuento,
                    actualizado_por=session.get('username')
                )
                db.session.add(nuevo_precio)
                mensaje = 'Precio asignado exitosamente.'
            
            db.session.commit()
            flash(mensaje, 'success')
            return redirect(url_for('precios.listar_precios'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al asignar precio: {str(e)}', 'danger')
    
    clientes = Cliente.query.order_by(Cliente.nombre).all()
    productos = Producto.query.order_by(Producto.nombre).all()
    
    return render_template('precios/asignar.html', clientes=clientes, productos=productos)

@precios_bp.route('/cliente/<int:cliente_id>')
def precios_por_cliente(cliente_id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))
    
    cliente = Cliente.query.get_or_404(cliente_id)
    precios = PrecioCliente.query.filter_by(cliente_id=cliente_id, activo=True).all()
    
    return render_template('precios/por_cliente.html', cliente=cliente, precios=precios)

@precios_bp.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_precio(id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))
    
    try:
        precio = PrecioCliente.query.get_or_404(id)
        precio.activo = False
        db.session.commit()
        
        flash('Precio desactivado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('precios.listar_precios'))

@precios_bp.route('/historial/<int:precio_id>')
def historial_precio(precio_id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))
    
    precio = PrecioCliente.query.get_or_404(precio_id)
    historial = HistorialPrecioCliente.query.filter_by(precio_cliente_id=precio_id).order_by(
        HistorialPrecioCliente.fecha_modificacion.desc()
    ).all()
    
    return render_template('precios/historial.html', precio=precio, historial=historial)

@precios_bp.route('/replicar/<int:producto_id>', methods=['POST'])
def replicar_precio(producto_id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))
    
    try:
        nuevo_precio = float(request.form.get('nuevo_precio'))
        aplicar_a = request.form.get('aplicar_a', 'todos')
        
        if aplicar_a == 'todos':
            precios = PrecioCliente.query.filter_by(producto_id=producto_id, activo=True).all()
            for precio in precios:
                precio.precio_base = nuevo_precio
                precio.precio_con_iva = nuevo_precio * 1.19
                precio.actualizado_por = session.get('username')
            
            db.session.commit()
            flash(f'Precio replicado a {len(precios)} clientes.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('precios.listar_precios'))

@precios_bp.route('/exportar-pdf')
def exportar_pdf():
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))
    
    precios = PrecioCliente.query.filter_by(activo=True).order_by(PrecioCliente.cliente_id).all()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    
    styles = getSampleStyleSheet()
    elementos = []
    
    titulo = Paragraph("<b>LISTA DE PRECIOS POR CLIENTE</b>", styles['Title'])
    elementos.extend([titulo, Spacer(1, 20)])
    
    data = [["Cliente", "Producto", "Precio Base", "Precio + IVA", "Descuento", "Precio Final"]]
    
    for p in precios:
        data.append([
            p.cliente.nombre,
            p.producto.nombre,
            f"${p.precio_base:,.2f}",
            f"${p.precio_con_iva:,.2f}",
            f"{p.descuento_porcentaje}%",
            f"${p.precio_con_iva * (1 - p.descuento_porcentaje/100):,.2f}"
        ])
    
    tabla = Table(data)
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    
    elementos.append(tabla)
    doc.build(elementos)
    
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f'precios_{datetime.now().strftime("%Y%m%d")}.pdf', mimetype='application/pdf')