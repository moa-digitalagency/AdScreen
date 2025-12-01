import io
import os
import secrets
import math
import qrcode
from PIL import Image, ImageDraw, ImageFont


def draw_wave_pattern(draw, canvas_width, y_start, y_end, color, amplitude=20, frequency=0.015):
    """Draw a decorative wave pattern."""
    points = []
    for x in range(canvas_width + 1):
        y = y_start + int(amplitude * math.sin(x * frequency))
        points.append((x, y))
    points.append((canvas_width, y_end))
    points.append((0, y_end))
    draw.polygon(points, fill=color)


def draw_geometric_decoration(draw, canvas_width, canvas_height, color_primary, color_secondary):
    """Draw subtle geometric decorations."""
    for x in range(0, canvas_width, 80):
        for y in range(0, canvas_height, 80):
            if (x + y) % 160 == 0:
                draw.ellipse([(x-3, y-3), (x+3, y+3)], fill=color_secondary)


def draw_gradient_background(draw, width, height, color_start, color_end, direction='diagonal'):
    """Draw a smooth gradient background."""
    if direction == 'diagonal':
        for y in range(height):
            for x in range(width):
                ratio = (x + y) / (width + height)
                r = int(color_start[0] + (color_end[0] - color_start[0]) * ratio)
                g = int(color_start[1] + (color_end[1] - color_start[1]) * ratio)
                b = int(color_start[2] + (color_end[2] - color_start[2]) * ratio)
                draw.point((x, y), fill=(r, g, b))
    else:
        for y in range(height):
            ratio = y / max(1, height)
            r = int(color_start[0] + (color_end[0] - color_start[0]) * ratio)
            g = int(color_start[1] + (color_end[1] - color_start[1]) * ratio)
            b = int(color_start[2] + (color_end[2] - color_start[2]) * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))


