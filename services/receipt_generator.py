from PIL import Image, ImageDraw, ImageFont
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


def _get_receipt_data(booking, screen, content):
    """Extract common receipt data used by both PDF and image generators."""
    currency = fetch_currency_by_code(
        screen.organization.currency if hasattr(screen.organization, 'currency') and screen.organization.currency else 'EUR'
    )
    currency_symbol = currency.get('symbol', 'EUR')
    
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
    
    return {
        'currency_symbol': currency_symbol,
        'details': details,
        'reservation_number': booking.reservation_number or "---",
        'total_price': f"{booking.total_price:.2f} {currency_symbol}",
        'org_name': screen.organization.name,
        'date_time': datetime.now().strftime('%d/%m/%Y %H:%M')
    }


def generate_receipt_pdf(booking, screen, content, qr_base64=None):
    buffer = io.BytesIO()
    width, height = A5
    c = canvas.Canvas(buffer, pagesize=A5)
    
    data = _get_receipt_data(booking, screen, content)
    currency_symbol = data['currency_symbol']
    
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
    c.drawCentredString(width / 2, y - 30, data['reservation_number'])
    
    y -= 70
    
    c.setFont("Helvetica", 11)
    for label, value in data['details']:
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
    c.drawCentredString(width / 2, y - 22, f"TOTAL: {data['total_price']}")
    
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
    c.drawCentredString(width / 2, 40, data['org_name'])
    c.setFillColor(colors.HexColor('#9ca3af'))
    c.drawCentredString(width / 2, 25, data['date_time'])
    
    c.save()
    buffer.seek(0)
    return buffer


def _draw_rounded_rect(draw, xy, radius, fill):
    """Draw a rounded rectangle on PIL ImageDraw."""
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill)


def _get_font(size, bold=False):
    """Get a font, falling back to default if custom fonts not available."""
    try:
        if bold:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except:
        return ImageFont.load_default()


def generate_receipt_image(booking, screen, content, qr_base64=None):
    """Generate receipt image directly using PIL with the same design as PDF."""
    scale = 2.5
    width = int(A5[0] * scale)
    height = int(A5[1] * scale)
    
    img = Image.new('RGB', (width, height), '#ffffff')
    draw = ImageDraw.Draw(img)
    
    data = _get_receipt_data(booking, screen, content)
    
    font_title = _get_font(int(18 * scale), bold=True)
    font_subtitle = _get_font(int(12 * scale))
    font_label = _get_font(int(10 * scale))
    font_value = _get_font(int(11 * scale))
    font_value_bold = _get_font(int(14 * scale), bold=True)
    font_total = _get_font(int(16 * scale), bold=True)
    font_status = _get_font(int(11 * scale))
    font_footer = _get_font(int(9 * scale))
    
    header_height = int(80 * scale)
    draw.rectangle([0, 0, width, header_height], fill='#10b981')
    
    title_text = "SHABAKA ADSCREEN"
    title_bbox = draw.textbbox((0, 0), title_text, font=font_title)
    title_x = (width - (title_bbox[2] - title_bbox[0])) // 2
    draw.text((title_x, int(25 * scale)), title_text, fill='#ffffff', font=font_title)
    
    subtitle_text = "Recu de Reservation"
    subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=font_subtitle)
    subtitle_x = (width - (subtitle_bbox[2] - subtitle_bbox[0])) // 2
    draw.text((subtitle_x, int(50 * scale)), subtitle_text, fill='#ffffff', font=font_subtitle)
    
    y = int(100 * scale)
    
    box_x1 = int(30 * scale)
    box_x2 = width - int(30 * scale)
    box_height = int(50 * scale)
    _draw_rounded_rect(draw, (box_x1, y, box_x2, y + box_height), radius=int(5 * scale), fill='#f3f4f6')
    
    res_label = "N Reservation"
    res_label_bbox = draw.textbbox((0, 0), res_label, font=font_label)
    res_label_x = (width - (res_label_bbox[2] - res_label_bbox[0])) // 2
    draw.text((res_label_x, y + int(8 * scale)), res_label, fill='#6b7280', font=font_label)
    
    res_num = data['reservation_number']
    res_num_bbox = draw.textbbox((0, 0), res_num, font=font_value_bold)
    res_num_x = (width - (res_num_bbox[2] - res_num_bbox[0])) // 2
    draw.text((res_num_x, y + int(28 * scale)), res_num, fill='#111827', font=font_value_bold)
    
    y += int(70 * scale)
    
    left_margin = int(40 * scale)
    right_margin = width - int(40 * scale)
    line_height = int(20 * scale)
    
    for label, value in data['details']:
        draw.text((left_margin, y), label, fill='#6b7280', font=font_value)
        value_bbox = draw.textbbox((0, 0), value, font=font_value)
        value_x = right_margin - (value_bbox[2] - value_bbox[0])
        draw.text((value_x, y), value, fill='#111827', font=font_value)
        y += line_height
    
    y += int(10 * scale)
    draw.line([(int(30 * scale), y), (width - int(30 * scale), y)], fill='#e5e7eb', width=1)
    y += int(15 * scale)
    
    total_box_height = int(40 * scale)
    _draw_rounded_rect(draw, (box_x1, y, box_x2, y + total_box_height), radius=int(5 * scale), fill='#10b981')
    
    total_text = f"TOTAL: {data['total_price']}"
    total_bbox = draw.textbbox((0, 0), total_text, font=font_total)
    total_x = (width - (total_bbox[2] - total_bbox[0])) // 2
    total_y = y + (total_box_height - (total_bbox[3] - total_bbox[1])) // 2
    draw.text((total_x, total_y), total_text, fill='#ffffff', font=font_total)
    
    y += total_box_height + int(20 * scale)
    
    status_box_height = int(35 * scale)
    _draw_rounded_rect(draw, (box_x1, y, box_x2, y + status_box_height), radius=int(5 * scale), fill='#fef3c7')
    
    status_text = "En attente de validation"
    status_bbox = draw.textbbox((0, 0), status_text, font=font_status)
    status_x = (width - (status_bbox[2] - status_bbox[0])) // 2
    status_y = y + (status_box_height - (status_bbox[3] - status_bbox[1])) // 2
    draw.text((status_x, status_y), status_text, fill='#92400e', font=font_status)
    
    y += status_box_height + int(20 * scale)
    
    if qr_base64:
        try:
            qr_data = base64.b64decode(qr_base64)
            qr_img = Image.open(io.BytesIO(qr_data))
            qr_size = int(70 * scale)
            qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
            qr_x = (width - qr_size) // 2
            img.paste(qr_img, (qr_x, y))
            y += qr_size + int(15 * scale)
        except Exception:
            pass
    
    footer_y = height - int(60 * scale)
    
    org_text = data['org_name']
    org_bbox = draw.textbbox((0, 0), org_text, font=font_footer)
    org_x = (width - (org_bbox[2] - org_bbox[0])) // 2
    draw.text((org_x, footer_y), org_text, fill='#6b7280', font=font_footer)
    
    date_text = data['date_time']
    date_bbox = draw.textbbox((0, 0), date_text, font=font_footer)
    date_x = (width - (date_bbox[2] - date_bbox[0])) // 2
    draw.text((date_x, footer_y + int(15 * scale)), date_text, fill='#9ca3af', font=font_footer)
    
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
