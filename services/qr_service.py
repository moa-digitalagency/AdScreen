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


def draw_gradient_vertical(draw, width, height, color_start, color_end):
    """Draw a smooth vertical gradient."""
    for y in range(height):
        ratio = y / height
        r = int(color_start[0] + (color_end[0] - color_start[0]) * ratio)
        g = int(color_start[1] + (color_end[1] - color_start[1]) * ratio)
        b = int(color_start[2] + (color_end[2] - color_start[2]) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))


def generate_enhanced_qr_image(screen, booking_url, platform_name='Shabaka AdScreen'):
    """
    Generate a professional light-theme enhanced QR code image.
    QR code proportional to screen resolution (max 30% of screen).
    
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
    
    qr_img_temp = qr.make_image(fill_color="#059669", back_color="white").convert('RGB')
    qr_base_size = qr_img_temp.size[0]
    
    # Responsive canvas size based on aspect ratio
    aspect_ratio = screen.resolution_width / screen.resolution_height
    
    if aspect_ratio >= 1:  # Landscape
        canvas_width = min(800, screen.resolution_width)
        canvas_height = int(canvas_width / aspect_ratio)
    else:  # Portrait
        canvas_height = min(800, screen.resolution_height)
        canvas_width = int(canvas_height * aspect_ratio)
    
    # Ensure minimum size
    canvas_width = max(canvas_width, 400)
    canvas_height = max(canvas_height, 400)
    
    padding = int(canvas_width * 0.06)
    
    # Light theme background
    canvas = Image.new('RGB', (canvas_width, canvas_height), '#ffffff')
    draw = ImageDraw.Draw(canvas)
    
    # Emerald gradient colors
    gradient_start = (16, 185, 129)  # #10b981
    gradient_end = (20, 184, 166)    # #14b8a6
    accent_light = (209, 250, 229)   # #d1fae5
    accent_dark = (5, 150, 105)      # #059669
    text_dark = (15, 23, 42)         # #0f172a
    text_muted = (107, 114, 128)     # #6b7280
    
    # Subtle dotted pattern
    dot_spacing = int(canvas_width * 0.1)
    for x in range(0, canvas_width, dot_spacing):
        for y in range(0, canvas_height, dot_spacing):
            if (x + y) // dot_spacing % 3 == 0:
                draw.ellipse([(x-1, y-1), (x+2, y+2)], fill=(240, 245, 240))
    
    # Header gradient
    header_height = max(int(canvas_height * 0.15), 60)
    draw_gradient_vertical(draw, canvas_width, header_height, gradient_start, gradient_end)
    
    # Platform name in header
    try:
        header_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 
                                        max(int(canvas_width * 0.04), 16))
        label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 
                                       max(int(canvas_width * 0.035), 14))
        info_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 
                                      max(int(canvas_width * 0.025), 11))
        footer_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 
                                        max(int(canvas_width * 0.02), 10))
    except:
        header_font = ImageFont.load_default()
        label_font = header_font
        info_font = header_font
        footer_font = header_font
    
    # Platform name
    platform_bbox = draw.textbbox((0, 0), platform_name, font=header_font)
    platform_x = (canvas_width - (platform_bbox[2] - platform_bbox[0])) // 2
    platform_y = int(header_height * 0.2)
    draw.text((platform_x, platform_y), platform_name, fill='#ffffff', font=header_font)
    
    # QR code section
    qr_label_y = header_height + int(canvas_height * 0.04)
    qr_label_bbox = draw.textbbox((0, 0), "Scannez", font=label_font)
    qr_label_x = (canvas_width - (qr_label_bbox[2] - qr_label_bbox[0])) // 2
    draw.text((qr_label_x, qr_label_y), "Scannez", fill=accent_dark, font=label_font)
    
    # QR code - PROPORTIONAL (25% of canvas height max)
    max_qr_height = int(canvas_height * 0.25)
    qr_size = min(max_qr_height, 280)
    
    try:
        qr_img = qr_img_temp.resize((qr_size, qr_size), Image.LANCZOS)
    except AttributeError:
        qr_img = qr_img_temp.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
    
    # Center QR code
    qr_bg_pad = int(qr_size * 0.15)
    qr_bg_size = qr_size + qr_bg_pad * 2
    qr_bg_x = (canvas_width - qr_bg_size) // 2
    qr_bg_y = qr_label_y + int(canvas_height * 0.08)
    
    # Light background
    draw.rectangle(
        [(qr_bg_x, qr_bg_y), (qr_bg_x + qr_bg_size, qr_bg_y + qr_bg_size)],
        fill=accent_light,
        outline=gradient_start,
        width=1
    )
    
    # Place QR
    qr_x = (canvas_width - qr_size) // 2
    qr_y = qr_bg_y + qr_bg_pad
    canvas.paste(qr_img, (qr_x, qr_y))
    
    # Info section below QR
    info_y = qr_bg_y + qr_bg_size + int(canvas_height * 0.04)
    
    org_name = screen.organization.name if screen.organization else 'Établissement'
    org_bbox = draw.textbbox((0, 0), org_name, font=info_font)
    org_x = (canvas_width - (org_bbox[2] - org_bbox[0])) // 2
    draw.text((org_x, info_y), org_name, fill=text_dark, font=info_font)
    
    # Screen name
    screen_name = screen.name
    screen_bbox = draw.textbbox((0, 0), screen_name, font=info_font)
    screen_x = (canvas_width - (screen_bbox[2] - screen_bbox[0])) // 2
    draw.text((screen_x, info_y + int(canvas_height * 0.04)), screen_name, fill=text_muted, font=info_font)
    
    # Resolution
    resolution_text = f"{screen.resolution_width}x{screen.resolution_height}"
    res_bbox = draw.textbbox((0, 0), resolution_text, font=info_font)
    res_x = (canvas_width - (res_bbox[2] - res_bbox[0])) // 2
    draw.text((res_x, info_y + int(canvas_height * 0.08)), resolution_text, fill=text_muted, font=info_font)
    
    # Footer
    footer_height = max(int(canvas_height * 0.1), 50)
    footer_y = canvas_height - footer_height
    
    draw_gradient_vertical(draw, canvas_width, footer_height, accent_light, gradient_start)
    
    website_url = "www.shabaka-adscreen.com"
    website_bbox = draw.textbbox((0, 0), website_url, font=footer_font)
    website_x = (canvas_width - (website_bbox[2] - website_bbox[0])) // 2
    website_y = footer_y + (footer_height - (website_bbox[3] - website_bbox[1])) // 2
    draw.text((website_x, website_y), website_url, fill='#ffffff', font=footer_font)
    
    canvas = canvas.convert('RGB')
    
    buffer = io.BytesIO()
    canvas.save(buffer, format='PNG', quality=95)
    buffer.seek(0)
    
    return buffer.getvalue()
