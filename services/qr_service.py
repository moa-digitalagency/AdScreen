import qrcode
import io
import base64
import math
from PIL import Image, ImageDraw, ImageFont
from flask import url_for


def generate_qr_code(data, box_size=10, border=4):
    """
    Generate a QR code image.
    
    Args:
        data: The data to encode in the QR code
        box_size: Size of each box in the QR code
        border: Border size around the QR code
    
    Returns:
        bytes: PNG image data
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return buffer.getvalue()


def generate_qr_base64(data, box_size=10, border=4):
    """
    Generate a QR code as a base64-encoded string.
    
    Args:
        data: The data to encode in the QR code
        box_size: Size of each box in the QR code
        border: Border size around the QR code
    
    Returns:
        str: Base64-encoded PNG image
    """
    img_data = generate_qr_code(data, box_size, border)
    return base64.b64encode(img_data).decode()


def generate_enhanced_qr_base64(screen, booking_url, platform_name='Shabaka AdScreen'):
    """
    Generate enhanced QR code as base64.
    
    Args:
        screen: Screen model instance
        booking_url: The booking URL to encode
        platform_name: Name of the platform
    
    Returns:
        str: Base64-encoded PNG image
    """
    img_data = generate_enhanced_qr_image(screen, booking_url, platform_name)
    return base64.b64encode(img_data).decode()


def draw_gradient_rect(draw, x1, y1, x2, y2, color_start, color_end, vertical=True):
    """Draw a smooth gradient rectangle."""
    if vertical:
        for y in range(y1, y2):
            ratio = (y - y1) / max(1, (y2 - y1))
            r = int(color_start[0] + (color_end[0] - color_start[0]) * ratio)
            g = int(color_start[1] + (color_end[1] - color_start[1]) * ratio)
            b = int(color_start[2] + (color_end[2] - color_start[2]) * ratio)
            draw.line([(x1, y), (x2, y)], fill=(r, g, b))
    else:
        for x in range(x1, x2):
            ratio = (x - x1) / max(1, (x2 - x1))
            r = int(color_start[0] + (color_end[0] - color_start[0]) * ratio)
            g = int(color_start[1] + (color_end[1] - color_start[1]) * ratio)
            b = int(color_start[2] + (color_end[2] - color_start[2]) * ratio)
            draw.line([(x, y1), (x, y2)], fill=(r, g, b))


def draw_rounded_rect(draw, coords, radius, fill=None, outline=None, width=1):
    """Draw a rounded rectangle."""
    x1, y1, x2, y2 = coords
    diameter = radius * 2
    
    draw.rectangle([(x1 + radius, y1), (x2 - radius, y2)], fill=fill)
    draw.rectangle([(x1, y1 + radius), (x2, y2 - radius)], fill=fill)
    
    draw.ellipse([(x1, y1), (x1 + diameter, y1 + diameter)], fill=fill)
    draw.ellipse([(x2 - diameter, y1), (x2, y1 + diameter)], fill=fill)
    draw.ellipse([(x1, y2 - diameter), (x1 + diameter, y2)], fill=fill)
    draw.ellipse([(x2 - diameter, y2 - diameter), (x2, y2)], fill=fill)
    
    if outline:
        draw.arc([(x1, y1), (x1 + diameter, y1 + diameter)], 180, 270, fill=outline, width=width)
        draw.arc([(x2 - diameter, y1), (x2, y1 + diameter)], 270, 360, fill=outline, width=width)
        draw.arc([(x1, y2 - diameter), (x1 + diameter, y2)], 90, 180, fill=outline, width=width)
        draw.arc([(x2 - diameter, y2 - diameter), (x2, y2)], 0, 90, fill=outline, width=width)
        draw.line([(x1 + radius, y1), (x2 - radius, y1)], fill=outline, width=width)
        draw.line([(x1 + radius, y2), (x2 - radius, y2)], fill=outline, width=width)
        draw.line([(x1, y1 + radius), (x1, y2 - radius)], fill=outline, width=width)
        draw.line([(x2, y1 + radius), (x2, y2 - radius)], fill=outline, width=width)


def generate_enhanced_qr_image(screen, booking_url, platform_name='Shabaka AdScreen'):
    """
    Generate a professional credit card style QR code image in portrait.
    Credit card ratio: 85.6mm x 53.98mm = ~1.586 ratio
    Format portrait: height > width
    QR code takes 50% of image, positioned towards bottom.
    
    Args:
        screen: Screen model instance
        booking_url: The booking URL to encode
        platform_name: Name of the platform
    
    Returns:
        bytes: PNG image data
    """
    card_ratio = 1.586
    base_width = 600
    base_height = int(base_width * card_ratio)
    
    canvas_width = base_width
    canvas_height = base_height
    
    emerald_500 = (16, 185, 129)
    emerald_600 = (5, 150, 105)
    emerald_700 = (4, 120, 87)
    emerald_50 = (236, 253, 245)
    emerald_100 = (209, 250, 229)
    teal_500 = (20, 184, 166)
    text_dark = (15, 23, 42)
    text_white = (255, 255, 255)
    
    canvas = Image.new('RGB', (canvas_width, canvas_height), '#ffffff')
    draw = ImageDraw.Draw(canvas)
    
    header_height = int(canvas_height * 0.20)
    draw_gradient_rect(draw, 0, 0, canvas_width, header_height, emerald_500, emerald_700, vertical=True)
    
    wave_height = int(canvas_height * 0.03)
    for x in range(canvas_width):
        wave_y = header_height + int(math.sin(x / 30) * wave_height * 0.5)
        ratio = x / canvas_width
        r = int(emerald_500[0] + (teal_500[0] - emerald_500[0]) * ratio)
        g = int(emerald_500[1] + (teal_500[1] - emerald_500[1]) * ratio)
        b = int(emerald_500[2] + (teal_500[2] - emerald_500[2]) * ratio)
        draw.line([(x, header_height), (x, wave_y + wave_height)], fill=(r, g, b))
    
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(canvas_width * 0.07))
        subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(canvas_width * 0.04))
        label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(canvas_width * 0.05))
        info_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(canvas_width * 0.035))
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(canvas_width * 0.028))
        footer_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(canvas_width * 0.032))
    except:
        title_font = ImageFont.load_default()
        subtitle_font = title_font
        label_font = title_font
        info_font = title_font
        small_font = title_font
        footer_font = title_font
    
    title_bbox = draw.textbbox((0, 0), platform_name, font=title_font)
    title_x = (canvas_width - (title_bbox[2] - title_bbox[0])) // 2
    title_y = int(header_height * 0.25)
    draw.text((title_x, title_y), platform_name, fill=text_white, font=title_font)
    
    tagline = "Votre espace publicitaire"
    tagline_bbox = draw.textbbox((0, 0), tagline, font=subtitle_font)
    tagline_x = (canvas_width - (tagline_bbox[2] - tagline_bbox[0])) // 2
    tagline_y = title_y + (title_bbox[3] - title_bbox[1]) + 10
    draw.text((tagline_x, tagline_y), tagline, fill=(255, 255, 255, 200), font=subtitle_font)
    
    content_start_y = header_height + wave_height + int(canvas_height * 0.02)
    
    org_name = screen.organization.name if screen.organization else 'Établissement'
    org_bbox = draw.textbbox((0, 0), org_name, font=label_font)
    org_x = (canvas_width - (org_bbox[2] - org_bbox[0])) // 2
    org_y = content_start_y
    draw.text((org_x, org_y), org_name, fill=text_dark, font=label_font)
    
    line_width = min(int((org_bbox[2] - org_bbox[0]) * 0.6), canvas_width - 100)
    line_x = (canvas_width - line_width) // 2
    line_y = org_y + (org_bbox[3] - org_bbox[1]) + 8
    draw.rounded_rectangle([(line_x, line_y), (line_x + line_width, line_y + 3)], radius=2, fill=emerald_500)
    
    screen_name = screen.name
    screen_bbox = draw.textbbox((0, 0), screen_name, font=info_font)
    screen_x = (canvas_width - (screen_bbox[2] - screen_bbox[0])) // 2
    screen_y = line_y + 15
    draw.text((screen_x, screen_y), screen_name, fill=emerald_600, font=info_font)
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(booking_url)
    qr.make(fit=True)
    
    qr_img_temp = qr.make_image(fill_color="#059669", back_color="white").convert('RGB')
    
    qr_section_height = int(canvas_height * 0.50)
    qr_section_start_y = canvas_height - qr_section_height
    
    qr_size = int(min(canvas_width, qr_section_height) * 0.55)
    
    try:
        qr_img = qr_img_temp.resize((qr_size, qr_size), Image.LANCZOS)
    except AttributeError:
        qr_img = qr_img_temp.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
    
    qr_bg_padding = int(qr_size * 0.12)
    qr_bg_size = qr_size + qr_bg_padding * 2
    qr_bg_x = (canvas_width - qr_bg_size) // 2
    qr_bg_y = qr_section_start_y + int((qr_section_height - qr_bg_size - 60) / 2)
    
    draw.rounded_rectangle(
        [(qr_bg_x - 5, qr_bg_y - 5), (qr_bg_x + qr_bg_size + 5, qr_bg_y + qr_bg_size + 5)],
        radius=20,
        fill=emerald_100,
        outline=emerald_500,
        width=3
    )
    
    draw.rectangle(
        [(qr_bg_x + qr_bg_padding - 5, qr_bg_y + qr_bg_padding - 5), 
         (qr_bg_x + qr_bg_padding + qr_size + 5, qr_bg_y + qr_bg_padding + qr_size + 5)],
        fill='#ffffff'
    )
    
    qr_x = qr_bg_x + qr_bg_padding
    qr_y = qr_bg_y + qr_bg_padding
    canvas.paste(qr_img, (qr_x, qr_y))
    
    scan_text = "Scannez pour réserver"
    scan_bbox = draw.textbbox((0, 0), scan_text, font=info_font)
    scan_x = (canvas_width - (scan_bbox[2] - scan_bbox[0])) // 2
    scan_y = qr_bg_y + qr_bg_size + 15
    draw.text((scan_x, scan_y), scan_text, fill=emerald_600, font=info_font)
    
    footer_height = int(canvas_height * 0.08)
    footer_y = canvas_height - footer_height
    draw_gradient_rect(draw, 0, footer_y, canvas_width, canvas_height, emerald_600, emerald_700, vertical=True)
    
    website_url = "www.shabaka-adscreen.com"
    website_bbox = draw.textbbox((0, 0), website_url, font=footer_font)
    website_x = (canvas_width - (website_bbox[2] - website_bbox[0])) // 2
    website_y = footer_y + (footer_height - (website_bbox[3] - website_bbox[1])) // 2
    draw.text((website_x, website_y), website_url, fill=text_white, font=footer_font)
    
    canvas = canvas.convert('RGB')
    
    buffer = io.BytesIO()
    canvas.save(buffer, format='PNG', quality=95)
    buffer.seek(0)
    
    return buffer.getvalue()
