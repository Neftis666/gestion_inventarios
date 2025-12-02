from flask import Blueprint, request, jsonify, render_template, session
from app import db
from app.models.product_model import Product, InventoryMovement, BarcodeLabel
from app.utils.barcode_generator import BarcodeGenerator
from datetime import datetime
from sqlalchemy import or_, func

barcode_bp = Blueprint('barcode', __name__, url_prefix='/barcode')

# ============================================
# INTERFAZ WEB
# ============================================

@barcode_bp.route('/scanner')
def scanner_interface():
    """Interfaz web para gestión de códigos de barras"""
    return render_template('barcode_scanner.html')


# ============================================
# API: BÚSQUEDA Y VERIFICACIÓN
# ============================================

@barcode_bp.route('/api/scan', methods=['POST'])
def scan_barcode():
    """
    Busca un producto por código de barras escaneado.
    Compatible con lectores USB y escáneres de cámara.
    """
    try:
        data = request.get_json()
        barcode = data.get('barcode', '').strip()
        
        if not barcode:
            return jsonify({
                'success': False,
                'message': 'Código de barras no proporcionado'
            }), 400
        
        # Buscar producto por código de barras
        product = Product.query.filter_by(barcode=barcode, active=True).first()
        
        if not product:
            return jsonify({
                'success': False,
                'message': f'Producto no encontrado con código: {barcode}',
                'barcode': barcode,
                'suggestion': 'create_product'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Producto encontrado',
            'product': product.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al buscar producto: {str(e)}'
        }), 500


@barcode_bp.route('/api/verify/<barcode>', methods=['GET'])
def verify_barcode(barcode):
    """Verifica si un código de barras ya existe en el sistema"""
    try:
        # Validar formato del código
        validation = BarcodeGenerator.validate_barcode(barcode)
        
        # Buscar en base de datos
        exists = Product.query.filter_by(barcode=barcode).first() is not None
        
        return jsonify({
            'success': True,
            'exists': exists,
            'barcode': barcode,
            'validation': validation
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al verificar código: {str(e)}'
        }), 500


@barcode_bp.route('/api/search', methods=['GET'])
def search_products():
    """
    Búsqueda avanzada de productos.
    Soporta búsqueda por nombre, código, SKU, categoría.
    """
    try:
        query = request.args.get('q', '').strip()
        category = request.args.get('category', '').strip()
        low_stock = request.args.get('low_stock', 'false').lower() == 'true'
        
        # Construir consulta base
        products_query = Product.query.filter_by(active=True)
        
        # Filtrar por búsqueda de texto
        if query:
            products_query = products_query.filter(
                or_(
                    Product.name.ilike(f'%{query}%'),
                    Product.barcode.ilike(f'%{query}%'),
                    Product.sku.ilike(f'%{query}%'),
                    Product.description.ilike(f'%{query}%')
                )
            )
        
        # Filtrar por categoría
        if category:
            products_query = products_query.filter_by(category=category)
        
        # Filtrar por stock bajo
        if low_stock:
            products_query = products_query.filter(Product.stock < Product.min_stock)
        
        # Obtener resultados
        products = products_query.order_by(Product.name).all()
        
        return jsonify({
            'success': True,
            'count': len(products),
            'products': [p.to_dict() for p in products]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error en búsqueda: {str(e)}'
        }), 500


# ============================================
# API: GESTIÓN DE PRODUCTOS
# ============================================

