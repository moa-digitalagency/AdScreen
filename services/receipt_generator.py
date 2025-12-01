from PIL import Image, ImageDraw, ImageFont
import io
import os
import base64
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
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
    
    vat_rate = getattr(booking, 'vat_rate', 0) or 0
    vat_amount = getattr(booking, 'vat_amount', 0) or 0
    total_price_with_vat = getattr(booking, 'total_price_with_vat', None) or booking.total_price
    
    return {
        'currency_symbol': currency_symbol,
        'reservation_number': booking.reservation_number or "---",
        'org_name': screen.organization.name,
        'screen_name': screen.name,
        'content_type': content.content_type.capitalize() if content.content_type else "---",
        'original_filename': content.original_filename or "---",
        'slot_duration': booking.slot_duration,
        'num_plays': booking.num_plays,
        'start_date': booking.start_date.strftime('%d/%m/%Y') if booking.start_date else "-",
        'end_date': booking.end_date.strftime('%d/%m/%Y') if booking.end_date else None,
        'price_per_play': booking.price_per_play,
        'total_price': booking.total_price,
        'vat_rate': vat_rate,
        'vat_amount': vat_amount,
        'total_price_with_vat': total_price_with_vat,
        'client_name': content.client_name or "Anonyme",
        'client_email': content.client_email or "---",
        'created_at': booking.created_at.strftime('%d/%m/%Y a %H:%M') if booking.created_at else datetime.now().strftime('%d/%m/%Y a %H:%M'),
        'date_time': datetime.now().strftime('%d/%m/%Y %H:%M')
    }


def _get_font(size, bold=False, mono=True):
    """Get a font, preferring monospace for thermal receipt style."""
    try:
        if mono:
            if bold:
                return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", size)
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", size)
        else:
            if bold:
                return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except:
        return ImageFont.load_default()


def _truncate(text, max_len):
    """Truncate text with ellipsis if too long."""
    if len(text) > max_len:
        return text[:max_len-2] + ".."
    return text


