from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from datetime import datetime


def generate_purchase_order_pdf(orden, output_buffer):
    """
    Genera un PDF ejecutivo de orden de compra
    
    Args:
        orden: objeto OrdenCompra de SQLAlchemy
        output_buffer: BytesIO buffer donde se escribirá el PDF
    
    Returns:
        BytesIO buffer con el PDF generado
    """
    doc = SimpleDocTemplate(
        output_buffer,
        pagesize=letter,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch,
        leftMargin=0.75*inch,
        rightMargin=0.75*inch
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_data = [[Paragraph('<b>ORDEN DE COMPRA</b>', 
                             ParagraphStyle('Title', parent=styles['Normal'], 
                                          fontSize=18, alignment=TA_CENTER))]]
    title_table = Table(title_data, colWidths=[6.5*inch])
    title_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(title_table)
    
    # Status bar
    status_text = f'<b>Estado: {orden.estado.upper()}</b>'
    status_data = [[Paragraph(status_text, 
                             ParagraphStyle('Status', parent=styles['Normal'], 
                                          fontSize=10, alignment=TA_CENTER, 
                                          textColor=colors.white))]]
    status_table = Table(status_data, colWidths=[6.5*inch])
    status_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(status_table)
    story.append(Spacer(1, 10))
    
    # Section: Información General
    info_header = [[Paragraph('<b>INFORMACIÓN GENERAL</b>', 
                             ParagraphStyle('SectionHeader', parent=styles['Normal'], 
                                          fontSize=9, textColor=colors.white))]]
    info_header_table = Table(info_header, colWidths=[6.5*inch])
    info_header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#333333')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(info_header_table)
    
    # General information
    fecha_orden = orden.fecha.strftime('%d/%m/%Y') if orden.fecha else 'N/A'
    
    general_info = [
        ['Número de Orden:', orden.numero_orden or 'N/A', 'Fecha de Orden:', fecha_orden],
        ['Fecha de Emisión:', fecha_orden, '', ''],
        ['Proveedor:', orden.proveedor or 'N/A', '', ''],
        ['Dirección:', orden.direccion_proveedor or 'N/A', '', ''],
        ['Teléfono:', orden.telefono_proveedor or 'N/A', 'Elaborado por:', orden.elaborado_por or 'N/A'],
        ['', '', 'Verificado por:', orden.verificado_por or 'N/A'],
    ]
    
    info_table = Table(general_info, colWidths=[1.4*inch, 1.75*inch, 1.5*inch, 1.85*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('ALIGN', (3, 0), (3, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('SPAN', (1, 3), (3, 3)),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 10))
    
    # Section: Detalle de Productos
    products_header = [[Paragraph('<b>DETALLE DE PRODUCTOS</b>', 
                                 ParagraphStyle('ProdHeader', parent=styles['Normal'], 
                                              fontSize=9, textColor=colors.white))]]
    products_header_table = Table(products_header, colWidths=[6.5*inch])
    products_header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#333333')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(products_header_table)
    
    # Products table
    products_data = [['Descripción', 'Cant.', 'Unidad', 'Precio Unit.', 'Subtotal']]
    
    for detalle in orden.detalles:
        products_data.append([
            detalle.producto_descripcion or 'N/A',
            str(detalle.cantidad) if detalle.cantidad else '0',
            detalle.unidad_medida or 'UND',
            f"${detalle.precio_unitario:,.2f}" if detalle.precio_unitario else '$0.00',
            f"${detalle.subtotal:,.2f}" if detalle.subtotal else '$0.00'
        ])
    
    products_table = Table(products_data, colWidths=[3.1*inch, 0.4*inch, 0.6*inch, 1.2*inch, 1.2*inch])
    products_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E8E8E8')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (2, -1), 'CENTER'),
        ('ALIGN', (3, 0), (4, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#666666')),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(products_table)
    story.append(Spacer(1, 10))
    
    # Section: Resumen Financiero
    financial_header = [[Paragraph('<b>RESUMEN FINANCIERO</b>', 
                                  ParagraphStyle('FinHeader', parent=styles['Normal'], 
                                               fontSize=9, textColor=colors.white))]]
    financial_header_table = Table(financial_header, colWidths=[6.5*inch])
    financial_header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#333333')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(financial_header_table)
    
    # Financial summary
    subtotal = orden.subtotal if orden.subtotal else 0
    iva = orden.iva if orden.iva else 0
    descuento = orden.descuento if orden.descuento else 0
    total = orden.total if orden.total else 0
    
    financial_data = [
        ['Subtotal', f"${subtotal:,.2f}"],
        ['IVA (19%)', f"${iva:,.2f}"],
    ]
    
    # Agregar descuento solo si existe
    if descuento > 0:
        financial_data.append(['Descuento', f"-${descuento:,.2f}"])
    
    financial_data.append(['TOTAL', f"${total:,.2f}"])
    
    financial_table = Table(financial_data, colWidths=[5.3*inch, 1.2*inch])
    
    # Determinar el índice de la fila TOTAL (última fila)
    total_row_index = len(financial_data) - 1
    
    financial_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, total_row_index-1), 'Helvetica'),
        ('FONTNAME', (0, total_row_index), (-1, total_row_index), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, total_row_index-1), 9),
        ('FONTSIZE', (0, total_row_index), (-1, total_row_index), 11),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEABOVE', (0, total_row_index), (-1, total_row_index), 1.5, colors.black),
        ('LINEBELOW', (0, total_row_index), (-1, total_row_index), 1.5, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, total_row_index-1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, total_row_index-1), 3),
        ('TOPPADDING', (0, total_row_index), (-1, total_row_index), 6),
        ('BOTTOMPADDING', (0, total_row_index), (-1, total_row_index), 6),
    ]))
    story.append(financial_table)
    
    story.append(Spacer(1, 15))
    
    # Observaciones si existen
    if orden.observaciones:
        obs_header = [[Paragraph('<b>OBSERVACIONES</b>', 
                                ParagraphStyle('ObsHeader', parent=styles['Normal'], 
                                             fontSize=9, textColor=colors.white))]]
        obs_header_table = Table(obs_header, colWidths=[6.5*inch])
        obs_header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#333333')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(obs_header_table)
        
        obs_text = Paragraph(orden.observaciones, 
                           ParagraphStyle('ObsText', parent=styles['Normal'], fontSize=8))
        story.append(obs_text)
        story.append(Spacer(1, 10))
    
    # Footer
    notes_style = ParagraphStyle('Notes', parent=styles['Normal'], 
                                fontSize=7, textColor=colors.HexColor('#666666'))
    notes = Paragraph(f'Documento generado el {datetime.now().strftime("%d/%m/%Y %H:%M")}', notes_style)
    story.append(notes)
    
    # Build PDF
    doc.build(story)
    
    return output_buffer
