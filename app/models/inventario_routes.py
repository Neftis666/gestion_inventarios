from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models.inventario_model import Producto, MovimientoInventario
from app import db
from datetime import datetime
from sqlalchemy import or_

inventario_bp = Blueprint('inventario', __name__, url_prefix='/inventario')


# ==============================
# 📋 LISTAR PRODUCTOS
# ==============================
@inventario_bp.route('/')
def listar_inventario():
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))

    search = request.args.get('search', '')
    estado = request.args.get('estado', '')
    categoria = request.args.get('categoria', '')

    query = Producto.query

    if search:
        query = query.filter(
            or_(
                Producto.codigo.like(f'%{search}%'),
                Producto.nombre.like(f'%{search}%'),
                Producto.descripcion.like(f'%{search}%'),
                Producto.referencia.like(f'%{search}%'),
                Producto.codigo_interno.like(f'%{search}%'),
                Producto.codigo_equipo.like(f'%{search}%'),
            )
        )

    if estado:
        query = query.filter_by(estado=estado)

    if categoria:
        query = query.filter_by(categoria=categoria)

    productos = query.order_by(Producto.nombre).all()

    total_productos = Producto.query.count()
    stock_bajo = Producto.query.filter(Producto.cantidad <= 10, Producto.cantidad > 5).count()
    stock_critico = Producto.query.filter(Producto.cantidad <= 5).count()

    categorias = db.session.query(Producto.categoria).distinct().all()
    categorias = [c[0] for c in categorias if c[0]]

    return render_template('inventario/listar.html',
                           productos=productos,
                           total_productos=total_productos,
                           stock_bajo=stock_bajo,
                           stock_critico=stock_critico,
                           categorias=categorias,
                           search=search,
                           estado_filtro=estado,
                           categoria_filtro=categoria)


# ==============================
# ➕ NUEVO PRODUCTO
# ==============================
@inventario_bp.route('/nuevo', methods=['GET', 'POST'])
def nuevo_producto():
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        try:
            codigo = request.form.get('codigo', '').strip()
            nombre = request.form.get('nombre', '').strip()
            referencia = request.form.get('referencia', '').strip()
            codigo_interno = request.form.get('codigo_interno', '').strip()
            codigo_equipo = request.form.get('codigo_equipo', '').strip()
            descripcion = request.form.get('descripcion', '').strip()
            serial = request.form.get('serial', '').strip()
            costo_unitario = float(request.form.get('costo_unitario', 0) or 0)
            cantidad = int(request.form.get('cantidad', 0) or 0)
            estado = request.form.get('estado', 'disponible')
            categoria = request.form.get('categoria', '').strip()

            if not all([codigo, nombre]):
                flash('Código y nombre son obligatorios.', 'danger')
                return redirect(url_for('inventario.nuevo_producto'))

            existe = Producto.query.filter_by(codigo=codigo).first()
            if existe:
                flash('El código de producto ya existe.', 'warning')
                return redirect(url_for('inventario.nuevo_producto'))

            nuevo = Producto(
                codigo=codigo,
                nombre=nombre,
                referencia=referencia or None,
                codigo_interno=codigo_interno or None,
                codigo_equipo=codigo_equipo or None,
                descripcion=descripcion or None,
                serial=serial or None,
                costo_unitario=costo_unitario,
                cantidad=cantidad,
                estado=estado,
                categoria=categoria or None
            )

            db.session.add(nuevo)
            db.session.flush()

            if cantidad > 0:
                movimiento = MovimientoInventario(
                    producto_id=nuevo.id,
                    tipo='entrada',
                    cantidad=cantidad,
                    cantidad_anterior=0,
                    cantidad_nueva=cantidad,
                    motivo='Ingreso inicial',
                    usuario=session.get('username')
                )
                db.session.add(movimiento)

            db.session.commit()
            flash(f'Producto {codigo} registrado exitosamente.', 'success')
            return redirect(url_for('inventario.listar_inventario'))

        except ValueError:
            flash('Error en los datos numéricos.', 'danger')
            return redirect(url_for('inventario.nuevo_producto'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar producto: {str(e)}', 'danger')
            return redirect(url_for('inventario.nuevo_producto'))

    return render_template('inventario/nuevo.html')


# ==============================
# ✏️ EDITAR PRODUCTO
# ==============================
@inventario_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_producto(id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))

    producto = Producto.query.get_or_404(id)

    if request.method == 'POST':
        try:
            cantidad_anterior = producto.cantidad

            producto.nombre = request.form.get('nombre', '').strip()
            producto.referencia = request.form.get('referencia', '').strip() or None
            producto.codigo_interno = request.form.get('codigo_interno', '').strip() or None
            producto.codigo_equipo = request.form.get('codigo_equipo', '').strip() or None
            producto.descripcion = request.form.get('descripcion', '').strip() or None
            producto.serial = request.form.get('serial', '').strip() or None
            producto.costo_unitario = float(request.form.get('costo_unitario', 0) or 0)
            producto.cantidad = int(request.form.get('cantidad', 0) or 0)
            producto.estado = request.form.get('estado', 'disponible')
            producto.categoria = request.form.get('categoria', '').strip() or None

            if cantidad_anterior != producto.cantidad:
                movimiento = MovimientoInventario(
                    producto_id=producto.id,
                    tipo='ajuste',
                    cantidad=abs(producto.cantidad - cantidad_anterior),
                    cantidad_anterior=cantidad_anterior,
                    cantidad_nueva=producto.cantidad,
                    motivo='Ajuste manual',
                    usuario=session.get('username')
                )
                db.session.add(movimiento)

            db.session.commit()
            flash('Producto actualizado exitosamente.', 'success')
            return redirect(url_for('inventario.listar_inventario'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'danger')

    return render_template('inventario/editar.html', producto=producto)


# ==============================
# 👁️ VER DETALLE
# ==============================
@inventario_bp.route('/detalle/<int:id>')
def detalle_producto(id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))

    producto = Producto.query.get_or_404(id)
    movimientos = MovimientoInventario.query.filter_by(producto_id=id).order_by(MovimientoInventario.fecha.desc()).limit(20).all()

    return render_template('inventario/detalle.html', producto=producto, movimientos=movimientos)


# ==============================
# 🗑️ ELIMINAR PRODUCTO
# ==============================
@inventario_bp.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_producto(id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))

    try:
        producto = Producto.query.get_or_404(id)
        codigo = producto.codigo
        db.session.delete(producto)
        db.session.commit()
        flash(f'Producto {codigo} eliminado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar: {str(e)}', 'danger')

    return redirect(url_for('inventario.listar_inventario'))


# ==============================
# 📊 HISTORIAL DE MOVIMIENTOS
# ==============================
@inventario_bp.route('/movimientos')
def historial_movimientos():
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero.', 'warning')
        return redirect(url_for('auth.login'))

    movimientos = MovimientoInventario.query.order_by(MovimientoInventario.fecha.desc()).limit(100).all()

    return render_template('inventario/movimientos.html', movimientos=movimientos)