def generate_receipt_image(booking, screen, content, qr_base64=None):
    """Generate thermal-style receipt image matching the print design."""
    width = 400
    
    data = _get_receipt_data(booking, screen, content)
    
    font_title = _get_font(24, bold=True)
    font_subtitle = _get_font(14)
    font_section = _get_font(12, bold=True)
    font_label = _get_font(14)
    font_value = _get_font(14, bold=True)
    font_total = _get_font(20, bold=True)
    font_status = _get_font(12)
    font_small = _get_font(11)
    font_footer = _get_font(12)
    
    padding = 20
    line_height = 22
    section_gap = 15
    
    temp_img = Image.new('RGB', (width, 2000), '#ffffff')
    temp_draw = ImageDraw.Draw(temp_img)
    
    y = padding
    
    title_bbox = temp_draw.textbbox((0, 0), data['org_name'], font=font_title)
    y += (title_bbox[3] - title_bbox[1]) + 5
    
    subtitle_bbox = temp_draw.textbbox((0, 0), data['screen_name'], font=font_subtitle)
    y += (subtitle_bbox[3] - subtitle_bbox[1]) + 15
    
    y += 3
    
    y += 50 + 15
    
    y += 3 + section_gap
    
    y += 18 + 10
    
    detail_lines = 7
    if data['end_date']:
        detail_lines += 1
    y += detail_lines * line_height
    
    y += 3 + section_gap
    y += 18 + 10
    y += 2 * line_height
    
    y += 3 + section_gap
    
    y += 50 + section_gap
    
    y += 40 + section_gap
    
    y += 3 + section_gap
    y += 2 * line_height
    
    y += 3 + section_gap
    
    qr_size = 80
    if qr_base64:
        y += qr_size + 10
    
    y += 3 + section_gap
    y += 4 * 16
    
    y += padding
    
    height = y
    
    img = Image.new('RGB', (width, height), '#ffffff')
    draw = ImageDraw.Draw(img)
    
    y = padding
    
    title = data['org_name']
    title_bbox = draw.textbbox((0, 0), title, font=font_title)
    title_x = (width - (title_bbox[2] - title_bbox[0])) // 2
    draw.text((title_x, y), title, fill='#000000', font=font_title)
    y += (title_bbox[3] - title_bbox[1]) + 5
    
    subtitle = data['screen_name']
    subtitle_bbox = draw.textbbox((0, 0), subtitle, font=font_subtitle)
    subtitle_x = (width - (subtitle_bbox[2] - subtitle_bbox[0])) // 2
    draw.text((subtitle_x, y), subtitle, fill='#000000', font=font_subtitle)
    y += (subtitle_bbox[3] - subtitle_bbox[1]) + 15
    
    draw.line([(padding, y), (width - padding, y)], fill='#000000', width=1)
    y += 3
    
    def draw_dashed_line(y_pos):
        dash_width = 8
        gap_width = 4
        x = padding
        while x < width - padding:
            end_x = min(x + dash_width, width - padding)
            draw.line([(x, y_pos), (end_x, y_pos)], fill='#000000', width=1)
            x += dash_width + gap_width
    
    box_y = y + 5
    box_height = 50
    draw.rectangle([(padding, box_y), (width - padding, box_y + box_height)], outline='#000000', width=2)
    
    res_label = "N° RESERVATION"
    res_label_bbox = draw.textbbox((0, 0), res_label, font=font_small)
    res_label_x = (width - (res_label_bbox[2] - res_label_bbox[0])) // 2
    draw.text((res_label_x, box_y + 5), res_label, fill='#000000', font=font_small)
    
    res_num = data['reservation_number']
    res_num_bbox = draw.textbbox((0, 0), res_num, font=font_value)
    res_num_x = (width - (res_num_bbox[2] - res_num_bbox[0])) // 2
    draw.text((res_num_x, box_y + 25), res_num, fill='#000000', font=font_value)
    
    y = box_y + box_height + 15
    
    draw_dashed_line(y)
    y += 3 + section_gap
    
    section_title = "RECAPITULATIF"
    section_bbox = draw.textbbox((0, 0), section_title, font=font_section)
    section_x = (width - (section_bbox[2] - section_bbox[0])) // 2
    draw.text((section_x, y), section_title, fill='#000000', font=font_section)
    y += 18 + 10
    
    def draw_detail_line(label, value, y_pos):
        draw.text((padding, y_pos), label, fill='#333333', font=font_label)
        value_bbox = draw.textbbox((0, 0), value, font=font_value)
        value_x = width - padding - (value_bbox[2] - value_bbox[0])
        draw.text((value_x, y_pos), value, fill='#000000', font=font_value)
        return y_pos + line_height
    
    y = draw_detail_line("Ecran:", _truncate(data['screen_name'], 18), y)
    y = draw_detail_line("Etablis.:", _truncate(data['org_name'], 16), y)
    y = draw_detail_line("Type:", data['content_type'], y)
    y = draw_detail_line("Fichier:", _truncate(data['original_filename'], 15), y)
    y = draw_detail_line("Creneau:", f"{data['slot_duration']}s", y)
    y = draw_detail_line("Diffusions:", f"{data['num_plays']}x", y)
    y = draw_detail_line("Debut:", data['start_date'], y)
    if data['end_date']:
        y = draw_detail_line("Fin:", data['end_date'], y)
    
    draw_dashed_line(y)
    y += 3 + section_gap
    
    section_title = "TARIFICATION"
    section_bbox = draw.textbbox((0, 0), section_title, font=font_section)
    section_x = (width - (section_bbox[2] - section_bbox[0])) // 2
    draw.text((section_x, y), section_title, fill='#000000', font=font_section)
    y += 18 + 10
    
    y = draw_detail_line("Prix/diff.:", f"{data['price_per_play']:.2f} {data['currency_symbol']}", y)
    y = draw_detail_line("Nb diff.:", f"x {data['num_plays']}", y)
    y = draw_detail_line("Sous-total HT:", f"{data['total_price']:.2f} {data['currency_symbol']}", y)
    if data['vat_rate'] and data['vat_rate'] > 0:
        y = draw_detail_line(f"TVA ({data['vat_rate']:.1f}%):", f"{data['vat_amount']:.2f} {data['currency_symbol']}", y)
    
    draw_dashed_line(y)
    y += 3 + section_gap
    
    if data['vat_rate'] and data['vat_rate'] > 0:
        total_text = f"TOTAL TTC: {data['total_price_with_vat']:.2f} {data['currency_symbol']}"
    else:
        total_text = f"TOTAL: {data['total_price']:.2f} {data['currency_symbol']}"
    total_bbox = draw.textbbox((0, 0), total_text, font=font_total)
    total_box_height = 50
    total_box_y = y
    draw.rectangle([(padding, total_box_y), (width - padding, total_box_y + total_box_height)], outline='#000000', width=3)
    total_x = (width - (total_bbox[2] - total_bbox[0])) // 2
    total_y = total_box_y + (total_box_height - (total_bbox[3] - total_bbox[1])) // 2
    draw.text((total_x, total_y), total_text, fill='#000000', font=font_total)
    y = total_box_y + total_box_height + section_gap
    
    status_text = "*** EN ATTENTE DE VALIDATION ***"
    status_bbox = draw.textbbox((0, 0), status_text, font=font_status)
    status_box_height = 40
    status_box_y = y
    
    for i in range(0, width - 2 * padding, 12):
        draw.line([(padding + i, status_box_y), (padding + i + 6, status_box_y)], fill='#000000', width=1)
        draw.line([(padding + i, status_box_y + status_box_height), (padding + i + 6, status_box_y + status_box_height)], fill='#000000', width=1)
    draw.line([(padding, status_box_y), (padding, status_box_y + status_box_height)], fill='#000000', width=1)
    draw.line([(width - padding, status_box_y), (width - padding, status_box_y + status_box_height)], fill='#000000', width=1)
    
    status_x = (width - (status_bbox[2] - status_bbox[0])) // 2
    status_y = status_box_y + (status_box_height - (status_bbox[3] - status_bbox[1])) // 2
    draw.text((status_x, status_y), status_text, fill='#000000', font=font_status)
    y = status_box_y + status_box_height + section_gap
    
    draw_dashed_line(y)
    y += 3 + section_gap
    
    y = draw_detail_line("Client:", _truncate(data['client_name'], 16), y)
    y = draw_detail_line("Email:", _truncate(data['client_email'], 18), y)
    
    draw_dashed_line(y)
    y += 3 + section_gap
    
    if qr_base64:
        try:
            qr_data = base64.b64decode(qr_base64)
            qr_img = Image.open(io.BytesIO(qr_data))
            qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
            
            qr_x = padding
            img.paste(qr_img, (qr_x, y))
            
            msg_x = qr_x + qr_size + 10
            msg_lines = [
                "Merci pour votre",
                "reservation!",
                "Scannez le QR code",
                "pour passer une",
                "nouvelle commande."
            ]
            msg_y = y
            for line in msg_lines:
                draw.text((msg_x, msg_y), line, fill='#000000', font=font_small)
                msg_y += 14
            
            y += qr_size + 10
        except Exception:
            pass
    
    draw_dashed_line(y)
    y += 3 + section_gap
    
    footer_lines = [
        data['created_at'],
        "--------------------------------",
        "Shabaka AdScreen",
        "www.shabaka-adscreen.com"
    ]
    for line in footer_lines:
        line_bbox = draw.textbbox((0, 0), line, font=font_footer)
        line_x = (width - (line_bbox[2] - line_bbox[0])) // 2
        draw.text((line_x, y), line, fill='#000000', font=font_footer)
        y += 16
    
    return img


