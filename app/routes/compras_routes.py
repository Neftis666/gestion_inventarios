from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from werkzeug.utils import secure_filename
from app.models.compra_model import Compra
from app import db
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import os

compras_bp = Blueprint('compras', __name__, url_prefix='/compras')

# Configuración de carga de archivos
UPLOAD_FOLDER = 'app/static/uploads/facturas'
ALLOWED_EXTENSIONS = {'pdf', 'xml', 'txt'}

# Crear carpeta si no existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==============================
# 📋 LISTAR COMPRAS
# ==============================
@compras_bp.route('/')
def listar_compras():
    # Verificar sesión
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))
    
    # Filtros
    search = request.args.get('search', '')
    tipo_compra = request.args.get('tipo_compra', '')
    fecha_desde = request.args.get('fecha_desde', '')
    fecha_hasta = request.args.get('fecha_hasta', '')
    
    # Query base
    query = Compra.query
    
    # Aplicar filtros
    if search:
        query = query.filter(
            (Compra.proveedor.like(f'%{search}%')) | 
            (Compra.numero_factura.like(f'%{search}%')) |
            (Compra.producto.like(f'%{search}%'))
        )
    
    if tipo_compra:
        query = query.filter_by(tipo_compra=tipo_compra)
    
    if fecha_desde:
        query = query.filter(Compra.fecha >= datetime.strptime(fecha_desde, '%Y-%m-%d'))
    
    if fecha_hasta:
        query = query.filter(Compra.fecha <= datetime.strptime(fecha_hasta, '%Y-%m-%d'))
    
    # Ordenar por fecha descendente
    compras = query.order_by(Compra.fecha.desc()).all()
    
    # Calcular totales
    total_compras = sum(c.total for c in compras)
    
    return render_template('compras/listar.html', 
                         compras=compras, 
                         total_compras=total_compras,
                         search=search,
                         tipo_compra=tipo_compra,
                         fecha_desde=fecha_desde,
                         fecha_hasta=fecha_hasta)


# ==============================
# ➕ NUEVA COMPRA
# ==============================
@compras_bp.route('/nueva', methods=['GET', 'POST'])
def nueva_compra():
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            proveedor = request.form.get('proveedor')
            numero_factura = request.form.get('numero_factura')
            tipo_compra = request.form.get('tipo_compra')
            producto = request.form.get('producto')
            cantidad = int(request.form.get('cantidad'))
            precio_unitario = float(request.form.get('precio_unitario'))
            iva_porcentaje = float(request.form.get('iva', 0))
            
            # Validar campos obligatorios
            if not all([proveedor, numero_factura, tipo_compra, producto, cantidad, precio_unitario]):
                flash('Todos los campos son obligatorios.', 'danger')
                return redirect(url_for('compras.nueva_compra'))
            
            # Verificar si la factura ya existe
            existe = Compra.query.filter_by(numero_factura=numero_factura).first()
            if existe:
                flash('El número de factura ya existe.', 'warning')
                return redirect(url_for('compras.nueva_compra'))
            
            # Cálculos automáticos
            subtotal = cantidad * precio_unitario
            iva = subtotal * (iva_porcentaje / 100)
            total = subtotal + iva
            
            # Procesar archivo adjunto
            documento_path = None
            if 'documento' in request.files:
                file = request.files['documento']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"{numero_factura}_{file.filename}")
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(file_path)
                    documento_path = filename
            
            # Crear nueva compra
            nueva_compra = Compra(
                proveedor=proveedor,
                numero_factura=numero_factura,
                tipo_compra=tipo_compra,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                iva=iva,
                total=total,
                documento=documento_path
            )
            
            db.session.add(nueva_compra)
            db.session.commit()
            
            flash(f'Compra registrada exitosamente. Total: ${total:,.2f}', 'success')
            return redirect(url_for('compras.listar_compras'))
            
        except ValueError as e:
            flash('Error en los datos numéricos. Verifica cantidad y precios.', 'danger')
            return redirect(url_for('compras.nueva_compra'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar la compra: {str(e)}', 'danger')
            return redirect(url_for('compras.nueva_compra'))
    
    return render_template('compras/nueva.html')


# ==============================
# ✏️ EDITAR COMPRA
# ==============================
@compras_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_compra(id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))
    
    compra = Compra.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Actualizar datos
            compra.proveedor = request.form.get('proveedor')
            compra.tipo_compra = request.form.get('tipo_compra')
            compra.producto = request.form.get('producto')
            compra.cantidad = int(request.form.get('cantidad'))
            compra.precio_unitario = float(request.form.get('precio_unitario'))
            iva_porcentaje = float(request.form.get('iva', 0))
            
            # Recalcular totales
            subtotal = compra.cantidad * compra.precio_unitario
            compra.iva = subtotal * (iva_porcentaje / 100)
            compra.total = subtotal + compra.iva
            
            # Actualizar documento si se cargó uno nuevo
            if 'documento' in request.files:
                file = request.files['documento']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"{compra.numero_factura}_{file.filename}")
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(file_path)
                    compra.documento = filename
            
            db.session.commit()
            flash('Compra actualizada exitosamente.', 'success')
            return redirect(url_for('compras.listar_compras'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'danger')
    
    return render_template('compras/editar.html', compra=compra)


# ==============================
# 🗑️ ELIMINAR COMPRA
# ==============================
@compras_bp.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_compra(id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))
    
    try:
        compra = Compra.query.get_or_404(id)
        
        # Eliminar archivo asociado si existe
        if compra.documento:
            file_path = os.path.join(UPLOAD_FOLDER, compra.documento)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        db.session.delete(compra)
        db.session.commit()
        
        flash('Compra eliminada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar: {str(e)}', 'danger')
    
    return redirect(url_for('compras.listar_compras'))