@barcode_bp.route('/api/product/create', methods=['POST'])
def create_product_with_barcode():
    """Crea un nuevo producto con código de barras generado automáticamente"""
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['name', 'price', 'cost']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'El campo {field} es requerido'
                }), 400
        
        # Verificar código de barras personalizado si se proporciona
        custom_barcode = data.get('barcode', '').strip()
        if custom_barcode:
            # Validar formato
            validation = BarcodeGenerator.validate_barcode(custom_barcode)
            if not validation['valid']:
                return jsonify({
                    'success': False,
                    'message': f'Código de barras inválido: {validation.get("error")}'
                }), 400
            
            # Verificar que no exista
            if Product.query.filter_by(barcode=custom_barcode).first():
                return jsonify({
                    'success': False,
                    'message': f'El código de barras {custom_barcode} ya existe'
                }), 400
        
        # Verificar SKU único si se proporciona
        sku = data.get('sku', '').strip()
        if sku and Product.query.filter_by(sku=sku).first():
            return jsonify({
                'success': False,
                'message': f'El SKU {sku} ya existe'
            }), 400
        
        # Obtener usuario actual (si hay sesión)
        current_user = session.get('username', 'system')
        
        # Crear producto
        product = Product(
            name=data.get('name'),
            description=data.get('description', ''),
            barcode=custom_barcode or None,  # Si es None, se genera automático
            sku=sku or None,
            price=float(data.get('price', 0)),
            cost=float(data.get('cost', 0)),
            stock=int(data.get('stock', 0)),
            min_stock=int(data.get('min_stock', 10)),
            category=data.get('category', ''),
            supplier=data.get('supplier', ''),
            created_by=current_user
        )
        
        db.session.add(product)
        db.session.commit()
        
        # Generar imágenes de códigos
        barcode_img = BarcodeGenerator.generate_barcode_image(product.barcode)
        qr_img = BarcodeGenerator.generate_qr_image(product.qr_code)
        
        # Registrar movimiento inicial si hay stock
        if product.stock > 0:
            movement = InventoryMovement(
                product_id=product.id,
                type='entrada',
                quantity=product.stock,
                previous_stock=0,
                new_stock=product.stock,
                reason='Stock inicial',
                created_by=current_user
            )
            db.session.add(movement)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Producto creado exitosamente',
            'product': product.to_dict(),
            'barcode_image': barcode_img.get('image') if barcode_img['success'] else None,
            'qr_image': qr_img.get('image') if qr_img['success'] else None
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error al crear producto: {str(e)}'
        }), 500


@barcode_bp.route('/api/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Obtiene información detallada de un producto"""
    try:
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({
                'success': False,
                'message': 'Producto no encontrado'
            }), 404
        
        # Obtener últimos movimientos
        movements = InventoryMovement.query.filter_by(product_id=product_id)\
            .order_by(InventoryMovement.created_at.desc())\
            .limit(10).all()
        
        return jsonify({
            'success': True,
            'product': product.to_dict(),
            'recent_movements': [m.to_dict() for m in movements]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al obtener producto: {str(e)}'
        }), 500


@barcode_bp.route('/api/product/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Actualiza información de un producto"""
    try:
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({
                'success': False,
                'message': 'Producto no encontrado'
            }), 404
        
        data = request.get_json()
        
        # Actualizar campos permitidos
        updatable_fields = ['name', 'description', 'price', 'cost', 
                           'min_stock', 'category', 'supplier', 'active']
        
        for field in updatable_fields:
            if field in data:
                setattr(product, field, data[field])
        
        product.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Producto actualizado exitosamente',
            'product': product.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error al actualizar producto: {str(e)}'
        }), 500