def generate_default_filler(screen, booking_url=None, platform_url=None, platform_name=None, base_url=None):
    """
    Generate a premium modern default filler image for a screen.
    Features a glassmorphism-inspired design with elegant gradients and animations effect.
    
    Args:
        screen: Screen model instance
        booking_url: The booking URL for QR code (optional, will be generated if not provided)
        platform_url: Platform URL for footer (optional, will use site setting if not provided)
    
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
    
    canvas = Image.new('RGB', (width, height), '#0f172a')
    draw = ImageDraw.Draw(canvas)
    
    color_primary_start = (16, 185, 129)
    color_primary_end = (5, 150, 105)
    color_accent = (52, 211, 153)
    color_secondary = (4, 120, 87)
    color_dark = (15, 23, 42)
    color_light = (248, 250, 252)
    
    for y in range(height):
        ratio = y / height
        curve = math.sin(ratio * math.pi) * 0.3 + ratio * 0.7
        r = int(15 + (30 - 15) * curve)
        g = int(23 + (41 - 23) * curve)
        b = int(42 + (59 - 42) * curve)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    header_height = int(height * 0.28)
    for y in range(header_height):
        ratio = y / header_height
        curve_ratio = math.sin(ratio * math.pi / 2)
        r = int(color_primary_start[0] + (color_primary_end[0] - color_primary_start[0]) * curve_ratio)
        g = int(color_primary_start[1] + (color_primary_end[1] - color_primary_start[1]) * curve_ratio)
        b = int(color_primary_start[2] + (color_primary_end[2] - color_primary_start[2]) * curve_ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    wave_y = header_height
    wave_points = []
    for x in range(width + 1):
        wave_offset = int(20 * math.sin(x * 0.015) + 10 * math.sin(x * 0.03))
        wave_points.append((x, wave_y + wave_offset))
    wave_points.append((width, height))
    wave_points.append((0, height))
    draw.polygon(wave_points, fill='#1e293b')
    
    num_circles = 8
    for i in range(num_circles):
        cx = int((i + 0.5) * width / num_circles) + int(30 * math.sin(i * 0.8))
        cy = int(header_height * 0.5) + int(20 * math.cos(i * 0.6))
        r = 15 + (i % 3) * 10
        opacity = 40 + (i % 4) * 15
        circle_color = (255, 255, 255)
        draw.ellipse([(cx-r, cy-r), (cx+r, cy+r)], fill=circle_color)
    
    footer_height = int(height * 0.12)
    footer_y = height - footer_height
    
    for y in range(footer_y, height):
        ratio = (y - footer_y) / footer_height
        r = int(15 + (8 - 15) * ratio)
        g = int(23 + (15 - 23) * ratio)
        b = int(42 + (40 - 42) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    accent_bar_height = 4
    for x in range(width):
        ratio = x / width
        r = int(color_primary_start[0] + (color_accent[0] - color_primary_start[0]) * ratio)
        g = int(color_primary_start[1] + (color_accent[1] - color_primary_start[1]) * ratio)
        b = int(color_primary_start[2] + (color_accent[2] - color_primary_start[2]) * ratio)
        draw.line([(x, footer_y), (x, footer_y + accent_bar_height)], fill=(r, g, b))
    
    try:
        base_size = min(width, height)
        title_size = max(int(base_size * 0.06), 32)
        subtitle_size = max(int(base_size * 0.038), 20)
        info_size = max(int(base_size * 0.028), 16)
        cta_size = max(int(base_size * 0.032), 18)
        footer_size = max(int(base_size * 0.024), 16)
        badge_size = max(int(base_size * 0.022), 14)
        
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", title_size)
        subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", subtitle_size)
        info_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", info_size)
        cta_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", cta_size)
        footer_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", footer_size)
        badge_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", badge_size)
    except:
        title_font = ImageFont.load_default()
        subtitle_font = title_font
        info_font = title_font
        cta_font = title_font
        footer_font = title_font
        badge_font = title_font
    
    org_name = screen.organization.name if screen.organization else 'Etablissement'
    org_bbox = draw.textbbox((0, 0), org_name, font=title_font)
    org_x = (width - (org_bbox[2] - org_bbox[0])) // 2
    org_y = int(header_height * 0.20)
    
    draw.text((org_x + 3, org_y + 3), org_name, fill='#047857', font=title_font)
    draw.text((org_x, org_y), org_name, fill='white', font=title_font)
    
    underline_width = min(int((org_bbox[2] - org_bbox[0]) * 0.6), width - 100)
    underline_y = org_y + (org_bbox[3] - org_bbox[1]) + 8
    underline_x = (width - underline_width) // 2
    draw.rounded_rectangle(
        [(underline_x, underline_y), (underline_x + underline_width, underline_y + 4)],
        radius=2,
        fill='#34d399'
    )
    
    screen_name = screen.name
    screen_bbox = draw.textbbox((0, 0), screen_name, font=subtitle_font)
    screen_x = (width - (screen_bbox[2] - screen_bbox[0])) // 2
    screen_y = underline_y + 20
    draw.text((screen_x, screen_y), screen_name, fill='#e0e7ff', font=subtitle_font)
    
    badge_y = screen_y + (screen_bbox[3] - screen_bbox[1]) + 15
    badges = []
    badges.append(f"🖥 {screen.resolution_width}x{screen.resolution_height}")
    badges.append(f"📐 {screen.orientation.capitalize()}")
    if screen.accepts_images and screen.accepts_videos:
        badges.append("📺 Image + Video")
    elif screen.accepts_images:
        badges.append("🖼 Image")
    elif screen.accepts_videos:
        badges.append("🎬 Video")
    
    total_badge_width = 0
    badge_info = []
    badge_padding = 12
    badge_gap = 10
    
    for badge_text in badges:
        bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
        badge_w = (bbox[2] - bbox[0]) + badge_padding * 2
        badge_info.append({'text': badge_text, 'width': badge_w, 'height': (bbox[3] - bbox[1]) + badge_padding})
        total_badge_width += badge_w
    total_badge_width += (len(badges) - 1) * badge_gap
    
    badge_start_x = (width - total_badge_width) // 2
    current_x = badge_start_x
    
    for info in badge_info:
        draw.rounded_rectangle(
            [(current_x, badge_y), (current_x + info['width'], badge_y + info['height'])],
            radius=info['height'] // 2,
            fill='#ffffff20',
            outline='#ffffff40'
        )
        text_x = current_x + badge_padding
        text_y = badge_y + (info['height'] - draw.textbbox((0, 0), info['text'], font=badge_font)[3]) // 2
        draw.text((text_x, text_y), info['text'], fill='#c7d2fe', font=badge_font)
        current_x += info['width'] + badge_gap
    
    qr_size = int(min(width, height) * 0.32)
    qr_size = max(qr_size, 140)
    
    if booking_url is None:
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
    qr_img = qr.make_image(fill_color="#1e293b", back_color="white").convert('RGB')
    qr_img = qr_img.resize((qr_size, qr_size), Image.LANCZOS)
    
    content_area_start = header_height + 30
    content_area_end = footer_y - 30
    content_area_height = content_area_end - content_area_start
    
    qr_container_padding = int(qr_size * 0.12)
    qr_container_size = qr_size + (qr_container_padding * 2)
    
    qr_center_y = content_area_start + int(content_area_height * 0.38)
    qr_x = (width - qr_container_size) // 2
    qr_y = qr_center_y - (qr_container_size // 2)
    
    corner_radius = int(qr_container_size * 0.10)
    
    shadow_layers = [
        (10, '#0f172a'),
        (6, '#1e293b'),
        (3, '#334155'),
    ]
    for offset, color in shadow_layers:
        draw.rounded_rectangle(
            [(qr_x + offset, qr_y + offset), 
             (qr_x + qr_container_size + offset, qr_y + qr_container_size + offset)],
            radius=corner_radius,
            fill=color
        )
    
    draw.rounded_rectangle(
        [(qr_x, qr_y), (qr_x + qr_container_size, qr_y + qr_container_size)],
        radius=corner_radius,
        fill='white'
    )
    
    corner_size = int(qr_container_size * 0.15)
    corner_thickness = 5
    corners_data = [
        (qr_x + 8, qr_y + 8, 'tl', '#10b981'),
        (qr_x + qr_container_size - 8 - corner_size, qr_y + 8, 'tr', '#059669'),
        (qr_x + 8, qr_y + qr_container_size - 8 - corner_size, 'bl', '#34d399'),
        (qr_x + qr_container_size - 8 - corner_size, qr_y + qr_container_size - 8 - corner_size, 'br', '#047857'),
    ]
    
    for cx, cy, pos, color in corners_data:
        if pos == 'tl':
            draw.line([(cx, cy), (cx + corner_size, cy)], fill=color, width=corner_thickness)
            draw.line([(cx, cy), (cx, cy + corner_size)], fill=color, width=corner_thickness)
        elif pos == 'tr':
            draw.line([(cx, cy), (cx + corner_size, cy)], fill=color, width=corner_thickness)
            draw.line([(cx + corner_size, cy), (cx + corner_size, cy + corner_size)], fill=color, width=corner_thickness)
        elif pos == 'bl':
            draw.line([(cx, cy), (cx, cy + corner_size)], fill=color, width=corner_thickness)
            draw.line([(cx, cy + corner_size), (cx + corner_size, cy + corner_size)], fill=color, width=corner_thickness)
        else:
            draw.line([(cx + corner_size, cy), (cx + corner_size, cy + corner_size)], fill=color, width=corner_thickness)
            draw.line([(cx, cy + corner_size), (cx + corner_size, cy + corner_size)], fill=color, width=corner_thickness)
    
    canvas.paste(qr_img, (qr_x + qr_container_padding, qr_y + qr_container_padding))
    
    cta_y = qr_y + qr_container_size + int(content_area_height * 0.06)
    cta_text = "📱 Scannez pour reserver votre espace"
    cta_bbox = draw.textbbox((0, 0), cta_text, font=cta_font)
    cta_width = cta_bbox[2] - cta_bbox[0]
    
    if cta_width > width - 60:
        cta_text = "📱 Scannez pour reserver"
        cta_bbox = draw.textbbox((0, 0), cta_text, font=cta_font)
        cta_width = cta_bbox[2] - cta_bbox[0]
    
    cta_box_padding_x = 30
    cta_box_padding_y = 15
    cta_box_width = cta_width + cta_box_padding_x * 2
    cta_box_height = (cta_bbox[3] - cta_bbox[1]) + cta_box_padding_y * 2
    cta_box_x = (width - cta_box_width) // 2
    cta_box_y = cta_y
    
    for y_offset in range(cta_box_height):
        ratio = y_offset / cta_box_height
        r = int(color_accent[0] - 20 * ratio)
        g = int(color_accent[1] - 30 * ratio)
        b = int(color_accent[2] - 20 * ratio)
        draw.line([(cta_box_x, cta_box_y + y_offset), (cta_box_x + cta_box_width, cta_box_y + y_offset)], fill=(r, g, b))
    
    draw.rounded_rectangle(
        [(cta_box_x, cta_box_y), (cta_box_x + cta_box_width, cta_box_y + cta_box_height)],
        radius=cta_box_height // 2,
        outline='#059669',
        width=0
    )
    
    cta_text_x = (width - cta_width) // 2
    cta_text_y = cta_box_y + cta_box_padding_y
    draw.text((cta_text_x, cta_text_y), cta_text, fill='white', font=cta_font)
    
    sub_cta_text = "Diffusez votre publicite sur cet ecran premium"
    sub_cta_bbox = draw.textbbox((0, 0), sub_cta_text, font=info_font)
    
    if (sub_cta_bbox[2] - sub_cta_bbox[0]) > width - 40:
        sub_cta_text = "Diffusez votre publicite ici"
        sub_cta_bbox = draw.textbbox((0, 0), sub_cta_text, font=info_font)
    
    sub_cta_x = (width - (sub_cta_bbox[2] - sub_cta_bbox[0])) // 2
    sub_cta_y = cta_box_y + cta_box_height + int(content_area_height * 0.03)
    draw.text((sub_cta_x, sub_cta_y), sub_cta_text, fill='#94a3b8', font=info_font)
    
    if platform_url is None:
        platform_url = 'www.shabaka-adscreen.com'
    
    if platform_name is None:
        platform_name = 'Shabaka AdScreen'
    
    footer_text = f"✨ {platform_name}"
    footer_bbox = draw.textbbox((0, 0), footer_text, font=footer_font)
    footer_x = (width - (footer_bbox[2] - footer_bbox[0])) // 2
    footer_text_y = footer_y + accent_bar_height + int((footer_height - accent_bar_height - (footer_bbox[3] - footer_bbox[1])) * 0.35)
    draw.text((footer_x, footer_text_y), footer_text, fill='white', font=footer_font)
    
    url_text = platform_url
    url_bbox = draw.textbbox((0, 0), url_text, font=info_font)
    url_x = (width - (url_bbox[2] - url_bbox[0])) // 2
    url_y = footer_text_y + (footer_bbox[3] - footer_bbox[1]) + 8
    draw.text((url_x, url_y), url_text, fill='#64748b', font=info_font)
    
    buffer = io.BytesIO()
    canvas.save(buffer, format='PNG', quality=95, optimize=True)
    buffer.seek(0)
    
    filename = f"default_filler_{screen.unique_code}_{secrets.token_hex(4)}.png"
    
    return buffer.getvalue(), filename


def save_default_filler_for_screen(screen, app=None):
    """
    Generate and save a default filler for the given screen.
    
    Args:
        screen: Screen model instance
        app: Flask app instance (optional, for context)
    
    Returns:
        Filler model instance or None if failed
    """
    from app import db
    from models import Filler
    
    try:
        if app:
            with app.app_context():
                return _create_and_save_filler(screen, db, Filler)
        else:
            return _create_and_save_filler(screen, db, Filler)
    except Exception as e:
        print(f"Error creating default filler for screen {screen.id}: {e}")
        return None


def _create_and_save_filler(screen, db, Filler, platform_name=None, platform_url=None):
    """Internal helper to create and save filler."""
    org_id = screen.organization_id
    upload_dir = f"static/uploads/fillers/{org_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    img_data, filename = generate_default_filler(screen, platform_name=platform_name, platform_url=platform_url)
    
    file_path = os.path.join(upload_dir, filename)
    with open(file_path, 'wb') as f:
        f.write(img_data)
    
    filler = Filler(
        filename=filename,
        content_type='image',
        file_path=file_path,
        duration_seconds=10.0,
        is_active=True,
        in_playlist=True,
        screen_id=screen.id
    )
    db.session.add(filler)
    db.session.commit()
    
    return filler


def regenerate_all_default_fillers():
    """
    Regenerate default fillers for all screens that don't have any fillers.
    """
    from app import app, db
    from models import Screen, Filler, SiteSetting
    
    with app.app_context():
        screens = Screen.query.all()
        created_count = 0
        
        platform_name = SiteSetting.get('platform_name', 'Shabaka AdScreen')
        platform_url = SiteSetting.get('platform_url', 'www.shabaka-adscreen.com')
        
        for screen in screens:
            existing_fillers = Filler.query.filter_by(screen_id=screen.id).count()
            if existing_fillers == 0:
                filler = _create_and_save_filler(screen, db, Filler, platform_name, platform_url)
                if filler:
                    created_count += 1
                    print(f"Created default filler for screen: {screen.name}")
        
        return created_count
