import io
import os
import secrets
import qrcode
from PIL import Image, ImageDraw, ImageFont


def generate_default_filler(screen, booking_url=None, platform_url=None, platform_name=None, base_url=None):
    """
    Generate a professional default filler image for a screen.
    
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
    
    gradient_start = (5, 150, 105)
    gradient_end = (16, 185, 129)
    
    header_height = int(height * 0.30)
    for y in range(header_height):
        ratio = y / header_height
        r = int(gradient_start[0] + (gradient_end[0] - gradient_start[0]) * ratio)
        g = int(gradient_start[1] + (gradient_end[1] - gradient_start[1]) * ratio)
        b = int(gradient_start[2] + (gradient_end[2] - gradient_start[2]) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    footer_height = int(height * 0.12)
    footer_y = height - footer_height
    draw.rectangle([(0, footer_y), (width, height)], fill='#1f2937')
    
    try:
        title_size = max(int(min(width, height) * 0.06), 24)
        subtitle_size = max(int(min(width, height) * 0.035), 16)
        info_size = max(int(min(width, height) * 0.025), 14)
        cta_size = max(int(min(width, height) * 0.03), 16)
        footer_size = max(int(min(width, height) * 0.025), 14)
        
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", title_size)
        subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", subtitle_size)
        info_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", info_size)
        cta_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", cta_size)
        footer_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", footer_size)
    except:
        title_font = ImageFont.load_default()
        subtitle_font = title_font
        info_font = title_font
        cta_font = title_font
        footer_font = title_font
    
    org_name = screen.organization.name if screen.organization else 'Établissement'
    org_bbox = draw.textbbox((0, 0), org_name, font=title_font)
    org_x = (width - (org_bbox[2] - org_bbox[0])) // 2
    org_y = int(header_height * 0.15)
    draw.text((org_x, org_y), org_name, fill='white', font=title_font)
    
    screen_name = screen.name
    screen_bbox = draw.textbbox((0, 0), screen_name, font=subtitle_font)
    screen_x = (width - (screen_bbox[2] - screen_bbox[0])) // 2
    screen_y = org_y + int((org_bbox[3] - org_bbox[1]) * 1.5)
    draw.text((screen_x, screen_y), screen_name, fill='#d1fae5', font=subtitle_font)
    
    resolution_text = f"{screen.resolution_width} × {screen.resolution_height} px"
    res_bbox = draw.textbbox((0, 0), resolution_text, font=info_font)
    res_x = (width - (res_bbox[2] - res_bbox[0])) // 2
    res_y = screen_y + int((screen_bbox[3] - screen_bbox[1]) * 1.8)
    draw.text((res_x, res_y), resolution_text, fill='#a7f3d0', font=info_font)
    
    qr_size = int(min(width, height) * 0.25)
    qr_size = max(qr_size, 100)
    
    if booking_url is None:
        if base_url:
            booking_url = f"{base_url}/book/{screen.unique_code}"
        else:
            booking_url = f"https://shabaka-adscreen.com/book/{screen.unique_code}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(booking_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#059669", back_color="white").convert('RGB')
    qr_img = qr_img.resize((qr_size, qr_size), Image.LANCZOS)
    
    qr_box_padding = int(qr_size * 0.1)
    qr_box_size = qr_size + (qr_box_padding * 2)
    
    content_area_start = header_height
    content_area_end = footer_y
    content_area_height = content_area_end - content_area_start
    
    qr_center_y = content_area_start + int(content_area_height * 0.35)
    qr_x = (width - qr_box_size) // 2
    qr_y = qr_center_y - (qr_box_size // 2)
    
    corner_radius = int(qr_box_size * 0.08)
    draw.rounded_rectangle(
        [(qr_x, qr_y), (qr_x + qr_box_size, qr_y + qr_box_size)],
        radius=corner_radius,
        fill='white',
        outline='#e5e7eb',
        width=2
    )
    
    canvas.paste(qr_img, (qr_x + qr_box_padding, qr_y + qr_box_padding))
    
    cta_text = "Scannez pour réserver votre espace publicitaire"
    cta_bbox = draw.textbbox((0, 0), cta_text, font=cta_font)
    cta_x = (width - (cta_bbox[2] - cta_bbox[0])) // 2
    cta_y = qr_y + qr_box_size + int(content_area_height * 0.08)
    
    if cta_x < 20:
        cta_text = "Scannez pour réserver"
        cta_bbox = draw.textbbox((0, 0), cta_text, font=cta_font)
        cta_x = (width - (cta_bbox[2] - cta_bbox[0])) // 2
    
    draw.text((cta_x, cta_y), cta_text, fill='#374151', font=cta_font)
    
    sub_cta_text = "Diffusez votre publicité sur cet écran"
    sub_cta_bbox = draw.textbbox((0, 0), sub_cta_text, font=info_font)
    sub_cta_x = (width - (sub_cta_bbox[2] - sub_cta_bbox[0])) // 2
    sub_cta_y = cta_y + int((cta_bbox[3] - cta_bbox[1]) * 1.8)
    draw.text((sub_cta_x, sub_cta_y), sub_cta_text, fill='#6b7280', font=info_font)
    
    if platform_url is None:
        platform_url = 'www.shabaka-adscreen.com'
    
    if platform_name is None:
        platform_name = 'Shabaka AdScreen'
    
    footer_text = f"{platform_name}"
    footer_bbox = draw.textbbox((0, 0), footer_text, font=footer_font)
    footer_x = (width - (footer_bbox[2] - footer_bbox[0])) // 2
    footer_text_y = footer_y + (footer_height - (footer_bbox[3] - footer_bbox[1])) // 2 - int(footer_height * 0.15)
    draw.text((footer_x, footer_text_y), footer_text, fill='white', font=footer_font)
    
    url_text = platform_url
    url_bbox = draw.textbbox((0, 0), url_text, font=info_font)
    url_x = (width - (url_bbox[2] - url_bbox[0])) // 2
    url_y = footer_text_y + int((footer_bbox[3] - footer_bbox[1]) * 1.3)
    draw.text((url_x, url_y), url_text, fill='#9ca3af', font=info_font)
    
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
