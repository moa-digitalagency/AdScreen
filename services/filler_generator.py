import io
import os
import secrets
import math
import qrcode
from PIL import Image, ImageDraw, ImageFont


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


def get_aspect_ratio_type(width, height):
    """
    Determine the aspect ratio type of the screen.
    Returns: 'square' (1:1), 'portrait' (height > width), 'landscape' (width > height)
    """
    ratio = width / height if height > 0 else 1
    
    if 0.95 <= ratio <= 1.05:
        return 'square'
    elif ratio < 1:
        return 'portrait'
    else:
        return 'landscape'


def generate_default_filler(screen, booking_url=None, platform_url=None, platform_name=None, base_url=None):
    """
    Generate a professional light-theme default filler image.
    QR code proportional to screen resolution:
    - 50% for landscape or portrait ratios
    - 30% for square (1:1) ratio
    
    Position:
    - Portrait: QR towards bottom
    - Landscape: QR towards right
    - Square: QR centered-bottom
    
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
    
    aspect_type = get_aspect_ratio_type(width, height)
    
    emerald_500 = (16, 185, 129)
    emerald_600 = (5, 150, 105)
    emerald_700 = (4, 120, 87)
    emerald_50 = (236, 253, 245)
    emerald_100 = (209, 250, 229)
    emerald_200 = (167, 243, 208)
    teal_500 = (20, 184, 166)
    text_dark = (15, 23, 42)
    text_muted = (107, 114, 128)
    text_white = (255, 255, 255)
    
    canvas = Image.new('RGB', (width, height), '#ffffff')
    draw = ImageDraw.Draw(canvas)
    
    dot_spacing = max(int(min(width, height) * 0.06), 30)
    for x in range(0, width, dot_spacing):
        for y in range(0, height, dot_spacing):
            if (x + y) // dot_spacing % 3 == 0:
                draw.ellipse([(x-2, y-2), (x+3, y+3)], fill=emerald_50)
    
    try:
        title_size = max(int(min(width, height) * 0.06), 32)
        subtitle_size = max(int(min(width, height) * 0.04), 24)
        label_size = max(int(min(width, height) * 0.045), 22)
        info_size = max(int(min(width, height) * 0.032), 18)
        small_size = max(int(min(width, height) * 0.025), 14)
        footer_size = max(int(min(width, height) * 0.028), 16)
        
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", title_size)
        subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", subtitle_size)
        label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", label_size)
        info_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", info_size)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", small_size)
        footer_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", footer_size)
    except:
        title_font = ImageFont.load_default()
        subtitle_font = title_font
        label_font = title_font
        info_font = title_font
        small_font = title_font
        footer_font = title_font
    
    if not booking_url:
        if base_url:
            booking_url = f"{base_url}/book/{screen.unique_code}"
        else:
            booking_url = f"https://shabaka-adscreen.com/book/{screen.unique_code}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(booking_url)
    qr.make(fit=True)
    qr_img_temp = qr.make_image(fill_color="#059669", back_color="white").convert('RGB')
    
    if aspect_type == 'square':
        qr_size_percent = 0.30
    else:
        qr_size_percent = 0.50
    
    org_name = screen.organization.name if screen.organization else 'Établissement'
    screen_name = screen.name
    resolution_text = f"{screen.resolution_width} x {screen.resolution_height}"
    
    if aspect_type == 'portrait':
        header_height = int(height * 0.12)
        draw_gradient_rect(draw, 0, 0, width, header_height, emerald_500, emerald_700, vertical=True)
        
        platform = platform_name or "Shabaka AdScreen"
        platform_bbox = draw.textbbox((0, 0), platform, font=title_font)
        platform_x = (width - (platform_bbox[2] - platform_bbox[0])) // 2
        platform_y = (header_height - (platform_bbox[3] - platform_bbox[1])) // 2
        draw.text((platform_x, platform_y), platform, fill=text_white, font=title_font)
        
        content_y = header_height + int(height * 0.04)
        
        org_bbox = draw.textbbox((0, 0), org_name, font=label_font)
        org_x = (width - (org_bbox[2] - org_bbox[0])) // 2
        draw.text((org_x, content_y), org_name, fill=text_dark, font=label_font)
        
        line_width = min(int((org_bbox[2] - org_bbox[0]) * 0.5), width - 100)
        line_x = (width - line_width) // 2
        line_y = content_y + (org_bbox[3] - org_bbox[1]) + 10
        draw.rounded_rectangle([(line_x, line_y), (line_x + line_width, line_y + 4)], radius=2, fill=emerald_500)
        
        screen_bbox = draw.textbbox((0, 0), screen_name, font=info_font)
        screen_x = (width - (screen_bbox[2] - screen_bbox[0])) // 2
        screen_y = line_y + 20
        draw.text((screen_x, screen_y), screen_name, fill=emerald_600, font=info_font)
        
        res_bbox = draw.textbbox((0, 0), resolution_text, font=small_font)
        res_x = (width - (res_bbox[2] - res_bbox[0])) // 2
        res_y = screen_y + (screen_bbox[3] - screen_bbox[1]) + 10
        draw.text((res_x, res_y), resolution_text, fill=text_muted, font=small_font)
        
        footer_height = int(height * 0.08)
        footer_y = height - footer_height
        
        qr_section_height = int(height * qr_size_percent)
        qr_section_y = footer_y - qr_section_height - int(height * 0.02)
        
        qr_size = int(min(width * 0.7, qr_section_height * 0.75))
        
        try:
            qr_img = qr_img_temp.resize((qr_size, qr_size), Image.LANCZOS)
        except AttributeError:
            qr_img = qr_img_temp.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
        
        qr_bg_padding = int(qr_size * 0.1)
        qr_bg_size = qr_size + qr_bg_padding * 2
        qr_bg_x = (width - qr_bg_size) // 2
        qr_bg_y = qr_section_y + int((qr_section_height - qr_bg_size - 50) / 2)
        
        draw.rounded_rectangle(
            [(qr_bg_x - 8, qr_bg_y - 8), (qr_bg_x + qr_bg_size + 8, qr_bg_y + qr_bg_size + 8)],
            radius=25,
            fill=emerald_100,
            outline=emerald_500,
            width=4
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
        scan_x = (width - (scan_bbox[2] - scan_bbox[0])) // 2
        scan_y = qr_bg_y + qr_bg_size + 20
        draw.text((scan_x, scan_y), scan_text, fill=emerald_600, font=info_font)
        
        draw_gradient_rect(draw, 0, footer_y, width, height, emerald_600, emerald_700, vertical=True)
        
        website_url = "www.shabaka-adscreen.com"
        website_bbox = draw.textbbox((0, 0), website_url, font=footer_font)
        website_x = (width - (website_bbox[2] - website_bbox[0])) // 2
        website_y = footer_y + (footer_height - (website_bbox[3] - website_bbox[1])) // 2
        draw.text((website_x, website_y), website_url, fill=text_white, font=footer_font)
        
    elif aspect_type == 'landscape':
        left_panel_width = int(width * (1 - qr_size_percent))
        right_panel_width = width - left_panel_width
        
        header_height = int(height * 0.15)
        draw_gradient_rect(draw, 0, 0, left_panel_width, header_height, emerald_500, emerald_700, vertical=True)
        
        platform = platform_name or "Shabaka AdScreen"
        platform_bbox = draw.textbbox((0, 0), platform, font=title_font)
        platform_x = (left_panel_width - (platform_bbox[2] - platform_bbox[0])) // 2
        platform_y = (header_height - (platform_bbox[3] - platform_bbox[1])) // 2
        draw.text((platform_x, platform_y), platform, fill=text_white, font=title_font)
        
        content_center_y = header_height + (height - header_height) // 2
        
        org_bbox = draw.textbbox((0, 0), org_name, font=label_font)
        org_x = (left_panel_width - (org_bbox[2] - org_bbox[0])) // 2
        org_y = content_center_y - int(height * 0.12)
        draw.text((org_x, org_y), org_name, fill=text_dark, font=label_font)
        
        line_width = min(int((org_bbox[2] - org_bbox[0]) * 0.5), left_panel_width - 100)
        line_x = (left_panel_width - line_width) // 2
        line_y = org_y + (org_bbox[3] - org_bbox[1]) + 15
        draw.rounded_rectangle([(line_x, line_y), (line_x + line_width, line_y + 4)], radius=2, fill=emerald_500)
        
        screen_bbox = draw.textbbox((0, 0), screen_name, font=info_font)
        screen_x = (left_panel_width - (screen_bbox[2] - screen_bbox[0])) // 2
        screen_y = line_y + 25
        draw.text((screen_x, screen_y), screen_name, fill=emerald_600, font=info_font)
        
        res_bbox = draw.textbbox((0, 0), resolution_text, font=small_font)
        res_x = (left_panel_width - (res_bbox[2] - res_bbox[0])) // 2
        res_y = screen_y + (screen_bbox[3] - screen_bbox[1]) + 15
        draw.text((res_x, res_y), resolution_text, fill=text_muted, font=small_font)
        
        footer_height = int(height * 0.10)
        footer_y = height - footer_height
        draw_gradient_rect(draw, 0, footer_y, left_panel_width, height, emerald_600, emerald_700, vertical=True)
        
        website_url = "www.shabaka-adscreen.com"
        website_bbox = draw.textbbox((0, 0), website_url, font=footer_font)
        website_x = (left_panel_width - (website_bbox[2] - website_bbox[0])) // 2
        website_y = footer_y + (footer_height - (website_bbox[3] - website_bbox[1])) // 2
        draw.text((website_x, website_y), website_url, fill=text_white, font=footer_font)
        
        right_panel_x = left_panel_width
        draw.rectangle([(right_panel_x, 0), (width, height)], fill=emerald_50)
        
        for x in range(right_panel_x, width, 40):
            for y in range(0, height, 40):
                if (x + y) // 40 % 2 == 0:
                    draw.ellipse([(x-3, y-3), (x+4, y+4)], fill=emerald_100)
        
        qr_size = int(min(right_panel_width * 0.75, height * 0.65))
        
        try:
            qr_img = qr_img_temp.resize((qr_size, qr_size), Image.LANCZOS)
        except AttributeError:
            qr_img = qr_img_temp.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
        
        qr_center_x = right_panel_x + right_panel_width // 2
        qr_center_y = height // 2
        
        qr_bg_padding = int(qr_size * 0.1)
        qr_bg_size = qr_size + qr_bg_padding * 2
        qr_bg_x = qr_center_x - qr_bg_size // 2
        qr_bg_y = qr_center_y - qr_bg_size // 2 - 20
        
        draw.rounded_rectangle(
            [(qr_bg_x - 10, qr_bg_y - 10), (qr_bg_x + qr_bg_size + 10, qr_bg_y + qr_bg_size + 10)],
            radius=30,
            fill=emerald_200,
            outline=emerald_500,
            width=5
        )
        
        draw.rounded_rectangle(
            [(qr_bg_x + qr_bg_padding - 8, qr_bg_y + qr_bg_padding - 8),
             (qr_bg_x + qr_bg_padding + qr_size + 8, qr_bg_y + qr_bg_padding + qr_size + 8)],
            radius=10,
            fill='#ffffff'
        )
        
        qr_x = qr_bg_x + qr_bg_padding
        qr_y = qr_bg_y + qr_bg_padding
        canvas.paste(qr_img, (qr_x, qr_y))
        
        scan_text = "Scannez pour réserver"
        scan_bbox = draw.textbbox((0, 0), scan_text, font=info_font)
        scan_x = qr_center_x - (scan_bbox[2] - scan_bbox[0]) // 2
        scan_y = qr_bg_y + qr_bg_size + 25
        draw.text((scan_x, scan_y), scan_text, fill=emerald_700, font=info_font)
        
    else:
        header_height = int(height * 0.15)
        draw_gradient_rect(draw, 0, 0, width, header_height, emerald_500, emerald_700, vertical=True)
        
        platform = platform_name or "Shabaka AdScreen"
        platform_bbox = draw.textbbox((0, 0), platform, font=title_font)
        platform_x = (width - (platform_bbox[2] - platform_bbox[0])) // 2
        platform_y = (header_height - (platform_bbox[3] - platform_bbox[1])) // 2
        draw.text((platform_x, platform_y), platform, fill=text_white, font=title_font)
        
        content_y = header_height + int(height * 0.05)
        
        org_bbox = draw.textbbox((0, 0), org_name, font=label_font)
        org_x = (width - (org_bbox[2] - org_bbox[0])) // 2
        draw.text((org_x, content_y), org_name, fill=text_dark, font=label_font)
        
        line_width = min(int((org_bbox[2] - org_bbox[0]) * 0.5), width - 100)
        line_x = (width - line_width) // 2
        line_y = content_y + (org_bbox[3] - org_bbox[1]) + 12
        draw.rounded_rectangle([(line_x, line_y), (line_x + line_width, line_y + 4)], radius=2, fill=emerald_500)
        
        screen_bbox = draw.textbbox((0, 0), screen_name, font=info_font)
        screen_x = (width - (screen_bbox[2] - screen_bbox[0])) // 2
        screen_y = line_y + 20
        draw.text((screen_x, screen_y), screen_name, fill=emerald_600, font=info_font)
        
        res_bbox = draw.textbbox((0, 0), resolution_text, font=small_font)
        res_x = (width - (res_bbox[2] - res_bbox[0])) // 2
        res_y = screen_y + (screen_bbox[3] - screen_bbox[1]) + 10
        draw.text((res_x, res_y), resolution_text, fill=text_muted, font=small_font)
        
        footer_height = int(height * 0.10)
        footer_y = height - footer_height
        
        qr_section_height = int(height * qr_size_percent)
        qr_size = int(min(width * 0.5, qr_section_height * 0.85))
        
        try:
            qr_img = qr_img_temp.resize((qr_size, qr_size), Image.LANCZOS)
        except AttributeError:
            qr_img = qr_img_temp.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
        
        qr_bg_padding = int(qr_size * 0.1)
        qr_bg_size = qr_size + qr_bg_padding * 2
        qr_bg_x = (width - qr_bg_size) // 2
        qr_bg_y = footer_y - qr_bg_size - int(height * 0.08)
        
        draw.rounded_rectangle(
            [(qr_bg_x - 8, qr_bg_y - 8), (qr_bg_x + qr_bg_size + 8, qr_bg_y + qr_bg_size + 8)],
            radius=20,
            fill=emerald_100,
            outline=emerald_500,
            width=4
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
        scan_x = (width - (scan_bbox[2] - scan_bbox[0])) // 2
        scan_y = qr_bg_y + qr_bg_size + 15
        draw.text((scan_x, scan_y), scan_text, fill=emerald_600, font=info_font)
        
        draw_gradient_rect(draw, 0, footer_y, width, height, emerald_600, emerald_700, vertical=True)
        
        website_url = "www.shabaka-adscreen.com"
        website_bbox = draw.textbbox((0, 0), website_url, font=footer_font)
        website_x = (width - (website_bbox[2] - website_bbox[0])) // 2
        website_y = footer_y + (footer_height - (website_bbox[3] - website_bbox[1])) // 2
        draw.text((website_x, website_y), website_url, fill=text_white, font=footer_font)
    
    filename = f"filler_{screen.id}_{secrets.token_hex(4)}.png"
    
    buffer = io.BytesIO()
    canvas.save(buffer, format='PNG', quality=95)
    buffer.seek(0)
    
    return buffer.getvalue(), filename
