from PIL import Image
import io
import os
import base64
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


def fetch_currency_by_code(code):
    from utils.currencies import get_currency_by_code
    return get_currency_by_code(code)


def get_currency_symbol(code):
    currency = fetch_currency_by_code(code)
    return currency.get("symbol", code)


def generate_receipt_pdf(booking, screen, content, qr_base64=None):
    buffer = io.BytesIO()
    width, height = A5
    c = canvas.Canvas(buffer, pagesize=A5)
    
    currency = fetch_currency_by_code(screen.organization.currency if hasattr(screen.organization, 'currency') and screen.organization.currency else 'EUR')
    currency_symbol = currency.get('symbol', 'EUR')
    
    c.setFillColor(colors.HexColor('#10b981'))
    c.rect(0, height - 80, width, 80, fill=True, stroke=False)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 35, "SHABAKA ADSCREEN")
    
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - 55, "Recu de Reservation")
    
    y = height - 110
    
    c.setFillColor(colors.HexColor('#f3f4f6'))
    c.roundRect(30, y - 45, width - 60, 50, 5, fill=True, stroke=False)
    
    c.setFillColor(colors.HexColor('#6b7280'))
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, y - 10, "N Reservation")
    
    c.setFillColor(colors.HexColor('#111827'))
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, y - 30, booking.reservation_number or "---")
    
    y -= 70
    
    details = [
        ("Ecran", screen.name[:30]),
        ("Etablissement", screen.organization.name[:30]),
        ("Type", content.content_type.capitalize() if content.content_type else "---"),
        ("Duree creneau", f"{booking.slot_duration}s"),
        ("Diffusions", str(booking.num_plays)),
        ("Date debut", booking.start_date.strftime('%d/%m/%Y') if booking.start_date else "-"),
    ]
    
    if booking.end_date:
        details.append(("Date fin", booking.end_date.strftime('%d/%m/%Y')))
    
    details.append(("Prix unitaire", f"{booking.price_per_play:.2f} {currency_symbol}"))
    
    c.setFont("Helvetica", 11)
    for label, value in details:
        c.setFillColor(colors.HexColor('#6b7280'))
        c.drawString(40, y, label)
        c.setFillColor(colors.HexColor('#111827'))
        c.drawRightString(width - 40, y, value)
        y -= 20
    
    y -= 10
    c.setStrokeColor(colors.HexColor('#e5e7eb'))
    c.line(30, y, width - 30, y)
    y -= 25
    
    c.setFillColor(colors.HexColor('#10b981'))
    c.roundRect(30, y - 35, width - 60, 40, 5, fill=True, stroke=False)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, y - 22, f"TOTAL: {booking.total_price:.2f} {currency_symbol}")
    
    y -= 60
    
    c.setFillColor(colors.HexColor('#fef3c7'))
    c.roundRect(30, y - 30, width - 60, 35, 5, fill=True, stroke=False)
    
    c.setFillColor(colors.HexColor('#92400e'))
    c.setFont("Helvetica", 11)
    c.drawCentredString(width / 2, y - 18, "En attente de validation")
    
    y -= 55
    
    if qr_base64:
        try:
            qr_data = base64.b64decode(qr_base64)
            qr_img = Image.open(io.BytesIO(qr_data))
            qr_size = 70
            qr_x = (width - qr_size) / 2
            c.drawImage(ImageReader(qr_img), qr_x, y - qr_size, width=qr_size, height=qr_size)
            y -= qr_size + 15
        except Exception:
            pass
    
    c.setFillColor(colors.HexColor('#6b7280'))
    c.setFont("Helvetica", 9)
    c.drawCentredString(width / 2, 40, screen.organization.name)
    c.setFillColor(colors.HexColor('#9ca3af'))
    c.drawCentredString(width / 2, 25, datetime.now().strftime('%d/%m/%Y %H:%M'))
    
    c.save()
    buffer.seek(0)
    return buffer


def pdf_to_image(pdf_buffer):
    try:
        import fitz
        pdf_buffer.seek(0)
        pdf_document = fitz.open(stream=pdf_buffer.read(), filetype="pdf")
        page = pdf_document.load_page(0)
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        pdf_document.close()
        return Image.open(io.BytesIO(img_data))
    except ImportError:
        return generate_receipt_image_fallback(pdf_buffer)


def generate_receipt_image_fallback(pdf_buffer):
    width = 400
    height = 600
    img = Image.new('RGB', (width, height), color='white')
    return img


