import barcode
from barcode.writer import ImageWriter
import qrcode
from io import BytesIO
import base64
from PIL import Image, ImageDraw, ImageFont

class BarcodeGenerator:
    """
    Clase para generar códigos de barras y QR.
    Soporta múltiples formatos y opciones de personalización.
    """
    
    @staticmethod
    def generate_barcode_image(code, barcode_type='ean13'):
        """
        Genera una imagen de código de barras.
        
        Args:
            code (str): Código a generar
            barcode_type (str): Tipo de código ('ean13', 'code128', 'code39', 'upc')
        
        Returns:
            dict: Resultado con imagen en base64 o error
        """
        try:
            # Seleccionar tipo de código de barras
            barcode_class = None
            
            if barcode_type == 'ean13':
                barcode_class = barcode.get_barcode_class('ean13')
                # EAN-13 requiere exactamente 13 dígitos
                if len(code) != 13:
                    return {
                        'success': False,
                        'error': 'EAN-13 requiere exactamente 13 dígitos'
                    }
            elif barcode_type == 'code128':
                barcode_class = barcode.get_barcode_class('code128')
            elif barcode_type == 'code39':
                barcode_class = barcode.get_barcode_class('code39')
            elif barcode_type == 'upc':
                barcode_class = barcode.get_barcode_class('upca')
            else:
                return {
                    'success': False,
                    'error': f'Tipo de código no soportado: {barcode_type}'
                }
            
            # Crear código de barras
            barcode_instance = barcode_class(code, writer=ImageWriter())
            
            # Guardar en buffer
            buffer = BytesIO()
            barcode_instance.write(buffer, options={
                'module_width': 0.3,
                'module_height': 15.0,
                'quiet_zone': 6.5,
                'font_size': 10,
                'text_distance': 5.0,
            })
            buffer.seek(0)
            
            # Convertir a base64
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                'success': True,
                'image': f"data:image/png;base64,{img_base64}",
                'code': code,
                'type': barcode_type
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def generate_qr_image(data, size=10, error_correction='M'):
        """
        Genera una imagen de código QR.
        
        Args:
            data (str): Datos a codificar
            size (int): Tamaño del QR (1-40)
            error_correction (str): Nivel de corrección ('L', 'M', 'Q', 'H')
        
        Returns:
            dict: Resultado con imagen en base64 o error
        """
        try:
            # Mapear nivel de corrección de errores
            error_map = {
                'L': qrcode.constants.ERROR_CORRECT_L,
                'M': qrcode.constants.ERROR_CORRECT_M,
                'Q': qrcode.constants.ERROR_CORRECT_Q,
                'H': qrcode.constants.ERROR_CORRECT_H
            }
            
            error_level = error_map.get(error_correction, qrcode.constants.ERROR_CORRECT_M)
            
            # Crear código QR
            qr = qrcode.QRCode(
                version=1,
                error_correction=error_level,
                box_size=size,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            # Generar imagen
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convertir a base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                'success': True,
                'image': f"data:image/png;base64,{img_base64}",
                'data': data,
                'size': size,
                'error_correction': error_correction
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def generate_product_label(product_data, include_qr=False):
        """
        Genera una etiqueta completa con código de barras y información del producto.
        
        Args:
            product_data (dict): Información del producto
            include_qr (bool): Incluir código QR en la etiqueta
        
        Returns:
            dict: Resultado con imagen en base64 o error
        """
        try:
            # Dimensiones de la etiqueta (ajustables según necesidad)
            width, height = 500, 400 if include_qr else 350
            img = Image.new('RGB', (width, height), 'white')
            draw = ImageDraw.Draw(img)
            
            # Intentar cargar fuentes del sistema
            try:
                title_font = ImageFont.truetype("arial.ttf", 22)
                text_font = ImageFont.truetype("arial.ttf", 16)
                small_font = ImageFont.truetype("arial.ttf", 12)
            except:
                # Fallback a fuente por defecto
                title_font = ImageFont.load_default()
                text_font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            
            # Información del producto
            y_position = 15
            
            # Título del producto
            product_name = product_data.get('name', 'Producto')[:40]
            draw.text((15, y_position), product_name, fill='black', font=title_font)
            y_position += 35
            
            # Línea divisoria
            draw.line([(15, y_position), (width-15, y_position)], fill='#cccccc', width=2)
            y_position += 15
            
            # Información adicional
            info_items = []
            
            if product_data.get('sku'):
                info_items.append(f"SKU: {product_data['sku']}")
            
            if product_data.get('category'):
                info_items.append(f"Categoría: {product_data['category']}")
            
            if product_data.get('price'):
                info_items.append(f"Precio: ${product_data['price']:,.2f}")
            
            for item in info_items:
                draw.text((15, y_position), item, fill='black', font=text_font)
                y_position += 25
            
            y_position += 10
            
            # Generar código de barras
            if product_data.get('barcode'):
                barcode_result = BarcodeGenerator.generate_barcode_image(
                    product_data['barcode']
                )
                
                if barcode_result['success']:
                    # Decodificar imagen de código de barras
                    barcode_data = barcode_result['image'].split(',')[1]
                    barcode_img = Image.open(BytesIO(base64.b64decode(barcode_data)))
                    
                    # Redimensionar para que quepa en la etiqueta
                    barcode_width = width - 40
                    barcode_height = int(barcode_img.height * (barcode_width / barcode_img.width))
                    barcode_img = barcode_img.resize((barcode_width, barcode_height))
                    
                    # Pegar en la etiqueta
                    img.paste(barcode_img, (20, y_position))
                    y_position += barcode_height + 15
            
            # Agregar código QR si se solicita
            if include_qr and product_data.get('qr_code'):
                qr_result = BarcodeGenerator.generate_qr_image(
                    product_data['qr_code'], 
                    size=5
                )
                
                if qr_result['success']:
                    qr_data = qr_result['image'].split(',')[1]
                    qr_img = Image.open(BytesIO(base64.b64decode(qr_data)))
                    qr_img = qr_img.resize((120, 120))
                    img.paste(qr_img, (width - 140, height - 140))
            
            # Convertir a base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                'success': True,
                'image': f"data:image/png;base64,{img_base64}"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def generate_batch_labels(products_list, include_qr=False):
        """
        Genera múltiples etiquetas en un solo documento.
        
        Args:
            products_list (list): Lista de diccionarios con información de productos
            include_qr (bool): Incluir códigos QR en las etiquetas
        
        Returns:
            dict: Resultado con lista de etiquetas o error
        """
        try:
            labels = []
            errors = []
            
            for product_data in products_list:
                label = BarcodeGenerator.generate_product_label(product_data, include_qr)
                
                if label['success']:
                    labels.append({
                        'product_id': product_data.get('id'),
                        'product_name': product_data.get('name'),
                        'image': label['image']
                    })
                else:
                    errors.append({
                        'product_id': product_data.get('id'),
                        'product_name': product_data.get('name'),
                        'error': label.get('error')
                    })
            
            return {
                'success': True,
                'count': len(labels),
                'labels': labels,
                'errors': errors if errors else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def validate_barcode(code, barcode_type='ean13'):
        """
        Valida un código de barras según su tipo.
        
        Args:
            code (str): Código a validar
            barcode_type (str): Tipo de código
        
        Returns:
            dict: Resultado de validación
        """
        try:
            if barcode_type == 'ean13':
                # Validar longitud
                if len(code) != 13:
                    return {
                        'valid': False,
                        'error': 'EAN-13 debe tener exactamente 13 dígitos'
                    }
                
                # Validar que sean solo números
                if not code.isdigit():
                    return {
                        'valid': False,
                        'error': 'EAN-13 debe contener solo dígitos'
                    }
                
                # Validar dígito de verificación
                odd_sum = sum(int(code[i]) for i in range(0, 12, 2))
                even_sum = sum(int(code[i]) for i in range(1, 12, 2))
                total = odd_sum + (even_sum * 3)
                check_digit = (10 - (total % 10)) % 10
                
                if int(code[12]) != check_digit:
                    return {
                        'valid': False,
                        'error': f'Dígito de verificación incorrecto. Esperado: {check_digit}'
                    }
                
                return {
                    'valid': True,
                    'type': 'ean13',
                    'check_digit': check_digit
                }
            
            # Otros tipos de código se consideran válidos si no están vacíos
            return {
                'valid': bool(code),
                'type': barcode_type
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
