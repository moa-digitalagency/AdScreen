import io
import os
import secrets
import math
import qrcode
from PIL import Image, ImageDraw, ImageFont


def draw_gradient_vertical(draw, width, height, color_start, color_end):
    """Draw a smooth vertical gradient."""
    for y in range(height):
        ratio = y / height
        r = int(color_start[0] + (color_end[0] - color_start[0]) * ratio)
        g = int(color_start[1] + (color_end[1] - color_start[1]) * ratio)
        b = int(color_start[2] + (color_end[2] - color_start[2]) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))


def generate_default_filler(screen, booking_url=None, platform_url=None, platform_name=None, base_url=None):
    """
    Generate a professional light-theme default filler image.
    QR code proportional to screen resolution.
    
    Args:
        screen: Screen model instance
        booking_url: The booking URL for QR code (optional)
        platform_url: Platform URL for footer (optional)
        platform_name: Name of the platform
        base_url: Base URL for constructing booking link
    
    Returns:
        tuple: (bytes image data, filename)
    """
    width = screen.resolution_width
    height = screen.resolution_height
    orientation = screen.orientation
    
    if orientation == 'portrait' and width > height:
        width, height = height, width
    elif orientation == 'landscape' and height > width:
        width, height = height, width
    
    # Light theme - white background
    canvas = Image.new('RGB', (width, height), '#ffffff')
    draw = ImageDraw.Draw(canvas)
    
    # Emerald gradient colors
    gradient_start = (16, 185, 129)  # #10b981
    gradient_end = (20, 184, 166)    # #14b8a6
    accent_light = (209, 250, 229)   # #d1fae5
    text_dark = (15, 23, 42)         # #0f172a
    text_muted = (107, 114, 128)     # #6b7280
    
    # Subtle dotted pattern
    dot_spacing = int(min(width, height) * 0.08)
    for x in range(0, width, dot_spacing):
        for y in range(0, height, dot_spacing):
            if (x + y) // dot_spacing % 3 == 0:
                draw.ellipse([(x-1, y-1), (x+2, y+2)], fill=(240, 245, 240))
    
    # Top gradient header (15% of height)
    header_height = max(int(height * 0.12), 80)
    draw_gradient_vertical(draw, width, header_height, gradient_start, gradient_end)
    
    # Organization name in header
    try:
        org_font_size = max(int(width * 0.05), 28)
        subtitle_font_size = max(int(width * 0.035), 20)
        info_font_size = max(int(width * 0.025), 14)
        footer_font_size = max(int(width * 0.022), 12)
        
        org_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", org_font_size)
        subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", subtitle_font_size)
        info_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", info_font_size)
        footer_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", footer_font_size)
    except:
        org_font = ImageFont.load_default()
        subtitle_font = org_font
        info_font = org_font
        footer_font = org_font
    
    org_name = screen.organization.name if screen.organization else 'Établissement'
    org_bbox = draw.textbbox((0, 0), org_name, font=org_font)
    org_x = (width - (org_bbox[2] - org_bbox[0])) // 2
    org_y = int(header_height * 0.15)
    draw.text((org_x, org_y), org_name, fill='#ffffff', font=org_font)
    
    # Content section
    content_y = header_height + int(height * 0.05)
    
    # Screen name
    screen_name = screen.name
    screen_bbox = draw.textbbox((0, 0), screen_name, font=subtitle_font)
    screen_x = (width - (screen_bbox[2] - screen_bbox[0])) // 2
    draw.text((screen_x, content_y), screen_name, fill=text_dark, font=subtitle_font)
    
    # Decorative line under name
    line_width = min(int((screen_bbox[2] - screen_bbox[0]) * 0.3), width - 100)
    line_x = (width - line_width) // 2
    line_y = content_y + (screen_bbox[3] - screen_bbox[1]) + 10
    draw.rounded_rectangle([(line_x, line_y), (line_x + line_width, line_y + 2)], radius=1, fill=gradient_start)
    
    # Resolution
    resolution_text = f"{screen.resolution_width} x {screen.resolution_height}"
    resolution_bbox = draw.textbbox((0, 0), resolution_text, font=info_font)
    res_x = (width - (resolution_bbox[2] - resolution_bbox[0])) // 2
    res_y = line_y + 20
    draw.text((res_x, res_y), resolution_text, fill=text_muted, font=info_font)
    
    # Generate proportional QR code
    if not booking_url:
        if base_url:
            booking_url = f"{base_url}/book/{screen.unique_code}"
        else:
            booking_url = f"https://shabaka-adscreen.com/book/{screen.unique_code}"
    
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=6,
            border=1,
        )
        qr.add_data(booking_url)
        qr.make(fit=True)
        
        qr_img_pil = qr.make_image(fill_color="#059669", back_color="white").convert('RGB')
        
        # QR size = 20% of screen width (max)
        max_qr_size = int(width * 0.20)
        qr_size = min(max_qr_size, 200)
        
        try:
            qr_img_pil = qr_img_pil.resize((qr_size, qr_size), Image.LANCZOS)
        except AttributeError:
            qr_img_pil = qr_img_pil.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
        
        # Center QR code
        qr_x = (width - qr_size) // 2
        qr_y = res_y + int(height * 0.08)
        
        # Light background for QR
        bg_pad = 8
        draw.rectangle(
            [(qr_x - bg_pad, qr_y - bg_pad), (qr_x + qr_size + bg_pad, qr_y + qr_size + bg_pad)],
            fill=accent_light,
            outline=gradient_start,
            width=1
        )
        
        canvas.paste(qr_img_pil, (qr_x, qr_y))
        
        # Text under QR
        reserve_text = "Réservez un créneau"
        reserve_bbox = draw.textbbox((0, 0), reserve_text, font=info_font)
        reserve_x = (width - (reserve_bbox[2] - reserve_bbox[0])) // 2
        reserve_y = qr_y + qr_size + 15
        draw.text((reserve_x, reserve_y), reserve_text, fill=gradient_start, font=info_font)
    except:
        pass
    
    # Footer section
    footer_height = max(int(height * 0.10), 60)
    footer_y = height - footer_height
    
    # Gradient footer
    draw_gradient_vertical(draw, width, footer_height, accent_light, gradient_start)
    
    # Website URL centered in footer
    website_url = "www.shabaka-adscreen.com"
    website_bbox = draw.textbbox((0, 0), website_url, font=footer_font)
    website_x = (width - (website_bbox[2] - website_bbox[0])) // 2
    website_y = footer_y + (footer_height - (website_bbox[3] - website_bbox[1])) // 2
    draw.text((website_x, website_y), website_url, fill='#ffffff', font=footer_font)
    
    # Save image
    filename = f"filler_{screen.id}_{secrets.token_hex(4)}.png"
    
    buffer = io.BytesIO()
    canvas.save(buffer, format='PNG', quality=95)
    buffer.seek(0)
    
    return buffer.getvalue(), filename
