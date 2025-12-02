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


def generate_enhanced_qr_image(screen, booking_url, platform_name='Shabaka AdScreen'):
    """
    Generate a premium light-themed enhanced QR code image with establishment info.
    Features a clean, modern design with emerald gradient accents.
    
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
    
    qr_img_temp = qr.make_image(fill_color="#059669", back_color="white")
    qr_img = qr_img_temp.convert('RGBA')
    qr_size = qr_img.size[0]
    
    canvas_width = 480
    padding = 30
    header_height = 110
    qr_section_height = qr_size + 80
    info_section_height = 80
    cta_section_height = 60
    footer_height = 60
    canvas_height = header_height + qr_section_height + info_section_height + cta_section_height + footer_height
    
    color_emerald_500 = (16, 185, 129)
    color_teal_500 = (20, 184, 166)
    color_gray_50 = (249, 250, 251)
    color_gray_100 = (243, 244, 246)
    color_gray_200 = (229, 231, 235)
    color_gray_500 = (107, 114, 128)
    color_gray_700 = (55, 65, 81)
    color_gray_800 = (31, 41, 55)
    
    canvas = Image.new('RGBA', (canvas_width, canvas_height), '#ffffff')
    draw = ImageDraw.Draw(canvas)
    
    for y in range(header_height + 20):
        ratio = y / (header_height + 20)
        r = int(color_emerald_500[0] + (color_teal_500[0] - color_emerald_500[0]) * ratio)
        g = int(color_emerald_500[1] + (color_teal_500[1] - color_emerald_500[1]) * ratio)
        b = int(color_emerald_500[2] + (color_teal_500[2] - color_emerald_500[2]) * ratio)
        draw.line([(0, y), (canvas_width, y)], fill=(r, g, b))
    
    wave_points = []
    for x in range(canvas_width + 1):
        wave_y = header_height + int(12 * math.sin(x * 0.018))
        wave_points.append((x, wave_y))
    wave_points.append((canvas_width, canvas_height))
    wave_points.append((0, canvas_height))
    draw.polygon(wave_points, fill='#ffffff')
    
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        info_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        info_bold_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13)
        cta_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13)
        footer_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
    except:
        title_font = ImageFont.load_default()
        subtitle_font = title_font
        info_font = title_font
        info_bold_font = title_font
        cta_font = title_font
        footer_font = title_font
        small_font = title_font
    
    org_name = screen.organization.name if screen.organization else 'Etablissement'
    org_bbox = draw.textbbox((0, 0), org_name, font=title_font)
    org_x = (canvas_width - (org_bbox[2] - org_bbox[0])) // 2
    draw.text((org_x, 25), org_name, fill='white', font=title_font)
    
    screen_name = screen.name
    screen_bbox = draw.textbbox((0, 0), screen_name, font=subtitle_font)
    screen_x = (canvas_width - (screen_bbox[2] - screen_bbox[0])) // 2
    draw.text((screen_x, 58), screen_name, fill='#d1fae5', font=subtitle_font)
    
    location = screen.location or (screen.organization.city if screen.organization and hasattr(screen.organization, 'city') else '')
    if location:
        loc_text = location
        loc_bbox = draw.textbbox((0, 0), loc_text, font=small_font)
        loc_x = (canvas_width - (loc_bbox[2] - loc_bbox[0])) // 2
        draw.text((loc_x, 80), loc_text, fill='#a7f3d0', font=small_font)
    
    qr_container_size = qr_size + 40
    qr_container_x = (canvas_width - qr_container_size) // 2
    qr_container_y = header_height + 30
    
    shadow_offset = 6
    draw.rounded_rectangle(
        [(qr_container_x + shadow_offset, qr_container_y + shadow_offset), 
         (qr_container_x + qr_container_size + shadow_offset, qr_container_y + qr_container_size + shadow_offset)],
        radius=20,
        fill=color_gray_200
    )
    
    draw.rounded_rectangle(
        [(qr_container_x, qr_container_y), 
         (qr_container_x + qr_container_size, qr_container_y + qr_container_size)],
        radius=20,
        fill='white',
        outline=color_emerald_500,
        width=3
    )
    
    qr_x = qr_container_x + (qr_container_size - qr_size) // 2
    qr_y = qr_container_y + (qr_container_size - qr_size) // 2
    canvas.paste(qr_img, (qr_x, qr_y), qr_img)
    
    info_y = qr_container_y + qr_container_size + 15
    info_box_width = canvas_width - 60
    info_box_x = 30
    
    draw.rounded_rectangle(
        [(info_box_x, info_y), (info_box_x + info_box_width, info_y + 55)],
        radius=12,
        fill=color_gray_50,
        outline=color_gray_200,
        width=1
    )
    
    col_width = info_box_width // 3
    
    res_text = f"{screen.resolution_width}x{screen.resolution_height}"
    res_label = "Resolution"
    res_bbox = draw.textbbox((0, 0), res_text, font=info_bold_font)
    draw.text((info_box_x + (col_width - (res_bbox[2] - res_bbox[0])) // 2, info_y + 12), res_text, fill=color_gray_800, font=info_bold_font)
    res_label_bbox = draw.textbbox((0, 0), res_label, font=small_font)
    draw.text((info_box_x + (col_width - (res_label_bbox[2] - res_label_bbox[0])) // 2, info_y + 32), res_label, fill=color_gray_500, font=small_font)
    
    orient_text = screen.orientation.capitalize()
    orient_label = "Orientation"
    orient_bbox = draw.textbbox((0, 0), orient_text, font=info_bold_font)
    draw.text((info_box_x + col_width + (col_width - (orient_bbox[2] - orient_bbox[0])) // 2, info_y + 12), orient_text, fill=color_gray_800, font=info_bold_font)
    orient_label_bbox = draw.textbbox((0, 0), orient_label, font=small_font)
    draw.text((info_box_x + col_width + (col_width - (orient_label_bbox[2] - orient_label_bbox[0])) // 2, info_y + 32), orient_label, fill=color_gray_500, font=small_font)
    
    type_parts = []
    if screen.accepts_images:
        type_parts.append("IMG")
    if screen.accepts_videos:
        type_parts.append("VID")
    type_text = " + ".join(type_parts) if type_parts else "Tous"
    type_label = "Format"
    type_bbox = draw.textbbox((0, 0), type_text, font=info_bold_font)
    draw.text((info_box_x + 2 * col_width + (col_width - (type_bbox[2] - type_bbox[0])) // 2, info_y + 12), type_text, fill=color_gray_800, font=info_bold_font)
    type_label_bbox = draw.textbbox((0, 0), type_label, font=small_font)
    draw.text((info_box_x + 2 * col_width + (col_width - (type_label_bbox[2] - type_label_bbox[0])) // 2, info_y + 32), type_label, fill=color_gray_500, font=small_font)
    
    cta_y = info_y + 70
    cta_box_width = canvas_width - 80
    cta_box_x = 40
    cta_box_height = 42
    
    for y_offset in range(cta_box_height):
        ratio = y_offset / cta_box_height
        r = int(color_emerald_500[0] + (color_teal_500[0] - color_emerald_500[0]) * ratio)
        g = int(color_emerald_500[1] + (color_teal_500[1] - color_emerald_500[1]) * ratio)
        b = int(color_emerald_500[2] + (color_teal_500[2] - color_emerald_500[2]) * ratio)
        draw.line([(cta_box_x, cta_y + y_offset), (cta_box_x + cta_box_width, cta_y + y_offset)], fill=(r, g, b))
    
    draw.rounded_rectangle(
        [(cta_box_x, cta_y), (cta_box_x + cta_box_width, cta_y + cta_box_height)],
        radius=cta_box_height // 2,
        outline=None,
        width=0
    )
    
    cta_text = "Scannez pour reserver votre espace"
    cta_bbox = draw.textbbox((0, 0), cta_text, font=cta_font)
    cta_text_x = (canvas_width - (cta_bbox[2] - cta_bbox[0])) // 2
    cta_text_y = cta_y + (cta_box_height - (cta_bbox[3] - cta_bbox[1])) // 2
    draw.text((cta_text_x, cta_text_y), cta_text, fill='white', font=cta_font)
    
    footer_y = canvas_height - footer_height
    
    draw.rectangle([(0, footer_y), (canvas_width, canvas_height)], fill=color_gray_100)
    
    for x in range(canvas_width):
        ratio = x / canvas_width
        r = int(color_emerald_500[0] + (color_teal_500[0] - color_emerald_500[0]) * ratio)
        g = int(color_emerald_500[1] + (color_teal_500[1] - color_emerald_500[1]) * ratio)
        b = int(color_emerald_500[2] + (color_teal_500[2] - color_emerald_500[2]) * ratio)
        draw.line([(x, footer_y), (x, footer_y + 3)], fill=(r, g, b))
    
    platform_bbox = draw.textbbox((0, 0), platform_name, font=footer_font)
    platform_x = (canvas_width - (platform_bbox[2] - platform_bbox[0])) // 2
    draw.text((platform_x, footer_y + 15), platform_name, fill=color_gray_800, font=footer_font)
    
    url_text = "www.shabaka-adscreen.com"
    url_bbox = draw.textbbox((0, 0), url_text, font=small_font)
    url_x = (canvas_width - (url_bbox[2] - url_bbox[0])) // 2
    draw.text((url_x, footer_y + 38), url_text, fill=color_gray_500, font=small_font)
    
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
