import io
import os
import secrets
import math
try:
    from qrcode import QRCode
    from qrcode.constants import ERROR_CORRECT_H
except ImportError:
    QRCode = None  # type: ignore
    ERROR_CORRECT_H = None  # type: ignore
from PIL import Image, ImageDraw, ImageFont


def generate_default_filler(screen, booking_url=None, platform_url=None, platform_name=None, base_url=None):
    """
    Generate a premium light-themed filler image for a screen.
    Features a clean, modern design with emerald gradient accents.
    
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
    
    canvas = Image.new('RGB', (width, height), '#ffffff')
    draw = ImageDraw.Draw(canvas)
    
    color_emerald_400 = (52, 211, 153)
    color_emerald_500 = (16, 185, 129)
    color_emerald_600 = (5, 150, 105)
    color_teal_500 = (20, 184, 166)
    color_gray_50 = (249, 250, 251)
    color_gray_100 = (243, 244, 246)
    color_gray_200 = (229, 231, 235)
    color_gray_600 = (75, 85, 99)
    color_gray_800 = (31, 41, 55)
    color_gray_900 = (17, 24, 39)
    
    for y in range(height):
        ratio = y / height
        r = int(255 - (255 - 249) * ratio * 0.5)
        g = int(255 - (255 - 250) * ratio * 0.5)
        b = int(255 - (255 - 251) * ratio * 0.5)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    header_height = int(height * 0.18)
    for y in range(header_height):
        ratio = y / header_height
        r = int(color_emerald_500[0] + (color_teal_500[0] - color_emerald_500[0]) * ratio)
        g = int(color_emerald_500[1] + (color_teal_500[1] - color_emerald_500[1]) * ratio)
        b = int(color_emerald_500[2] + (color_teal_500[2] - color_emerald_500[2]) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    wave_amplitude = int(height * 0.025)
    wave_frequency = 0.012
    wave_points = []
    for x in range(width + 1):
        wave_y = header_height + int(wave_amplitude * math.sin(x * wave_frequency))
        wave_points.append((x, wave_y))
    wave_points.append((width, height))
    wave_points.append((0, height))
    draw.polygon(wave_points, fill=color_gray_50)
    
    footer_height = int(height * 0.08)
    footer_y = height - footer_height
    
    draw.rectangle([(0, footer_y), (width, height)], fill=color_gray_100)
    
    accent_height = 4
    for x in range(width):
        ratio = x / width
        r = int(color_emerald_500[0] + (color_teal_500[0] - color_emerald_500[0]) * ratio)
        g = int(color_emerald_500[1] + (color_teal_500[1] - color_emerald_500[1]) * ratio)
        b = int(color_emerald_500[2] + (color_teal_500[2] - color_emerald_500[2]) * ratio)
        draw.line([(x, footer_y), (x, footer_y + accent_height)], fill=(r, g, b))
    
    try:
        base_size = min(width, height)
        title_size = max(int(base_size * 0.055), 28)
        subtitle_size = max(int(base_size * 0.032), 18)
        info_size = max(int(base_size * 0.024), 14)
        cta_size = max(int(base_size * 0.028), 16)
        footer_size = max(int(base_size * 0.022), 14)
        badge_size = max(int(base_size * 0.018), 12)
        
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
    org_y = int(header_height * 0.25)
    draw.text((org_x, org_y), org_name, fill='white', font=title_font)
    
    screen_name = screen.name
    screen_bbox = draw.textbbox((0, 0), screen_name, font=subtitle_font)
    screen_x = (width - (screen_bbox[2] - screen_bbox[0])) // 2
    screen_y = org_y + (org_bbox[3] - org_bbox[1]) + int(header_height * 0.08)
    draw.text((screen_x, screen_y), screen_name, fill='#d1fae5', font=subtitle_font)
    
    qr_size = int(min(width, height) * 0.30)
    qr_size = max(qr_size, 120)
    
    if booking_url is None:
        if base_url:
            booking_url = f"{base_url}/book/{screen.unique_code}"
        else:
            booking_url = f"https://shabaka-adscreen.com/book/{screen.unique_code}"
    
    qr = QRCode(
        version=1,
        error_correction=ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(booking_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#059669", back_color="white").convert('RGB')
    try:
        resample = Image.LANCZOS  # type: ignore
    except AttributeError:
        resample = Image.Resampling.LANCZOS  # type: ignore
    qr_img = qr_img.resize((qr_size, qr_size), resample)
    
    content_start = header_height + wave_amplitude + 20
    content_end = footer_y - 20
    content_height = content_end - content_start
    
    qr_padding = int(qr_size * 0.10)
    qr_container_size = qr_size + (qr_padding * 2)
    
    qr_center_y = content_start + int(content_height * 0.35)
    qr_x = (width - qr_container_size) // 2
    qr_y = qr_center_y - (qr_container_size // 2)
    
    shadow_offset = 8
    draw.rounded_rectangle(
        [(qr_x + shadow_offset, qr_y + shadow_offset), 
         (qr_x + qr_container_size + shadow_offset, qr_y + qr_container_size + shadow_offset)],
        radius=16,
        fill=color_gray_200
    )
    
    draw.rounded_rectangle(
        [(qr_x, qr_y), (qr_x + qr_container_size, qr_y + qr_container_size)],
        radius=16,
        fill='white',
        outline=color_emerald_500,
        width=3
    )
    
    canvas.paste(qr_img, (qr_x + qr_padding, qr_y + qr_padding))
    
    cta_y = qr_y + qr_container_size + int(content_height * 0.06)
    cta_text = "Scannez pour reserver"
    cta_bbox = draw.textbbox((0, 0), cta_text, font=cta_font)
    cta_width = cta_bbox[2] - cta_bbox[0]
    
    cta_box_padding_x = 24
    cta_box_padding_y = 12
    cta_box_width = cta_width + cta_box_padding_x * 2
    cta_box_height = int((cta_bbox[3] - cta_bbox[1]) + cta_box_padding_y * 2)
    cta_box_x = (width - cta_box_width) // 2
    cta_box_y = cta_y
    
    for y_offset in range(cta_box_height):
        ratio = y_offset / cta_box_height
        r = int(color_emerald_500[0] + (color_teal_500[0] - color_emerald_500[0]) * ratio)
        g = int(color_emerald_500[1] + (color_teal_500[1] - color_emerald_500[1]) * ratio)
        b = int(color_emerald_500[2] + (color_teal_500[2] - color_emerald_500[2]) * ratio)
        draw.line([(cta_box_x, cta_box_y + y_offset), (cta_box_x + cta_box_width, cta_box_y + y_offset)], fill=(r, g, b))
    
    draw.rounded_rectangle(
        [(cta_box_x, cta_box_y), (cta_box_x + cta_box_width, cta_box_y + cta_box_height)],
        radius=cta_box_height // 2,
        outline=None,
        width=0
    )
    
    cta_text_x = (width - cta_width) // 2
    cta_text_y = cta_box_y + cta_box_padding_y
    draw.text((cta_text_x, cta_text_y), cta_text, fill='white', font=cta_font)
    
    sub_cta_y = cta_box_y + cta_box_height + int(content_height * 0.04)
    sub_cta_text = "Diffusez votre publicite sur cet ecran"
    sub_cta_bbox = draw.textbbox((0, 0), sub_cta_text, font=info_font)
    
    if (sub_cta_bbox[2] - sub_cta_bbox[0]) > width - 40:
        sub_cta_text = "Votre publicite ici"
        sub_cta_bbox = draw.textbbox((0, 0), sub_cta_text, font=info_font)
    
    sub_cta_x = (width - (sub_cta_bbox[2] - sub_cta_bbox[0])) // 2
    draw.text((sub_cta_x, sub_cta_y), sub_cta_text, fill=color_gray_600, font=info_font)
    
    info_y = sub_cta_y + (sub_cta_bbox[3] - sub_cta_bbox[1]) + int(content_height * 0.04)
    info_parts = []
    info_parts.append(f"{screen.resolution_width}x{screen.resolution_height}")
    info_parts.append(screen.orientation.capitalize())
    if screen.accepts_images and screen.accepts_videos:
        info_parts.append("Image + Video")
    elif screen.accepts_images:
        info_parts.append("Image")
    elif screen.accepts_videos:
        info_parts.append("Video")
    
    info_text = "  |  ".join(info_parts)
    info_bbox = draw.textbbox((0, 0), info_text, font=badge_font)
    info_x = (width - (info_bbox[2] - info_bbox[0])) // 2
    
    if info_y + (info_bbox[3] - info_bbox[1]) < footer_y - 10:
        draw.text((info_x, info_y), info_text, fill=color_gray_600, font=badge_font)
    
    if platform_url is None:
        platform_url = 'www.shabaka-adscreen.com'
    
    if platform_name is None:
        platform_name = 'Shabaka AdScreen'
    
    footer_text = platform_name
    footer_bbox = draw.textbbox((0, 0), footer_text, font=footer_font)
    footer_x = (width - (footer_bbox[2] - footer_bbox[0])) // 2
    footer_text_y = footer_y + accent_height + int((footer_height - accent_height - (footer_bbox[3] - footer_bbox[1])) * 0.5)
    draw.text((footer_x, footer_text_y), footer_text, fill=color_gray_800, font=footer_font)
    
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
