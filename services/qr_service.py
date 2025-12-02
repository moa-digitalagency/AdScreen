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


def draw_dotted_line(draw, start, end, color, width=2, spacing=8):
    """Draw a dotted line."""
    x1, y1 = start
    x2, y2 = end
    distance = math.sqrt((x2-x1)**2 + (y2-y1)**2)
    num_dots = int(distance / spacing)
    
    for i in range(num_dots):
        t = i / max(1, num_dots)
        x = int(x1 + (x2 - x1) * t)
        y = int(y1 + (y2 - y1) * t)
        draw.ellipse([(x-width, y-width), (x+width, y+width)], fill=color)


def generate_enhanced_qr_image(screen, booking_url, platform_name='Shabaka AdScreen'):
    """
    Generate a professional light-theme enhanced QR code image.
    Features large visible QR code, emerald gradients, no blocking elements.
    
    Args:
        screen: Screen model instance
        booking_url: The booking URL to encode
        platform_name: Name of the platform
    
    Returns:
        bytes: PNG image data
    """
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(booking_url)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="#059669", back_color="white").convert('RGBA')
    qr_size = qr_img.size[0]
    
    # Professional proportions - portrait layout
    canvas_width = 600
    canvas_height = 900
    padding = 40
    
    # Light theme background
    canvas = Image.new('RGB', (canvas_width, canvas_height), '#ffffff')
    draw = ImageDraw.Draw(canvas)
    
    # Emerald gradient colors
    gradient_start = (16, 185, 129)  # #10b981
    gradient_end = (20, 184, 166)    # #14b8a6
    accent_light = (209, 250, 229)   # #d1fae5
    accent_dark = (5, 150, 105)      # #059669
    
    # Decorative dotted border at top
    for i in range(0, canvas_width, 15):
        draw.ellipse([(i, 15), (i+4, 19)], fill=gradient_start)
    
    # Subtle gradient header bar
    header_height = 80
    for y in range(header_height):
        ratio = y / header_height
        r = int(gradient_start[0] + (accent_light[0] - gradient_start[0]) * ratio)
        g = int(gradient_start[1] + (accent_light[1] - gradient_start[1]) * ratio)
        b = int(gradient_start[2] + (accent_light[2] - gradient_start[2]) * ratio)
        draw.line([(0, y), (canvas_width, y)], fill=(r, g, b))
    
    # Platform name in header
    try:
        header_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        qr_label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
        info_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        footer_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    except:
        header_font = ImageFont.load_default()
        qr_label_font = header_font
        info_font = header_font
        footer_font = header_font
    
    # Platform name centered in header
    platform_bbox = draw.textbbox((0, 0), platform_name, font=header_font)
    platform_x = (canvas_width - (platform_bbox[2] - platform_bbox[0])) // 2
    draw.text((platform_x, 25), platform_name, fill='#ffffff', font=header_font)
    
    # QR Code section - LARGE AND CENTERED
    qr_label_y = header_height + 30
    qr_label_bbox = draw.textbbox((0, 0), "Scannez pour réserver", font=qr_label_font)
    qr_label_x = (canvas_width - (qr_label_bbox[2] - qr_label_bbox[0])) // 2
    draw.text((qr_label_x, qr_label_y), "Scannez pour réserver", fill=accent_dark, font=qr_label_font)
    
    # QR code placement - LARGE AND VISIBLE
    qr_bg_size = qr_size + 60
    qr_bg_x = (canvas_width - qr_bg_size) // 2
    qr_bg_y = qr_label_y + 50
    
    # Light background for QR
    draw.rectangle(
        [(qr_bg_x, qr_bg_y), (qr_bg_x + qr_bg_size, qr_bg_y + qr_bg_size)],
        fill=accent_light,
        outline=gradient_start,
        width=2
    )
    
    # Add subtle corner decorations
    corner_size = 15
    corners = [
        (qr_bg_x, qr_bg_y),
        (qr_bg_x + qr_bg_size - corner_size, qr_bg_y),
        (qr_bg_x, qr_bg_y + qr_bg_size - corner_size),
        (qr_bg_x + qr_bg_size - corner_size, qr_bg_y + qr_bg_size - corner_size),
    ]
    for cx, cy in corners:
        draw.ellipse([(cx, cy), (cx + corner_size, cy + corner_size)], fill=gradient_start)
    
    # Place QR code
    qr_x = (canvas_width - qr_size) // 2
    qr_y = qr_bg_y + 30
    canvas.paste(qr_img, (qr_x, qr_y))
    
    # Information section
    info_y = qr_bg_y + qr_bg_size + 40
    
    # Organization name
    org_name = screen.organization.name if screen.organization else 'Établissement'
    org_bbox = draw.textbbox((0, 0), org_name, font=info_font)
    org_x = (canvas_width - (org_bbox[2] - org_bbox[0])) // 2
    draw.text((org_x, info_y), org_name, fill=accent_dark, font=info_font)
    
    # Screen name
    screen_name = screen.name
    screen_bbox = draw.textbbox((0, 0), screen_name, font=info_font)
    screen_x = (canvas_width - (screen_bbox[2] - screen_bbox[0])) // 2
    draw.text((screen_x, info_y + 35), screen_name, fill='#666666', font=info_font)
    
    # Resolution
    resolution_text = f"{screen.resolution_width}x{screen.resolution_height}"
    res_bbox = draw.textbbox((0, 0), resolution_text, font=info_font)
    res_x = (canvas_width - (res_bbox[2] - res_bbox[0])) // 2
    draw.text((res_x, info_y + 70), resolution_text, fill='#999999', font=info_font)
    
    # Footer with dotted line separator
    footer_y = canvas_height - 100
    
    # Dotted line
    for i in range(padding, canvas_width - padding, 12):
        draw.ellipse([(i, footer_y - 15), (i+3, footer_y - 12)], fill=gradient_start)
    
    # Website URL
    website_url = "www.shabaka-adscreen.com"
    website_bbox = draw.textbbox((0, 0), website_url, font=footer_font)
    website_x = (canvas_width - (website_bbox[2] - website_bbox[0])) // 2
    draw.text((website_x, footer_y), website_url, fill=gradient_start, font=footer_font)
    
    # Convert to RGB for PNG
    canvas = canvas.convert('RGB')
    
    buffer = io.BytesIO()
    canvas.save(buffer, format='PNG', quality=95)
    buffer.seek(0)
    
    return buffer.getvalue()
