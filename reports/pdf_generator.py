import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generar_pdf_caso(texto_reporte, filename="expediente_forense.pdf"):
    # Ruta de salida
    filepath = os.path.join("reports", filename)
    os.makedirs("reports", exist_ok=True)
    
    doc = SimpleDocTemplate(filepath, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    
    # Estilos personalizados con elegancia corporativa
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=12
    )
    
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor("#2D3748"),
        leading=14,
        spaceAfter=8
    )
    
    # Encabezado formal
    # Encabezado formal
    story.append(Paragraph("THE FORENSIC AUDITOR - AUDIT CASE FILE", title_style))
    story.append(Paragraph("<b>REPORTE TÉCNICO DE INVESTIGACIÓN FINANCIERA</b>", body_style))
    story.append(Paragraph("<i>Infosys Challenge — HackMTY 2026</i>", body_style))
    story.append(Spacer(1, 10))
    
    # Línea divisoria
    d = Table([['']], colWidths=[550], rowHeights=[2])
    d.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#E2E8F0"))]))
    story.append(d)
    story.append(Spacer(1, 15))
    
    # Contenido del reporte generado por la IA (con la sangría correcta)
    for linea in texto_reporte.split('\n'):
        if linea.strip():
            story.append(Paragraph(linea, body_style))
            
    story.append(Spacer(1, 20))
    story.append(Paragraph("<b>ESTADO:</b> Documento generado automáticamente por Agente Autónomo Gemini.", body_style))
    
    doc.build(story)
    return filepath