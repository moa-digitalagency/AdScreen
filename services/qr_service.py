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


def draw_rounded_rectangle(draw, coords, radius, fill=None, outline=None, width=1):
    """Draw a rounded rectangle."""
    x1, y1, x2, y2 = coords
    draw.rounded_rectangle(coords, radius=radius, fill=fill, outline=outline, width=width)


def draw_gradient_rectangle(canvas, coords, color_start, color_end, direction='vertical'):
    """Draw a gradient rectangle on the canvas."""
    x1, y1, x2, y2 = coords
    draw = ImageDraw.Draw(canvas)
    
    if direction == 'vertical':
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


def draw_decorative_circles(draw, canvas_width, header_height):
    """Draw decorative floating circles in the header."""
    circles = [
        (40, 30, 25, (255, 255, 255, 30)),
        (canvas_width - 60, 50, 35, (255, 255, 255, 20)),
        (100, 90, 18, (255, 255, 255, 25)),
        (canvas_width - 100, 25, 22, (255, 255, 255, 15)),
    ]
    for x, y, r, color in circles:
        if y < header_height:
            draw.ellipse([(x-r, y-r), (x+r, y+r)], fill=color[:3], outline=None)


def generate_enhanced_qr_image(screen, booking_url, platform_name='Shabaka AdScreen'):
    """
    Generate a premium modern enhanced QR code image with establishment info.
    Features a glassmorphism-inspired design with elegant gradients.
    
    Args:
        screen: Screen model instance
        booking_url: The booking URL to encode
        platform_name: Name of the platform
    
    Returns:
        bytes: PNG image data
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=8,
        border=2,
    )
    qr.add_data(booking_url)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="#1e293b", back_color="white").convert('RGBA')
    qr_size = qr_img.size[0]
    
    canvas_width = 520
    padding = 35
    header_height = 140
    qr_section_height = qr_size + 100
    info_section_height = 90
    cta_section_height = 70
    footer_height = 80
    canvas_height = header_height + qr_section_height + info_section_height + cta_section_height + footer_height
    
    canvas = Image.new('RGBA', (canvas_width, canvas_height), '#ffffff')
    draw = ImageDraw.Draw(canvas)
    
    color_primary_start = (16, 185, 129)
    color_primary_end = (5, 150, 105)
    color_accent = (52, 211, 153)
    color_dark = (15, 23, 42)
    
    for y in range(header_height + 30):
        ratio = y / (header_height + 30)
        curve_ratio = math.sin(ratio * math.pi / 2)
        r = int(color_primary_start[0] + (color_primary_end[0] - color_primary_start[0]) * curve_ratio)
        g = int(color_primary_start[1] + (color_primary_end[1] - color_primary_start[1]) * curve_ratio)
        b = int(color_primary_start[2] + (color_primary_end[2] - color_primary_start[2]) * curve_ratio)
        draw.line([(0, y), (canvas_width, y)], fill=(r, g, b))
    
    wave_points = []
    for x in range(canvas_width + 1):
        wave_y = header_height + 15 + int(15 * math.sin(x * 0.02))
        wave_points.append((x, wave_y))
    wave_points.append((canvas_width, canvas_height))
    wave_points.append((0, canvas_height))
    draw.polygon(wave_points, fill='#ffffff')
    
    draw_decorative_circles(draw, canvas_width, header_height)
    
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        info_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
        info_bold_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13)
        cta_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        footer_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
        icon_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except:
        title_font = ImageFont.load_default()
        subtitle_font = title_font
        info_font = title_font
        info_bold_font = title_font
        cta_font = title_font
        footer_font = title_font
        small_font = title_font
        icon_font = title_font
    
    org_name = screen.organization.name if screen.organization else 'Etablissement'
    org_bbox = draw.textbbox((0, 0), org_name, font=title_font)
    org_x = (canvas_width - (org_bbox[2] - org_bbox[0])) // 2
    
    draw.text((org_x + 2, 32), org_name, fill=(255, 255, 255, 100), font=title_font)
    draw.text((org_x, 30), org_name, fill='white', font=title_font)
    
    screen_name = screen.name
    screen_bbox = draw.textbbox((0, 0), screen_name, font=subtitle_font)
    screen_x = (canvas_width - (screen_bbox[2] - screen_bbox[0])) // 2
    draw.text((screen_x, 72), screen_name, fill='#e0e7ff', font=subtitle_font)
    
    location = screen.location or screen.organization.name if screen.organization else ''
    if location:
        loc_text = f"📍 {location}"
        loc_bbox = draw.textbbox((0, 0), loc_text, font=small_font)
        loc_x = (canvas_width - (loc_bbox[2] - loc_bbox[0])) // 2
        draw.text((loc_x, 98), loc_text, fill='#c7d2fe', font=small_font)
    
    qr_container_size = qr_size + 50
    qr_container_x = (canvas_width - qr_container_size) // 2
    qr_container_y = header_height + 35
    
    shadow_layers = [(8, '#e2e8f0'), (5, '#e5e7eb'), (3, '#f1f5f9')]
    for offset, color in shadow_layers:
        draw.rounded_rectangle(
            [(qr_container_x + offset, qr_container_y + offset), 
             (qr_container_x + qr_container_size + offset, qr_container_y + qr_container_size + offset)],
            radius=24,
            fill=color
        )
    
    draw.rounded_rectangle(
        [(qr_container_x, qr_container_y), 
         (qr_container_x + qr_container_size, qr_container_y + qr_container_size)],
        radius=24,
        fill='white',
        outline='#e5e7eb',
        width=2
    )
    
    corner_size = 25
    corner_thickness = 4
    corners = [
        (qr_container_x + 10, qr_container_y + 10),
        (qr_container_x + qr_container_size - 10 - corner_size, qr_container_y + 10),
        (qr_container_x + 10, qr_container_y + qr_container_size - 10 - corner_size),
        (qr_container_x + qr_container_size - 10 - corner_size, qr_container_y + qr_container_size - 10 - corner_size),
    ]
    
    for i, (cx, cy) in enumerate(corners):
        if i == 0:
            draw.line([(cx, cy), (cx + corner_size, cy)], fill='#10b981', width=corner_thickness)
            draw.line([(cx, cy), (cx, cy + corner_size)], fill='#10b981', width=corner_thickness)
        elif i == 1:
            draw.line([(cx, cy), (cx + corner_size, cy)], fill='#059669', width=corner_thickness)
            draw.line([(cx + corner_size, cy), (cx + corner_size, cy + corner_size)], fill='#059669', width=corner_thickness)
        elif i == 2:
            draw.line([(cx, cy), (cx, cy + corner_size)], fill='#34d399', width=corner_thickness)
            draw.line([(cx, cy + corner_size), (cx + corner_size, cy + corner_size)], fill='#34d399', width=corner_thickness)
        else:
            draw.line([(cx + corner_size, cy), (cx + corner_size, cy + corner_size)], fill='#047857', width=corner_thickness)
            draw.line([(cx, cy + corner_size), (cx + corner_size, cy + corner_size)], fill='#047857', width=corner_thickness)
    
    qr_x = qr_container_x + (qr_container_size - qr_size) // 2
    qr_y = qr_container_y + (qr_container_size - qr_size) // 2
    canvas.paste(qr_img, (qr_x, qr_y), qr_img)
    
    info_y = qr_container_y + qr_container_size + 20
    info_box_width = canvas_width - 70
    info_box_x = 35
    
    draw.rounded_rectangle(
        [(info_box_x, info_y), (info_box_x + info_box_width, info_y + 65)],
        radius=14,
        fill='#f8fafc',
        outline='#e2e8f0',
        width=1
    )
    
    col_width = info_box_width // 3
    
    res_icon = "🖥"
    res_text = f"{screen.resolution_width}x{screen.resolution_height}"
    res_label = "Resolution"
    draw.text((info_box_x + col_width // 2 - 10, info_y + 10), res_icon, fill='#10b981', font=icon_font)
    res_bbox = draw.textbbox((0, 0), res_text, font=info_bold_font)
    draw.text((info_box_x + (col_width - (res_bbox[2] - res_bbox[0])) // 2, info_y + 30), res_text, fill='#1e293b', font=info_bold_font)
    res_label_bbox = draw.textbbox((0, 0), res_label, font=small_font)
    draw.text((info_box_x + (col_width - (res_label_bbox[2] - res_label_bbox[0])) // 2, info_y + 48), res_label, fill='#64748b', font=small_font)
    
    orient_icon = "📐"
    orient_text = screen.orientation.capitalize()
    orient_label = "Orientation"
    draw.text((info_box_x + col_width + col_width // 2 - 10, info_y + 10), orient_icon, fill='#059669', font=icon_font)
    orient_bbox = draw.textbbox((0, 0), orient_text, font=info_bold_font)
    draw.text((info_box_x + col_width + (col_width - (orient_bbox[2] - orient_bbox[0])) // 2, info_y + 30), orient_text, fill='#1e293b', font=info_bold_font)
    orient_label_bbox = draw.textbbox((0, 0), orient_label, font=small_font)
    draw.text((info_box_x + col_width + (col_width - (orient_label_bbox[2] - orient_label_bbox[0])) // 2, info_y + 48), orient_label, fill='#64748b', font=small_font)
    
    type_icon = "📺"
    type_parts = []
    if screen.accepts_images:
        type_parts.append("IMG")
    if screen.accepts_videos:
        type_parts.append("VID")
    type_text = " + ".join(type_parts) if type_parts else "Tous"
    type_label = "Format"
    draw.text((info_box_x + 2 * col_width + col_width // 2 - 10, info_y + 10), type_icon, fill='#10b981', font=icon_font)
    type_bbox = draw.textbbox((0, 0), type_text, font=info_bold_font)
    draw.text((info_box_x + 2 * col_width + (col_width - (type_bbox[2] - type_bbox[0])) // 2, info_y + 30), type_text, fill='#1e293b', font=info_bold_font)
    type_label_bbox = draw.textbbox((0, 0), type_label, font=small_font)
    draw.text((info_box_x + 2 * col_width + (col_width - (type_label_bbox[2] - type_label_bbox[0])) // 2, info_y + 48), type_label, fill='#64748b', font=small_font)
    
    cta_y = info_y + 80
    cta_box_width = canvas_width - 80
    cta_box_x = 40
    cta_box_height = 50
    
    for y_offset in range(cta_box_height):
        ratio = y_offset / cta_box_height
        r = int(16 + (52 - 16) * ratio)
        g = int(185 + (211 - 185) * ratio)
        b = int(129 + (153 - 129) * ratio)
        draw.line([(cta_box_x, cta_y + y_offset), (cta_box_x + cta_box_width, cta_y + y_offset)], fill=(r, g, b))
    
    draw.rounded_rectangle(
        [(cta_box_x, cta_y), (cta_box_x + cta_box_width, cta_y + cta_box_height)],
        radius=14,
        outline='#059669',
        width=0
    )
    
    mask = Image.new('L', (cta_box_width, cta_box_height), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([(0, 0), (cta_box_width, cta_box_height)], radius=14, fill=255)
    
    cta_text = "📱 Scannez pour reserver votre espace pub"
    cta_bbox = draw.textbbox((0, 0), cta_text, font=cta_font)
    cta_text_x = (canvas_width - (cta_bbox[2] - cta_bbox[0])) // 2
    cta_text_y = cta_y + (cta_box_height - (cta_bbox[3] - cta_bbox[1])) // 2
    draw.text((cta_text_x, cta_text_y), cta_text, fill='white', font=cta_font)
    
    footer_y = canvas_height - footer_height
    
    for y in range(footer_y, canvas_height):
        ratio = (y - footer_y) / footer_height
        r = int(15 + (30 - 15) * ratio)
        g = int(23 + (41 - 23) * ratio)
        b = int(42 + (59 - 42) * ratio)
        draw.line([(0, y), (canvas_width, y)], fill=(r, g, b))
    
    draw.rectangle([(0, footer_y), (canvas_width, footer_y + 3)], fill='#10b981')
    
    platform_bbox = draw.textbbox((0, 0), platform_name, font=footer_font)
    platform_x = (canvas_width - (platform_bbox[2] - platform_bbox[0])) // 2
    draw.text((platform_x, footer_y + 20), platform_name, fill='white', font=footer_font)
    
    url_text = "www.shabaka-adscreen.com"
    url_bbox = draw.textbbox((0, 0), url_text, font=small_font)
    url_x = (canvas_width - (url_bbox[2] - url_bbox[0])) // 2
    draw.text((url_x, footer_y + 50), url_text, fill='#94a3b8', font=small_font)
    
    canvas_rgb = canvas.convert('RGB')
    
    buffer = io.BytesIO()
    canvas_rgb.save(buffer, format='PNG', quality=95)
    buffer.seek(0)
    
    return buffer.getvalue()


def generate_enhanced_qr_base64(screen, booking_url, platform_name='Shabaka AdScreen'):
    """
    Generate an enhanced QR code as a base64-encoded string.
    
    Args:
        screen: Screen model instance
        booking_url: The booking URL to encode
        platform_name: Name of the platform
    
    Returns:
        str: Base64-encoded PNG image
    """
    img_data = generate_enhanced_qr_image(screen, booking_url, platform_name)
    return base64.b64encode(img_data).decode()


def generate_screen_booking_url(screen, external=True):
    """
    Generate the booking URL for a screen.
    
    Args:
        screen: Screen model instance
        external: Whether to generate an external URL
    
    Returns:
        str: The booking URL
    """
    return url_for('booking.screen_booking', screen_code=screen.unique_code, _external=external)
