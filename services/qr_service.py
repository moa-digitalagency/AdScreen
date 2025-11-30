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


def generate_enhanced_qr_image(screen, booking_url, platform_name='AdScreen'):
    """
    Generate an enhanced QR code image with establishment info.
    
    Args:
        screen: Screen model instance
        booking_url: The booking URL to encode
        platform_name: Name of the platform
    
    Returns:
        bytes: PNG image data
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(booking_url)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="#059669", back_color="white").convert('RGB')
    qr_size = qr_img.size[0]
    
    canvas_width = max(400, qr_size + 60)
    header_height = 100
    footer_height = 80
    qr_section_height = qr_size + 40
    info_height = 60
    canvas_height = header_height + qr_section_height + info_height + footer_height
    
    canvas = Image.new('RGB', (canvas_width, canvas_height), 'white')
    draw = ImageDraw.Draw(canvas)
    
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        info_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        footer_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    except:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        info_font = ImageFont.load_default()
        footer_font = ImageFont.load_default()
    
    draw.rectangle([(0, 0), (canvas_width, header_height)], fill='#059669')
    
    org_name = screen.organization.name if screen.organization else 'Etablissement'
    org_bbox = draw.textbbox((0, 0), org_name, font=title_font)
    org_x = (canvas_width - (org_bbox[2] - org_bbox[0])) // 2
    draw.text((org_x, 20), org_name, fill='white', font=title_font)
    
    screen_name = screen.name
    screen_bbox = draw.textbbox((0, 0), screen_name, font=subtitle_font)
    screen_x = (canvas_width - (screen_bbox[2] - screen_bbox[0])) // 2
    draw.text((screen_x, 55), screen_name, fill='white', font=subtitle_font)
    
    resolution = f"{screen.resolution_width}x{screen.resolution_height}"
    res_bbox = draw.textbbox((0, 0), resolution, font=info_font)
    res_x = (canvas_width - (res_bbox[2] - res_bbox[0])) // 2
    draw.text((res_x, 78), resolution, fill='#d1fae5', font=info_font)
    
    qr_x = (canvas_width - qr_size) // 2
    qr_y = header_height + 20
    canvas.paste(qr_img, (qr_x, qr_y))
    
    cta_text = "Scannez pour reserver un canal publicitaire"
    cta_bbox = draw.textbbox((0, 0), cta_text, font=info_font)
    cta_x = (canvas_width - (cta_bbox[2] - cta_bbox[0])) // 2
    cta_y = header_height + qr_section_height + 10
    draw.text((cta_x, cta_y), cta_text, fill='#374151', font=info_font)
    
    footer_y = canvas_height - footer_height
    draw.rectangle([(0, footer_y), (canvas_width, canvas_height)], fill='#1f2937')
    
    platform_bbox = draw.textbbox((0, 0), platform_name, font=footer_font)
    platform_x = (canvas_width - (platform_bbox[2] - platform_bbox[0])) // 2
    draw.text((platform_x, footer_y + 30), platform_name, fill='white', font=footer_font)
    
    buffer = io.BytesIO()
    canvas.save(buffer, format='PNG', quality=95)
    buffer.seek(0)
    
    return buffer.getvalue()


def generate_enhanced_qr_base64(screen, booking_url, platform_name='AdScreen'):
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
