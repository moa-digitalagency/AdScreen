import qrcode
import io
import base64
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


def generate_enhanced_qr_image(screen, booking_url, platform_name='Shabaka AdScreen'):
    """
    Generate a modern enhanced QR code image with establishment info.
    
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
        box_size=10,
        border=2,
    )
    qr.add_data(booking_url)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="#059669", back_color="white").convert('RGB')
    qr_size = qr_img.size[0]
    
    canvas_width = 480
    padding = 30
    header_height = 120
    qr_section_height = qr_size + 60
    cta_section_height = 80
    footer_height = 70
    canvas_height = header_height + qr_section_height + cta_section_height + footer_height
    
    canvas = Image.new('RGB', (canvas_width, canvas_height), '#f8fafc')
    draw = ImageDraw.Draw(canvas)
    
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
        subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        info_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
        cta_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
        footer_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
    except:
        title_font = ImageFont.load_default()
        subtitle_font = title_font
        info_font = title_font
        cta_font = title_font
        footer_font = title_font
        small_font = title_font
    
    for y in range(header_height):
        ratio = y / header_height
        r = int(5 + (16 - 5) * ratio)
        g = int(150 + (185 - 150) * ratio)
        b = int(105 + (129 - 105) * ratio)
        draw.line([(0, y), (canvas_width, y)], fill=(r, g, b))
    
    org_name = screen.organization.name if screen.organization else 'Etablissement'
    org_bbox = draw.textbbox((0, 0), org_name, font=title_font)
    org_x = (canvas_width - (org_bbox[2] - org_bbox[0])) // 2
    draw.text((org_x, 25), org_name, fill='white', font=title_font)
    
    screen_name = screen.name
    screen_bbox = draw.textbbox((0, 0), screen_name, font=subtitle_font)
    screen_x = (canvas_width - (screen_bbox[2] - screen_bbox[0])) // 2
    draw.text((screen_x, 62), screen_name, fill='#d1fae5', font=subtitle_font)
    
    resolution = f"{screen.resolution_width} x {screen.resolution_height} px"
    res_bbox = draw.textbbox((0, 0), resolution, font=info_font)
    res_x = (canvas_width - (res_bbox[2] - res_bbox[0])) // 2
    draw.text((res_x, 90), resolution, fill='#a7f3d0', font=info_font)
    
    qr_box_padding = 15
    qr_box_width = qr_size + (qr_box_padding * 2)
    qr_box_x = (canvas_width - qr_box_width) // 2
    qr_box_y = header_height + 20
    
    shadow_offset = 4
    draw.rounded_rectangle(
        [(qr_box_x + shadow_offset, qr_box_y + shadow_offset), 
         (qr_box_x + qr_box_width + shadow_offset, qr_box_y + qr_box_width + shadow_offset)],
        radius=16,
        fill='#e2e8f0'
    )
    
    draw.rounded_rectangle(
        [(qr_box_x, qr_box_y), (qr_box_x + qr_box_width, qr_box_y + qr_box_width)],
        radius=16,
        fill='white',
        outline='#e5e7eb',
        width=2
    )
    
    canvas.paste(qr_img, (qr_box_x + qr_box_padding, qr_box_y + qr_box_padding))
    
    cta_y = header_height + qr_section_height
    cta_box_width = canvas_width - 60
    cta_box_x = 30
    cta_box_height = 50
    
    draw.rounded_rectangle(
        [(cta_box_x, cta_y), (cta_box_x + cta_box_width, cta_y + cta_box_height)],
        radius=12,
        fill='#ecfdf5',
        outline='#10b981',
        width=2
    )
    
    cta_text = "Scannez pour reserver votre espace publicitaire"
    cta_bbox = draw.textbbox((0, 0), cta_text, font=cta_font)
    cta_text_x = (canvas_width - (cta_bbox[2] - cta_bbox[0])) // 2
    cta_text_y = cta_y + (cta_box_height - (cta_bbox[3] - cta_bbox[1])) // 2
    draw.text((cta_text_x, cta_text_y), cta_text, fill='#047857', font=cta_font)
    
    footer_y = canvas_height - footer_height
    draw.rectangle([(0, footer_y), (canvas_width, canvas_height)], fill='#1f2937')
    
    platform_bbox = draw.textbbox((0, 0), platform_name, font=footer_font)
    platform_x = (canvas_width - (platform_bbox[2] - platform_bbox[0])) // 2
    draw.text((platform_x, footer_y + 15), platform_name, fill='white', font=footer_font)
    
    url_text = "www.shabaka-adscreen.com"
    url_bbox = draw.textbbox((0, 0), url_text, font=small_font)
    url_x = (canvas_width - (url_bbox[2] - url_bbox[0])) // 2
    draw.text((url_x, footer_y + 42), url_text, fill='#9ca3af', font=small_font)
    
    buffer = io.BytesIO()
    canvas.save(buffer, format='PNG', quality=95)
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
