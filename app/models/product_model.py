from app import db
from datetime import datetime
import random

class Product(db.Model):
    """
    Modelo de Producto con soporte para códigos de barras y QR.
    Integrado con el sistema de inventarios existente.
    """
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    barcode = db.Column(db.String(100), unique=True, nullable=False, index=True)
    qr_code = db.Column(db.String(200), unique=True)
    sku = db.Column(db.String(100), unique=True, index=True)
    
    # Información comercial
    price = db.Column(db.Float, nullable=False, default=0.0)
    cost = db.Column(db.Float, nullable=False, default=0.0)
    stock = db.Column(db.Integer, nullable=False, default=0)
    min_stock = db.Column(db.Integer, default=10)
    
    # Categorización
    category = db.Column(db.String(100))
    supplier = db.Column(db.String(200))
    
    # Estado
    active = db.Column(db.Boolean, default=True)
    
    # Campos de auditoría
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(100))
    
    # Relación con movimientos de inventario
    movements = db.relationship('InventoryMovement', backref='product', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super(Product, self).__init__(**kwargs)
        if not self.barcode:
            self.barcode = self.generate_barcode()
        if not self.qr_code:
            self.qr_code = self.generate_qr_data()
    
    @staticmethod
    def generate_barcode():
        """
        Genera un código de barras EAN-13 único y válido.
        Incluye dígito de verificación según el algoritmo EAN-13.
        """
        # Generar 12 dígitos aleatorios
        code = ''.join([str(random.randint(0, 9)) for _ in range(12)])
        
        # Calcular dígito de verificación
        odd_sum = sum(int(code[i]) for i in range(0, 12, 2))
        even_sum = sum(int(code[i]) for i in range(1, 12, 2))
        total = odd_sum + (even_sum * 3)
        check_digit = (10 - (total % 10)) % 10
        
        return code + str(check_digit)
    
    def generate_qr_data(self):
        """
        Genera datos únicos para código QR.
        Incluye código de barras y timestamp para garantizar unicidad.
        """
        return f"PROD-{self.barcode}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    def update_stock(self, quantity, movement_type='manual'):
        """
        Actualiza el stock del producto y registra el movimiento.
        
        Args:
            quantity: Cantidad a agregar (positivo) o restar (negativo)
            movement_type: Tipo de movimiento ('entrada', 'salida', 'ajuste')
        """
        old_stock = self.stock
        self.stock += quantity
        
        # Registrar movimiento
        movement = InventoryMovement(
            product_id=self.id,
            type=movement_type,
            quantity=abs(quantity),
            previous_stock=old_stock,
            new_stock=self.stock,
            created_at=datetime.utcnow()
        )
        db.session.add(movement)
        
    def is_low_stock(self):
        """Verifica si el stock está por debajo del mínimo"""
        return self.stock < self.min_stock
    
    def to_dict(self):
        """Convierte el producto a diccionario para JSON"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'barcode': self.barcode,
            'qr_code': self.qr_code,
            'sku': self.sku,
            'price': float(self.price),
            'cost': float(self.cost),
            'stock': self.stock,
            'min_stock': self.min_stock,
            'category': self.category,
            'supplier': self.supplier,
            'active': self.active,
            'is_low_stock': self.is_low_stock(),
            'profit_margin': self.calculate_profit_margin(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    def calculate_profit_margin(self):
        """Calcula el margen de utilidad del producto"""
        if self.price > 0 and self.cost > 0:
            return round(((self.price - self.cost) / self.price) * 100, 2)
        return 0.0
    
    def __repr__(self):
        return f'<Product {self.name} - {self.barcode}>'


class InventoryMovement(db.Model):
    """
    Modelo para registrar movimientos de inventario.
    Trazabilidad completa de entradas y salidas.
    """
    __tablename__ = 'inventory_movements'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    # Tipo de movimiento
    type = db.Column(db.String(20), nullable=False)  # 'entrada', 'salida', 'ajuste'
    quantity = db.Column(db.Integer, nullable=False)
    
    # Stocks antes y después del movimiento
    previous_stock = db.Column(db.Integer)
    new_stock = db.Column(db.Integer)
    
    # Información adicional
    reason = db.Column(db.String(200))
    reference = db.Column(db.String(100))  # Número de orden, factura, etc.
    barcode_scanned = db.Column(db.String(100))
    notes = db.Column(db.Text)
    
    # Auditoría
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(100))
    
    def to_dict(self):
        """Convierte el movimiento a diccionario para JSON"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'type': self.type,
            'quantity': self.quantity,
            'previous_stock': self.previous_stock,
            'new_stock': self.new_stock,
            'reason': self.reason,
            'reference': self.reference,
            'barcode_scanned': self.barcode_scanned,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by
        }
    
    def __repr__(self):
        return f'<Movement {self.type} - Product {self.product_id} - Qty {self.quantity}>'


class BarcodeLabel(db.Model):
    """
    Modelo para almacenar etiquetas generadas.
    Historial de etiquetas impresas.
    """
    __tablename__ = 'barcode_labels'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    label_type = db.Column(db.String(50))  # 'barcode', 'qr', 'complete'
    format = db.Column(db.String(50))  # 'png', 'pdf', 'svg'
    quantity_printed = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(100))
    
    # Relación con producto
    product = db.relationship('Product', backref='labels')
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'label_type': self.label_type,
            'format': self.format,
            'quantity_printed': self.quantity_printed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by
        }
    
    def __repr__(self):
        return f'<BarcodeLabel {self.label_type} - Product {self.product_id}>'