@barcode_bp.route('/api/products', methods=['GET'])
def list_products():
    """Lista todos los productos activos con sus códigos"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        products = Product.query.filter_by(active=True)\
            .order_by(Product.name)\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'count': products.total,
            'pages': products.pages,
            'current_page': products.page,
            'products': [p.to_dict() for p in products.items]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al listar productos: {str(e)}'
        }), 500


# ============================================
# API: MOVIMIENTOS DE INVENTARIO
# ============================================

@barcode_bp.route('/api/inventory/entry', methods=['POST'])
def inventory_entry():
    """Registra una entrada de inventario mediante escaneo"""
    try:
        data = request.get_json()
        barcode = data.get('barcode', '').strip()
        quantity = int(data.get('quantity', 1))
        reason = data.get('reason', 'Entrada por escaneo')
        reference = data.get('reference', '')
        
        current_user = session.get('username', 'system')
        
        if not barcode:
            return jsonify({
                'success': False,
                'message': 'Código de barras no proporcionado'
            }), 400
        
        if quantity <= 0:
            return jsonify({
                'success': False,
                'message': 'La cantidad debe ser mayor a 0'
            }), 400
        
        # Buscar producto
        product = Product.query.filter_by(barcode=barcode, active=True).first()
        
        if not product:
            return jsonify({
                'success': False,
                'message': f'Producto no encontrado con código: {barcode}'
            }), 404
        
        # Guardar stock anterior
        previous_stock = product.stock
        
        # Actualizar stock
        product.stock += quantity
        product.updated_at = datetime.utcnow()
        
        # Registrar movimiento
        movement = InventoryMovement(
            product_id=product.id,
            type='entrada',
            quantity=quantity,
            previous_stock=previous_stock,
            new_stock=product.stock,
            reason=reason,
            reference=reference,
            barcode_scanned=barcode,
            created_by=current_user
        )
        
        db.session.add(movement)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Entrada registrada: {quantity} unidades',
            'product': product.to_dict(),
            'movement': movement.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error al registrar entrada: {str(e)}'
        }), 500


@barcode_bp.route('/api/inventory/exit', methods=['POST'])
def inventory_exit():
    """Registra una salida de inventario mediante escaneo"""
    try:
        data = request.get_json()
        barcode = data.get('barcode', '').strip()
        quantity = int(data.get('quantity', 1))
        reason = data.get('reason', 'Salida por escaneo')
        reference = data.get('reference', '')
        
        current_user = session.get('username', 'system')
        
        if not barcode:
            return jsonify({
                'success': False,
                'message': 'Código de barras no proporcionado'
            }), 400
        
        if quantity <= 0:
            return jsonify({
                'success': False,
                'message': 'La cantidad debe ser mayor a 0'
            }), 400
        
        # Buscar producto
        product = Product.query.filter_by(barcode=barcode, active=True).first()
        
        if not product:
            return jsonify({
                'success': False,
                'message': f'Producto no encontrado con código: {barcode}'
            }), 404
        
        # Verificar stock disponible
        if product.stock < quantity:
            return jsonify({
                'success': False,
                'message': f'Stock insuficiente. Disponible: {product.stock}, Solicitado: {quantity}'
            }), 400
        
        # Guardar stock anterior
        previous_stock = product.stock
        
        # Actualizar stock
        product.stock -= quantity
        product.updated_at = datetime.utcnow()
        
        # Registrar movimiento
        movement = InventoryMovement(
            product_id=product.id,
            type='salida',
            quantity=quantity,
            previous_stock=previous_stock,
            new_stock=product.stock,
            reason=reason,
            reference=reference,
            barcode_scanned=barcode,
            created_by=current_user
        )
        
        db.session.add(movement)
        db.session.commit()
        
        # Alerta de stock bajo
        alert = None
        if product.is_low_stock():
            alert = f'⚠️ Stock bajo: {product.stock} unidades (mínimo: {product.min_stock})'
        
        return jsonify({
            'success': True,
            'message': f'Salida registrada: {quantity} unidades',
            'product': product.to_dict(),
            'movement': movement.to_dict(),
            'alert': alert
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error al registrar salida: {str(e)}'
        }), 500


@barcode_bp.route('/api/inventory/movements/<int:product_id>', methods=['GET'])
def get_product_movements(product_id):
    """Obtiene historial de movimientos de un producto"""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        movements = InventoryMovement.query.filter_by(product_id=product_id)\
            .order_by(InventoryMovement.created_at.desc())\
            .limit(limit).all()
        
        return jsonify({
            'success': True,
            'count': len(movements),
            'movements': [m.to_dict() for m in movements]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al obtener movimientos: {str(e)}'
        }), 500


# ============================================
# API: GENERACIÓN DE CÓDIGOS Y ETIQUETAS
# ============================================

@barcode_bp.route('/api/generate/barcode', methods=['POST'])
def generate_barcode():
    """Genera un código de barras para un código dado"""
    try:
        data = request.get_json()
        code = data.get('code', '').strip()
        barcode_type = data.get('type', 'ean13')
        
        if not code:
            return jsonify({
                'success': False,
                'message': 'Código no proporcionado'
            }), 400
        
        result = BarcodeGenerator.generate_barcode_image(code, barcode_type)
        
        return jsonify(result), 200 if result['success'] else 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al generar código de barras: {str(e)}'
        }), 500


@barcode_bp.route('/api/generate/qr', methods=['POST'])
def generate_qr():
    """Genera un código QR para datos dados"""
    try:
        data = request.get_json()
        qr_data = data.get('data', '').strip()
        size = data.get('size', 10)
        error_correction = data.get('error_correction', 'M')
        
        if not qr_data:
            return jsonify({
                'success': False,
                'message': 'Datos no proporcionados'
            }), 400
        
        result = BarcodeGenerator.generate_qr_image(qr_data, size, error_correction)
        
        return jsonify(result), 200 if result['success'] else 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al generar código QR: {str(e)}'
        }), 500


@barcode_bp.route('/api/generate/label/<int:product_id>', methods=['GET'])
def generate_product_label(product_id):
    """Genera una etiqueta completa para un producto"""
    try:
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({
                'success': False,
                'message': 'Producto no encontrado'
            }), 404
        
        include_qr = request.args.get('include_qr', 'false').lower() == 'true'
        
        result = BarcodeGenerator.generate_product_label(
            product.to_dict(), 
            include_qr=include_qr
        )
        
        # Registrar etiqueta generada
        if result['success']:
            label_record = BarcodeLabel(
                product_id=product.id,
                label_type='complete',
                format='png',
                quantity_printed=1,
                created_by=session.get('username', 'system')
            )
            db.session.add(label_record)
            db.session.commit()
        
        return jsonify(result), 200 if result['success'] else 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al generar etiqueta: {str(e)}'
        }), 500


@barcode_bp.route('/api/generate/labels/batch', methods=['POST'])
def generate_batch_labels():
    """Genera etiquetas en lote para múltiples productos"""
    try:
        data = request.get_json()
        product_ids = data.get('product_ids', [])
        include_qr = data.get('include_qr', False)
        
        if not product_ids:
            return jsonify({
                'success': False,
                'message': 'No se proporcionaron IDs de productos'
            }), 400
        
        products = Product.query.filter(Product.id.in_(product_ids)).all()
        products_data = [p.to_dict() for p in products]
        
        result = BarcodeGenerator.generate_batch_labels(products_data, include_qr)
        
        # Registrar etiquetas generadas
        current_user = session.get('username', 'system')
        for product in products:
            label_record = BarcodeLabel(
                product_id=product.id,
                label_type='batch',
                format='png',
                quantity_printed=1,
                created_by=current_user
            )
            db.session.add(label_record)
        db.session.commit()
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al generar etiquetas: {str(e)}'
        }), 500


# ============================================
# API: ESTADÍSTICAS Y REPORTES
# ============================================

@barcode_bp.route('/api/stats/general', methods=['GET'])
def get_general_stats():
    """Obtiene estadísticas generales del sistema de códigos de barras"""
    try:
        total_products = Product.query.filter_by(active=True).count()
        low_stock_products = Product.query.filter(
            Product.active == True,
            Product.stock < Product.min_stock
        ).count()
        out_of_stock = Product.query.filter(
            Product.active == True,
            Product.stock == 0
        ).count()
        
        total_inventory_value = db.session.query(
            func.sum(Product.stock * Product.cost)
        ).filter_by(active=True).scalar() or 0
        
        recent_movements = InventoryMovement.query\
            .order_by(InventoryMovement.created_at.desc())\
            .limit(10).all()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_products': total_products,
                'low_stock_products': low_stock_products,
                'out_of_stock': out_of_stock,
                'total_inventory_value': float(total_inventory_value),
            },
            'recent_movements': [m.to_dict() for m in recent_movements]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al obtener estadísticas: {str(e)}'
        }), 500