# ==============================
# 📄 VER DETALLE DE COMPRA
# ==============================
@compras_bp.route('/detalle/<int:id>')
def detalle_compra(id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))
    
    compra = Compra.query.get_or_404(id)
    
    # Calcular subtotal para mostrar
    subtotal = compra.total - compra.iva
    
    return render_template('compras/detalle.html', compra=compra, subtotal=subtotal)


# ==============================
# 📥 DESCARGAR FACTURA PDF
# ==============================
@compras_bp.route('/generar-pdf/<int:id>')
def generar_pdf(id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))
    
    compra = Compra.query.get_or_404(id)
    
    # Crear PDF en memoria
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Encabezado
    p.setFont("Helvetica-Bold", 20)
    p.drawString(1*inch, height - 1*inch, "COMPROBANTE DE COMPRA")
    
    p.setFont("Helvetica", 12)
    p.drawString(1*inch, height - 1.5*inch, f"Factura N°: {compra.numero_factura}")
    p.drawString(1*inch, height - 1.8*inch, f"Fecha: {compra.fecha.strftime('%d/%m/%Y')}")
    p.drawString(1*inch, height - 2.1*inch, f"Proveedor: {compra.proveedor}")
    p.drawString(1*inch, height - 2.4*inch, f"Tipo: {compra.tipo_compra}")
    
    # Línea separadora
    p.line(1*inch, height - 2.7*inch, width - 1*inch, height - 2.7*inch)
    
    # Detalles del producto
    p.setFont("Helvetica-Bold", 12)
    p.drawString(1*inch, height - 3.2*inch, "DETALLE DE PRODUCTOS")
    
    p.setFont("Helvetica", 11)
    p.drawString(1*inch, height - 3.6*inch, f"Producto: {compra.producto}")
    p.drawString(1*inch, height - 3.9*inch, f"Cantidad: {compra.cantidad}")
    p.drawString(1*inch, height - 4.2*inch, f"Precio Unitario: ${compra.precio_unitario:,.2f}")
    
    # Totales
    subtotal = compra.total - compra.iva
    p.line(1*inch, height - 4.5*inch, width - 1*inch, height - 4.5*inch)
    
    p.setFont("Helvetica", 11)
    p.drawString(1*inch, height - 5*inch, f"Subtotal: ${subtotal:,.2f}")
    p.drawString(1*inch, height - 5.3*inch, f"IVA: ${compra.iva:,.2f}")
    
    p.setFont("Helvetica-Bold", 14)
    p.drawString(1*inch, height - 5.7*inch, f"TOTAL: ${compra.total:,.2f}")
    
    # Pie de página
    p.setFont("Helvetica-Oblique", 9)
    p.drawString(1*inch, 1*inch, f"Generado por: {session.get('username', 'Sistema')}")
    p.drawString(1*inch, 0.7*inch, f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f'compra_{compra.numero_factura}.pdf', mimetype='application/pdf')


# ==============================
# 📊 REPORTE DE COMPRAS
# ==============================
@compras_bp.route('/reporte')
def reporte_compras():
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))
    
    # Estadísticas generales
    total_compras = Compra.query.count()
    suma_total = db.session.query(db.func.sum(Compra.total)).scalar() or 0
    
    # Compras por tipo
    compras_nacional = Compra.query.filter_by(tipo_compra='Nacional').count()
    compras_internacional = Compra.query.filter_by(tipo_compra='Internacional').count()
    
    # Proveedores con más compras
    proveedores = db.session.query(
        Compra.proveedor, 
        db.func.count(Compra.id).label('total'),
        db.func.sum(Compra.total).label('monto')
    ).group_by(Compra.proveedor).order_by(db.desc('total')).limit(10).all()
    
    return render_template('compras/reporte.html',
                         total_compras=total_compras,
                         suma_total=suma_total,
                         compras_nacional=compras_nacional,
                         compras_internacional=compras_internacional,
                         proveedores=proveedores)