def generate_receipt_pdf(booking, screen, content, qr_base64=None):
    """Generate PDF receipt with thermal style design."""
    buffer = io.BytesIO()
    
    pdf_width = 200
    pdf_height = 500
    
    c = canvas.Canvas(buffer, pagesize=(pdf_width, pdf_height))
    
    data = _get_receipt_data(booking, screen, content)
    
    y = pdf_height - 20
    
    c.setFont("Courier-Bold", 10)
    org_name = data['org_name'][:25]
    c.drawCentredString(pdf_width / 2, y, org_name)
    y -= 12
    
    c.setFont("Courier", 8)
    screen_name = data['screen_name'][:25]
    c.drawCentredString(pdf_width / 2, y, screen_name)
    y -= 15
    
    c.line(10, y, pdf_width - 10, y)
    y -= 10
    
    c.setFont("Courier", 6)
    c.drawCentredString(pdf_width / 2, y, "N° RESERVATION")
    y -= 10
    c.setFont("Courier-Bold", 10)
    c.drawCentredString(pdf_width / 2, y, data['reservation_number'])
    y -= 15
    
    c.setStrokeColor(colors.black)
    c.setDash(3, 2)
    c.line(10, y, pdf_width - 10, y)
    c.setDash()
    y -= 12
    
    c.setFont("Courier-Bold", 7)
    c.drawCentredString(pdf_width / 2, y, "RECAPITULATIF")
    y -= 12
    
    c.setFont("Courier", 7)
    details = [
        ("Ecran:", _truncate(data['screen_name'], 15)),
        ("Etablis.:", _truncate(data['org_name'], 13)),
        ("Type:", data['content_type']),
        ("Creneau:", f"{data['slot_duration']}s"),
        ("Diffusions:", f"{data['num_plays']}x"),
        ("Debut:", data['start_date']),
    ]
    if data['end_date']:
        details.append(("Fin:", data['end_date']))
    
    for label, value in details:
        c.drawString(12, y, label)
        c.drawRightString(pdf_width - 12, y, value)
        y -= 10
    
    c.setDash(3, 2)
    c.line(10, y, pdf_width - 10, y)
    c.setDash()
    y -= 12
    
    c.setFont("Courier-Bold", 7)
    c.drawCentredString(pdf_width / 2, y, "TARIFICATION")
    y -= 12
    
    c.setFont("Courier", 7)
    c.drawString(12, y, "Prix/diff.:")
    c.drawRightString(pdf_width - 12, y, f"{data['price_per_play']:.2f} {data['currency_symbol']}")
    y -= 10
    c.drawString(12, y, "Nb diff.:")
    c.drawRightString(pdf_width - 12, y, f"x {data['num_plays']}")
    y -= 10
    c.drawString(12, y, "Sous-total HT:")
    c.drawRightString(pdf_width - 12, y, f"{data['total_price']:.2f} {data['currency_symbol']}")
    y -= 10
    if data['vat_rate'] and data['vat_rate'] > 0:
        c.drawString(12, y, f"TVA ({data['vat_rate']:.1f}%):")
        c.drawRightString(pdf_width - 12, y, f"{data['vat_amount']:.2f} {data['currency_symbol']}")
        y -= 10
    y -= 5
    
    c.setDash(3, 2)
    c.line(10, y, pdf_width - 10, y)
    c.setDash()
    y -= 15
    
    c.setFont("Courier-Bold", 10)
    if data['vat_rate'] and data['vat_rate'] > 0:
        total_text = f"TOTAL TTC: {data['total_price_with_vat']:.2f} {data['currency_symbol']}"
    else:
        total_text = f"TOTAL: {data['total_price']:.2f} {data['currency_symbol']}"
    c.rect(10, y - 5, pdf_width - 20, 18, stroke=True, fill=False)
    c.drawCentredString(pdf_width / 2, y, total_text)
    y -= 25
    
    c.setFont("Courier", 7)
    c.setDash(3, 2)
    c.rect(10, y - 5, pdf_width - 20, 15, stroke=True, fill=False)
    c.setDash()
    c.drawCentredString(pdf_width / 2, y, "*** EN ATTENTE DE VALIDATION ***")
    y -= 25
    
    c.setDash(3, 2)
    c.line(10, y, pdf_width - 10, y)
    c.setDash()
    y -= 12
    
    c.setFont("Courier", 7)
    c.drawString(12, y, "Client:")
    c.drawRightString(pdf_width - 12, y, _truncate(data['client_name'], 14))
    y -= 10
    c.drawString(12, y, "Email:")
    c.drawRightString(pdf_width - 12, y, _truncate(data['client_email'], 16))
    y -= 15
    
    if qr_base64:
        try:
            qr_data = base64.b64decode(qr_base64)
            qr_img = Image.open(io.BytesIO(qr_data))
            qr_size = 40
            c.drawImage(ImageReader(qr_img), 12, y - qr_size, width=qr_size, height=qr_size)
            
            c.setFont("Courier", 6)
            c.drawString(55, y - 10, "Merci pour votre")
            c.drawString(55, y - 18, "reservation!")
            c.drawString(55, y - 26, "Scannez le QR code")
            c.drawString(55, y - 34, "pour commander.")
            y -= qr_size + 10
        except Exception:
            pass
    
    c.setDash(3, 2)
    c.line(10, y, pdf_width - 10, y)
    c.setDash()
    y -= 12
    
    c.setFont("Courier", 6)
    c.drawCentredString(pdf_width / 2, y, data['created_at'])
    y -= 8
    c.drawCentredString(pdf_width / 2, y, "------------------------")
    y -= 8
    c.drawCentredString(pdf_width / 2, y, "Shabaka AdScreen")
    y -= 8
    c.drawCentredString(pdf_width / 2, y, "www.shabaka-adscreen.com")
    
    c.save()
    buffer.seek(0)
    return buffer


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