def generate_receipt_image(booking, screen, content, qr_base64=None):
    width = 400
    height = 600
    
    from PIL import ImageDraw, ImageFont
    
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        font_regular = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    except:
        font_bold = ImageFont.load_default()
        font_regular = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_large = ImageFont.load_default()
    
    draw.rectangle([0, 0, width, 70], fill='#10b981')
    
    draw.text((width//2, 25), "SHABAKA ADSCREEN", fill='white', font=font_large, anchor='mm')
    draw.text((width//2, 50), "Recu de Reservation", fill='#d1fae5', font=font_regular, anchor='mm')
    
    y = 90
    
    draw.rectangle([30, y, width-30, y+50], fill='#f3f4f6', outline='#e5e7eb')
    draw.text((width//2, y+15), "N Reservation", fill='#6b7280', font=font_small, anchor='mm')
    draw.text((width//2, y+35), booking.reservation_number or "---", fill='#111827', font=font_bold, anchor='mm')
    
    y += 70
    
    currency = fetch_currency_by_code(screen.organization.currency if hasattr(screen.organization, 'currency') and screen.organization.currency else 'EUR')
    currency_symbol = currency.get('symbol', 'EUR')
    
    details = [
        ("Ecran", screen.name[:25]),
        ("Etablissement", screen.organization.name[:25]),
        ("Type", content.content_type.capitalize() if content.content_type else "---"),
        ("Duree creneau", f"{booking.slot_duration}s"),
        ("Diffusions", str(booking.num_plays)),
        ("Date debut", booking.start_date.strftime('%d/%m/%Y') if booking.start_date else "-"),
        ("Prix unitaire", f"{booking.price_per_play:.2f} {currency_symbol}"),
    ]
    
    if booking.end_date:
        details.insert(6, ("Date fin", booking.end_date.strftime('%d/%m/%Y')))
    
    for label, value in details:
        draw.text((40, y), label, fill='#6b7280', font=font_regular)
        draw.text((width-40, y), value, fill='#111827', font=font_regular, anchor='ra')
        y += 22
    
    y += 10
    draw.line([(30, y), (width-30, y)], fill='#e5e7eb', width=1)
    y += 15
    
    draw.rectangle([30, y, width-30, y+40], fill='#10b981', outline='#059669')
    draw.text((width//2, y+20), f"TOTAL: {booking.total_price:.2f} {currency_symbol}", fill='white', font=font_large, anchor='mm')
    
    y += 60
    
    draw.rectangle([30, y, width-30, y+35], fill='#fef3c7', outline='#fcd34d')
    draw.text((width//2, y+17), "En attente de validation", fill='#92400e', font=font_regular, anchor='mm')
    
    y += 55
    
    if qr_base64:
        try:
            qr_data = base64.b64decode(qr_base64)
            qr_img = Image.open(io.BytesIO(qr_data))
            qr_size = 80
            qr_img = qr_img.resize((qr_size, qr_size))
            qr_x = (width - qr_size) // 2
            img.paste(qr_img, (qr_x, y))
            y += qr_size + 10
        except Exception:
            pass
    
    footer_y = height - 40
    draw.text((width//2, footer_y), screen.organization.name, fill='#6b7280', font=font_small, anchor='mm')
    draw.text((width//2, footer_y + 15), datetime.now().strftime('%d/%m/%Y %H:%M'), fill='#9ca3af', font=font_small, anchor='mm')
    
    return img


def save_receipt_pdf(booking, screen, content, qr_base64=None):
    pdf_buffer = generate_receipt_pdf(booking, screen, content, qr_base64)
    
    receipts_dir = os.path.join('static', 'uploads', 'receipts')
    os.makedirs(receipts_dir, exist_ok=True)
    
    filename = f"receipt_{booking.reservation_number}.pdf"
    filepath = os.path.join(receipts_dir, filename)
    
    with open(filepath, 'wb') as f:
        f.write(pdf_buffer.read())
    
    return filepath


def save_receipt_image(booking, screen, content, qr_base64=None):
    img = generate_receipt_image(booking, screen, content, qr_base64)
    
    receipts_dir = os.path.join('static', 'uploads', 'receipts')
    os.makedirs(receipts_dir, exist_ok=True)
    
    filename = f"receipt_{booking.reservation_number}.png"
    filepath = os.path.join(receipts_dir, filename)
    
    img.save(filepath, 'PNG')
    
    return filepath


def get_receipt_base64(booking, screen, content, qr_base64=None):
    img = generate_receipt_image(booking, screen, content, qr_base64)
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def get_receipt_pdf_base64(booking, screen, content, qr_base64=None):
    pdf_buffer = generate_receipt_pdf(booking, screen, content, qr_base64)
    pdf_buffer.seek(0)
    return base64.b64encode(pdf_buffer.read()).decode('utf-8')
