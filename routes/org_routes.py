from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from app import db
from models import Screen, TimeSlot, TimePeriod, Content, Booking, Filler, InternalContent, StatLog, ScreenOverlay
from datetime import datetime, timedelta
from sqlalchemy import func
import os
import secrets
from werkzeug.utils import secure_filename

org_bp = Blueprint('org', __name__)


def org_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.is_superadmin():
            return redirect(url_for('admin.dashboard'))
        if not current_user.organization_id:
            flash('Vous devez être associé à un établissement.', 'error')
            return redirect(url_for('auth.logout'))
        return f(*args, **kwargs)
    return decorated_function


@org_bp.route('/dashboard')
@login_required
@org_required
def dashboard():
    from utils.currencies import get_currency_by_code
    
    org = current_user.organization
    screens = Screen.query.filter_by(organization_id=org.id).all()
    
    total_screens = len(screens)
    online_screens = len([s for s in screens if s.status in ['online', 'playing']])
    
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    
    pending_validations = Content.query.join(Screen).filter(
        Screen.organization_id == org.id,
        Content.status == 'pending'
    ).count()
    
    total_revenue = db.session.query(func.sum(Booking.total_price)).join(Screen).filter(
        Screen.organization_id == org.id,
        Booking.payment_status == 'paid'
    ).scalar() or 0
    
    weekly_revenue = db.session.query(func.sum(Booking.total_price)).join(Screen).filter(
        Screen.organization_id == org.id,
        Booking.payment_status == 'paid',
        Booking.created_at >= week_ago
    ).scalar() or 0
    
    recent_bookings = Booking.query.join(Screen).filter(
        Screen.organization_id == org.id
    ).order_by(Booking.created_at.desc()).limit(10).all()
    
    currency_info = get_currency_by_code(org.currency or 'EUR')
    currency_symbol = currency_info.get('symbol', org.currency or 'EUR')
    
    return render_template('org/dashboard.html',
        org=org,
        screens=screens,
        total_screens=total_screens,
        online_screens=online_screens,
        pending_validations=pending_validations,
        total_revenue=total_revenue,
        weekly_revenue=weekly_revenue,
        recent_bookings=recent_bookings,
        currency_symbol=currency_symbol
    )


@org_bp.route('/bookings')
@login_required
@org_required
def booking_history():
    from utils.currencies import get_currency_by_code
    
    org = current_user.organization
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    status_filter = request.args.get('status', 'all')
    screen_filter = request.args.get('screen', 'all')
    
    query = Booking.query.join(Screen).filter(
        Screen.organization_id == org.id
    )
    
    if status_filter != 'all':
        query = query.filter(Booking.status == status_filter)
    
    if screen_filter != 'all':
        try:
            screen_id = int(screen_filter)
            query = query.filter(Booking.screen_id == screen_id)
        except ValueError:
            pass
    
    bookings = query.order_by(Booking.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    screens = Screen.query.filter_by(organization_id=org.id).all()
    
    total_revenue = db.session.query(func.sum(Booking.total_price)).join(Screen).filter(
        Screen.organization_id == org.id,
        Booking.payment_status == 'paid'
    ).scalar() or 0
    
    total_vat = db.session.query(func.sum(Booking.vat_amount)).join(Screen).filter(
        Screen.organization_id == org.id,
        Booking.payment_status == 'paid'
    ).scalar() or 0
    
    currency_info = get_currency_by_code(org.currency or 'EUR')
    currency_symbol = currency_info.get('symbol', org.currency or 'EUR')
    
    return render_template('org/booking_history.html',
        org=org,
        bookings=bookings,
        screens=screens,
        status_filter=status_filter,
        screen_filter=screen_filter,
        total_revenue=total_revenue,
        total_vat=total_vat,
        currency_symbol=currency_symbol
    )


@org_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@org_required
def settings():
    from utils.currencies import get_all_currencies, get_country_choices, get_cities_for_country
    from models.site_setting import SiteSetting
    
    org = current_user.organization
    currencies = get_all_currencies()
    countries = get_country_choices()
    cities = get_cities_for_country(org.country or 'FR')
    registration_label = SiteSetting.get('registration_number_label', "Numéro d'immatriculation")
    
    timezones = [
        'UTC',
        'Africa/Abidjan', 'Africa/Accra', 'Africa/Algiers', 'Africa/Cairo', 'Africa/Casablanca',
        'Africa/Dakar', 'Africa/Johannesburg', 'Africa/Lagos', 'Africa/Nairobi', 'Africa/Tunis',
        'America/Bogota', 'America/Buenos_Aires', 'America/Caracas', 'America/Chicago',
        'America/Lima', 'America/Los_Angeles', 'America/Mexico_City', 'America/New_York',
        'America/Santiago', 'America/Sao_Paulo', 'America/Toronto',
        'Asia/Bangkok', 'Asia/Beirut', 'Asia/Dubai', 'Asia/Hong_Kong', 'Asia/Jakarta',
        'Asia/Kolkata', 'Asia/Riyadh', 'Asia/Seoul', 'Asia/Shanghai', 'Asia/Singapore',
        'Asia/Tokyo',
        'Australia/Melbourne', 'Australia/Sydney',
        'Europe/Amsterdam', 'Europe/Athens', 'Europe/Berlin', 'Europe/Brussels',
        'Europe/Dublin', 'Europe/Helsinki', 'Europe/Istanbul', 'Europe/Lisbon',
        'Europe/London', 'Europe/Madrid', 'Europe/Moscow', 'Europe/Paris',
        'Europe/Prague', 'Europe/Rome', 'Europe/Stockholm', 'Europe/Vienna', 'Europe/Warsaw',
        'Europe/Zurich',
        'Pacific/Auckland', 'Pacific/Fiji', 'Pacific/Honolulu'
    ]
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        country = request.form.get('country', org.country or 'FR')
        currency = request.form.get('currency', org.currency or 'EUR')
        timezone_input = request.form.get('timezone', org.timezone or 'UTC')
        
        if timezone_input not in timezones:
            timezone_input = 'UTC'
        
        business_name = request.form.get('business_name', '').strip()
        registration_number_label = request.form.get('registration_number_label', '').strip()
        business_registration_number = request.form.get('business_registration_number', '').strip()
        vat_number = request.form.get('vat_number', '').strip()
        try:
            vat_rate = float(request.form.get('vat_rate', 0) or 0)
            vat_rate = max(0, min(vat_rate, 100))
        except (ValueError, TypeError):
            vat_rate = 0
        
        if not name:
            flash('Le nom de l\'établissement est obligatoire.', 'error')
            return render_template('org/settings.html',
                org=org,
                currencies=currencies,
                countries=countries,
                cities=cities,
                timezones=timezones,
                registration_label=registration_label
            )
        
        org.name = name
        org.phone = phone
        org.address = address
        org.city = city
        org.country = country
        org.currency = currency
        org.timezone = timezone_input
        org.business_name = business_name
        org.registration_number_label = registration_number_label
        org.business_registration_number = business_registration_number
        org.vat_number = vat_number
        org.vat_rate = vat_rate
        db.session.commit()
        
        flash('Paramètres mis à jour avec succès!', 'success')
        return redirect(url_for('org.settings'))
    
    return render_template('org/settings.html',
        org=org,
        currencies=currencies,
        countries=countries,
        cities=cities,
        timezones=timezones,
        registration_label=registration_label
    )


@org_bp.route('/screens')
@login_required
@org_required
def screens():
    org = current_user.organization
    screens = Screen.query.filter_by(organization_id=org.id).order_by(Screen.created_at.desc()).all()
    return render_template('org/screens.html', screens=screens)


@org_bp.route('/screen/new', methods=['GET', 'POST'])
@login_required
@org_required
def new_screen():
    from utils.currencies import get_currency_by_code
    
    if request.method == 'POST':
        name = request.form.get('name')
        location = request.form.get('location')
        resolution_width = int(request.form.get('resolution_width', 1920))
        resolution_height = int(request.form.get('resolution_height', 1080))
        orientation = request.form.get('orientation', 'landscape')
        accepts_images = 'accepts_images' in request.form
        accepts_videos = 'accepts_videos' in request.form
        max_file_size = int(request.form.get('max_file_size', 50))
        password = request.form.get('password')
        price_per_minute = float(request.form.get('price_per_minute', 2.0))
        
        screen = Screen(
            name=name,
            location=location,
            resolution_width=resolution_width,
            resolution_height=resolution_height,
            orientation=orientation,
            accepts_images=accepts_images,
            accepts_videos=accepts_videos,
            max_file_size_mb=max_file_size,
            price_per_minute=price_per_minute,
            organization_id=current_user.organization_id
        )
        screen.set_password(password)
        
        if 'screen_image' in request.files:
            file = request.files['screen_image']
            if file.filename:
                filename = secure_filename(file.filename)
                ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
                if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                    new_filename = f"{secrets.token_hex(8)}_{filename}"
                    upload_path = os.path.join('static', 'uploads', 'screen_images', str(current_user.organization_id))
                    os.makedirs(upload_path, exist_ok=True)
                    file_path = os.path.join(upload_path, new_filename)
                    file.save(file_path)
                    screen.screen_image = file_path
        
        db.session.add(screen)
        db.session.flush()
        
        default_slots = [
            ('image', 10),
            ('image', 15),
            ('image', 30),
            ('video', 10),
            ('video', 15),
            ('video', 30),
        ]
        
        for content_type, duration in default_slots:
            calculated_price = screen.calculate_slot_price(duration)
            slot = TimeSlot(
                screen_id=screen.id,
                content_type=content_type,
                duration_seconds=duration,
                price_per_play=calculated_price
            )
            db.session.add(slot)
        
        default_periods = [
            ('Matin', 6, 12, 0.8),
            ('Midi', 12, 14, 1.2),
            ('Après-midi', 14, 18, 1.0),
            ('Soir', 18, 22, 1.5),
            ('Nuit', 22, 6, 0.5),
        ]
        
        for name_p, start, end, mult in default_periods:
            period = TimePeriod(
                screen_id=screen.id,
                name=name_p,
                start_hour=start,
                end_hour=end,
                price_multiplier=mult
            )
            db.session.add(period)
        
        db.session.commit()
        
        flash('Écran créé avec succès!', 'success')
        return redirect(url_for('org.screen_detail', screen_id=screen.id))
    
    org = current_user.organization
    currency_info = get_currency_by_code(org.currency or 'EUR')
    currency_symbol = currency_info.get('symbol', org.currency or 'EUR')
    
    return render_template('org/screen_form.html', screen=None, currency_symbol=currency_symbol)


@org_bp.route('/screen/<int:screen_id>')
@login_required
@org_required
def screen_detail(screen_id):
    from utils.currencies import get_currency_by_code
    
    screen = Screen.query.filter_by(
        id=screen_id,
        organization_id=current_user.organization_id
    ).first_or_404()
    
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    
    revenue = db.session.query(func.sum(Booking.total_price)).filter(
        Booking.screen_id == screen_id,
        Booking.payment_status == 'paid'
    ).scalar() or 0
    
    weekly_revenue = db.session.query(func.sum(Booking.total_price)).filter(
        Booking.screen_id == screen_id,
        Booking.payment_status == 'paid',
        Booking.created_at >= week_ago
    ).scalar() or 0
    
    total_plays = db.session.query(func.count(StatLog.id)).filter(
        StatLog.screen_id == screen_id
    ).scalar() or 0
    
    pending_count = Content.query.filter_by(
        screen_id=screen_id,
        status='pending'
    ).count()
    
    org = current_user.organization
    currency_info = get_currency_by_code(org.currency or 'EUR')
    currency_symbol = currency_info.get('symbol', org.currency or 'EUR')
    
    return render_template('org/screen_detail.html',
        screen=screen,
        revenue=revenue,
        weekly_revenue=weekly_revenue,
        total_plays=total_plays,
        pending_count=pending_count,
        currency_symbol=currency_symbol
    )


@org_bp.route('/screen/<int:screen_id>/edit', methods=['GET', 'POST'])
@login_required
@org_required
def edit_screen(screen_id):
    from utils.currencies import get_currency_by_code
    
    screen = Screen.query.filter_by(
        id=screen_id,
        organization_id=current_user.organization_id
    ).first_or_404()
    
    if request.method == 'POST':
        screen.name = request.form.get('name')
        screen.location = request.form.get('location')
        screen.resolution_width = int(request.form.get('resolution_width', 1920))
        screen.resolution_height = int(request.form.get('resolution_height', 1080))
        screen.orientation = request.form.get('orientation', 'landscape')
        screen.accepts_images = 'accepts_images' in request.form
        screen.accepts_videos = 'accepts_videos' in request.form
        screen.max_file_size_mb = int(request.form.get('max_file_size', 50))
        
        new_price_per_minute = float(request.form.get('price_per_minute', 2.0))
        screen.price_per_minute = new_price_per_minute
        
        recalculate_slots = 'recalculate_slots' in request.form
        if recalculate_slots:
            for slot in screen.time_slots:
                slot.price_per_play = screen.calculate_slot_price(slot.duration_seconds)
        
        if 'remove_screen_image' in request.form and screen.screen_image:
            if os.path.exists(screen.screen_image):
                os.remove(screen.screen_image)
            screen.screen_image = None
        elif 'screen_image' in request.files:
            file = request.files['screen_image']
            if file.filename:
                filename = secure_filename(file.filename)
                ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
                if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                    if screen.screen_image and os.path.exists(screen.screen_image):
                        os.remove(screen.screen_image)
                    new_filename = f"{secrets.token_hex(8)}_{filename}"
                    upload_path = os.path.join('static', 'uploads', 'screen_images', str(current_user.organization_id))
                    os.makedirs(upload_path, exist_ok=True)
                    file_path = os.path.join(upload_path, new_filename)
                    file.save(file_path)
                    screen.screen_image = file_path
        
        new_password = request.form.get('password')
        if new_password:
            screen.set_password(new_password)
        
        db.session.commit()
        flash('Écran mis à jour avec succès!', 'success')
        return redirect(url_for('org.screen_detail', screen_id=screen.id))
    
    org = current_user.organization
    currency_info = get_currency_by_code(org.currency or 'EUR')
    currency_symbol = currency_info.get('symbol', org.currency or 'EUR')
    
    return render_template('org/screen_form.html', screen=screen, currency_symbol=currency_symbol)


@org_bp.route('/screen/<int:screen_id>/slots', methods=['GET', 'POST'])
@login_required
@org_required
def screen_slots(screen_id):
    from utils.currencies import get_currency_by_code
    
    screen = Screen.query.filter_by(
        id=screen_id,
        organization_id=current_user.organization_id
    ).first_or_404()
    
    if request.method == 'POST':
        TimeSlot.query.filter_by(screen_id=screen_id).delete()
        
        content_types = request.form.getlist('slot_type[]')
        durations = request.form.getlist('slot_duration[]')
        prices = request.form.getlist('slot_price[]')
        
        for i in range(len(content_types)):
            if content_types[i] and durations[i] and prices[i]:
                slot = TimeSlot(
                    screen_id=screen_id,
                    content_type=content_types[i],
                    duration_seconds=int(durations[i]),
                    price_per_play=float(prices[i])
                )
                db.session.add(slot)
        
        db.session.commit()
        flash('Créneaux mis à jour avec succès!', 'success')
        return redirect(url_for('org.screen_detail', screen_id=screen_id))
    
    org = current_user.organization
    currency_info = get_currency_by_code(org.currency or 'EUR')
    currency_symbol = currency_info.get('symbol', org.currency or 'EUR')
    
    return render_template('org/screen_slots.html', screen=screen, currency_symbol=currency_symbol)


@org_bp.route('/screen/<int:screen_id>/periods', methods=['GET', 'POST'])
@login_required
@org_required
def screen_periods(screen_id):
    from utils.currencies import get_currency_by_code
    
    screen = Screen.query.filter_by(
        id=screen_id,
        organization_id=current_user.organization_id
    ).first_or_404()
    
    if request.method == 'POST':
        TimePeriod.query.filter_by(screen_id=screen_id).delete()
        
        names = request.form.getlist('period_name[]')
        starts = request.form.getlist('period_start[]')
        ends = request.form.getlist('period_end[]')
        multipliers = request.form.getlist('period_multiplier[]')
        
        for i in range(len(names)):
            if names[i] and starts[i] and ends[i] and multipliers[i]:
                period = TimePeriod(
                    screen_id=screen_id,
                    name=names[i],
                    start_hour=int(starts[i]),
                    end_hour=int(ends[i]),
                    price_multiplier=float(multipliers[i])
                )
                db.session.add(period)
        
        db.session.commit()
        flash('Périodes mises à jour avec succès!', 'success')
        return redirect(url_for('org.screen_detail', screen_id=screen_id))
    
    org = current_user.organization
    currency_info = get_currency_by_code(org.currency or 'EUR')
    currency_symbol = currency_info.get('symbol', org.currency or 'EUR')
    
    return render_template('org/screen_periods.html', screen=screen, currency_symbol=currency_symbol)


@org_bp.route('/screen/<int:screen_id>/fillers', methods=['GET', 'POST'])
@login_required
@org_required
def screen_fillers(screen_id):
    screen = Screen.query.filter_by(
        id=screen_id,
        organization_id=current_user.organization_id
    ).first_or_404()
    
    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            if file.filename:
                filename = secure_filename(file.filename)
                ext = filename.rsplit('.', 1)[-1].lower()
                
                if ext in ['jpg', 'jpeg', 'png', 'gif']:
                    content_type = 'image'
                elif ext in ['mp4', 'webm', 'mov']:
                    content_type = 'video'
                else:
                    flash('Format de fichier non supporté.', 'error')
                    return redirect(url_for('org.screen_fillers', screen_id=screen_id))
                
                new_filename = f"{secrets.token_hex(8)}_{filename}"
                upload_path = os.path.join('static', 'uploads', 'fillers', str(screen_id))
                os.makedirs(upload_path, exist_ok=True)
                file_path = os.path.join(upload_path, new_filename)
                file.save(file_path)
                
                duration = None
                if content_type == 'video':
                    from utils.video_utils import get_video_duration
                    duration = get_video_duration(file_path)
                
                filler = Filler(
                    screen_id=screen_id,
                    filename=new_filename,
                    content_type=content_type,
                    file_path=file_path,
                    duration_seconds=duration
                )
                db.session.add(filler)
                db.session.commit()
                
                flash('Filler ajouté avec succès!', 'success')
        
        return redirect(url_for('org.screen_fillers', screen_id=screen_id))
    
    fillers = Filler.query.filter_by(screen_id=screen_id).all()
    return render_template('org/screen_fillers.html', screen=screen, fillers=fillers)


@org_bp.route('/screen/<int:screen_id>/filler/<int:filler_id>/delete', methods=['POST'])
@login_required
@org_required
def delete_filler(screen_id, filler_id):
    screen = Screen.query.filter_by(
        id=screen_id,
        organization_id=current_user.organization_id
    ).first_or_404()
    
    filler = Filler.query.filter_by(id=filler_id, screen_id=screen_id).first_or_404()
    
    if os.path.exists(filler.file_path):
        os.remove(filler.file_path)
    
    db.session.delete(filler)
    db.session.commit()
    
    flash('Filler supprimé.', 'success')
    return redirect(url_for('org.screen_fillers', screen_id=screen_id))


@org_bp.route('/screen/<int:screen_id>/internal', methods=['GET', 'POST'])
@login_required
@org_required
def screen_internal(screen_id):
    screen = Screen.query.filter_by(
        id=screen_id,
        organization_id=current_user.organization_id
    ).first_or_404()
    
    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            name = request.form.get('name', 'Contenu interne')
            priority = int(request.form.get('priority', 80))
            
            if file.filename:
                filename = secure_filename(file.filename)
                ext = filename.rsplit('.', 1)[-1].lower()
                
                if ext in ['jpg', 'jpeg', 'png', 'gif']:
                    content_type = 'image'
                elif ext in ['mp4', 'webm', 'mov']:
                    content_type = 'video'
                else:
                    flash('Format de fichier non supporté.', 'error')
                    return redirect(url_for('org.screen_internal', screen_id=screen_id))
                
                new_filename = f"{secrets.token_hex(8)}_{filename}"
                upload_path = os.path.join('static', 'uploads', 'internal', str(screen_id))
                os.makedirs(upload_path, exist_ok=True)
                file_path = os.path.join(upload_path, new_filename)
                file.save(file_path)
                
                duration = None
                if content_type == 'video':
                    from utils.video_utils import get_video_duration
                    duration = get_video_duration(file_path)
                
                internal = InternalContent(
                    screen_id=screen_id,
                    name=name,
                    filename=new_filename,
                    content_type=content_type,
                    file_path=file_path,
                    duration_seconds=duration,
                    priority=priority
                )
                db.session.add(internal)
                db.session.commit()
                
                flash('Contenu interne ajouté avec succès!', 'success')
        
        return redirect(url_for('org.screen_internal', screen_id=screen_id))
    
    internals = InternalContent.query.filter_by(screen_id=screen_id).order_by(InternalContent.priority.desc()).all()
    return render_template('org/screen_internal.html', screen=screen, internals=internals)


@org_bp.route('/validations')
@login_required
@org_required
def validations():
    org = current_user.organization
    
    pending = Content.query.join(Screen).filter(
        Screen.organization_id == org.id,
        Content.status == 'pending'
    ).order_by(Content.created_at.asc()).all()
    
    return render_template('org/validations.html', contents=pending)


@org_bp.route('/validation/<int:content_id>/approve', methods=['POST'])
@login_required
@org_required
def approve_content(content_id):
    content = Content.query.join(Screen).filter(
        Content.id == content_id,
        Screen.organization_id == current_user.organization_id
    ).first_or_404()
    
    content.status = 'approved'
    content.validated_at = datetime.utcnow()
    content.in_playlist = True
    
    if content.booking:
        content.booking.status = 'active'
    
    db.session.commit()
    
    flash('Contenu approuvé et ajouté à la playlist!', 'success')
    return redirect(url_for('org.validations'))


@org_bp.route('/validation/<int:content_id>/reject', methods=['POST'])
@login_required
@org_required
def reject_content(content_id):
    content = Content.query.join(Screen).filter(
        Content.id == content_id,
        Screen.organization_id == current_user.organization_id
    ).first_or_404()
    
    reason = request.form.get('reason', 'Contenu non conforme')
    
    content.status = 'rejected'
    content.rejection_reason = reason
    content.validated_at = datetime.utcnow()
    
    if content.booking:
        content.booking.status = 'rejected'
    
    db.session.commit()
    
    flash('Contenu refusé.', 'info')
    return redirect(url_for('org.validations'))


@org_bp.route('/screen/<int:screen_id>/overlays', methods=['GET', 'POST'])
@login_required
@org_required
def screen_overlays(screen_id):
    screen = Screen.query.filter_by(
        id=screen_id,
        organization_id=current_user.organization_id
    ).first_or_404()
    
    if request.method == 'POST':
        overlay_type = request.form.get('overlay_type', 'ticker')
        message = request.form.get('message', '')
        
        if overlay_type == 'ticker':
            position = request.form.get('position', 'footer')
            position_mode = 'linear'
            corner_position_value = 'top_left'
        else:
            image_position = request.form.get('image_position', 'top_right')
            if image_position in ['header', 'body', 'footer']:
                position = image_position
                position_mode = 'linear'
                corner_position_value = 'top_left'
            elif image_position == 'custom':
                position = 'custom'
                position_mode = 'custom'
                corner_position_value = 'top_left'
            else:
                position = 'corner'
                position_mode = 'corner'
                corner_position_value = image_position
        
        background_color = request.form.get('background_color', '#1f2937')
        text_color = request.form.get('text_color', '#ffffff')
        font_size = int(request.form.get('font_size', 28))
        scroll_speed = int(request.form.get('scroll_speed', 60))
        is_active = 'is_active' in request.form
        
        frequency_type = request.form.get('frequency_type', 'duration')
        frequency_unit = request.form.get('frequency_unit', 'day')
        
        if frequency_type == 'duration':
            display_duration = int(request.form.get('display_duration', 10))
            passage_limit = 0
        else:
            display_duration = 0
            passage_limit = int(request.form.get('passage_limit', 10))
        
        start_time_str = request.form.get('start_time', '')
        end_time_str = request.form.get('end_time', '')
        start_time = datetime.fromisoformat(start_time_str) if start_time_str else None
        end_time = datetime.fromisoformat(end_time_str) if end_time_str else None
        
        image_width_percent = float(request.form.get('image_width_percent', 20))
        image_pos_x = int(request.form.get('image_pos_x', 50))
        image_pos_y = int(request.form.get('image_pos_y', 50))
        image_opacity = float(request.form.get('image_opacity', 1.0))
        
        image_path = None
        image_width = 0
        image_height = 0
        if overlay_type == 'image' and 'image_file' in request.files:
            file = request.files['image_file']
            if file.filename:
                filename = secure_filename(file.filename)
                new_filename = f"{secrets.token_hex(8)}_{filename}"
                upload_path = os.path.join('static', 'uploads', 'overlays', str(screen_id))
                os.makedirs(upload_path, exist_ok=True)
                file_path = os.path.join(upload_path, new_filename)
                file.save(file_path)
                image_path = file_path
                
                try:
                    from PIL import Image
                    with Image.open(file_path) as img:
                        image_width, image_height = img.size
                except:
                    pass
        
        corner_size = int(request.form.get('corner_size', 15))
        
        overlay = ScreenOverlay(
            screen_id=screen_id,
            overlay_type=overlay_type,
            message=message if overlay_type == 'ticker' else None,
            image_path=image_path,
            position=position,
            position_mode=position_mode,
            corner_position=corner_position_value,
            corner_size=corner_size,
            background_color=background_color,
            text_color=text_color,
            font_size=font_size,
            scroll_speed=scroll_speed,
            frequency_type=frequency_type,
            display_duration=display_duration,
            passage_limit=passage_limit,
            frequency_unit=frequency_unit,
            start_time=start_time,
            end_time=end_time,
            image_width=image_width,
            image_height=image_height,
            image_width_percent=image_width_percent,
            image_pos_x=image_pos_x,
            image_pos_y=image_pos_y,
            image_opacity=image_opacity,
            is_active=is_active
        )
        db.session.add(overlay)
        db.session.commit()
        
        flash('Overlay ajouté avec succès!', 'success')
        return redirect(url_for('org.screen_overlays', screen_id=screen_id))
    
    overlays = ScreenOverlay.query.filter_by(screen_id=screen_id).order_by(ScreenOverlay.created_at.desc()).all()
    return render_template('org/screen_overlays.html', screen=screen, overlays=overlays)


@org_bp.route('/screen/<int:screen_id>/overlay/<int:overlay_id>/toggle', methods=['POST'])
@login_required
@org_required
def toggle_overlay(screen_id, overlay_id):
    screen = Screen.query.filter_by(
        id=screen_id,
        organization_id=current_user.organization_id
    ).first_or_404()
    
    overlay = ScreenOverlay.query.filter_by(id=overlay_id, screen_id=screen_id).first_or_404()
    overlay.is_active = not overlay.is_active
    db.session.commit()
    
    status = 'activé' if overlay.is_active else 'désactivé'
    flash(f'Overlay {status}!', 'success')
    return redirect(url_for('org.screen_overlays', screen_id=screen_id))


@org_bp.route('/screen/<int:screen_id>/overlay/<int:overlay_id>/delete', methods=['POST'])
@login_required
@org_required
def delete_overlay(screen_id, overlay_id):
    screen = Screen.query.filter_by(
        id=screen_id,
        organization_id=current_user.organization_id
    ).first_or_404()
    
    overlay = ScreenOverlay.query.filter_by(id=overlay_id, screen_id=screen_id).first_or_404()
    
    if overlay.image_path and os.path.exists(overlay.image_path):
        os.remove(overlay.image_path)
    
    db.session.delete(overlay)
    db.session.commit()
    
    flash('Overlay supprimé.', 'success')
    return redirect(url_for('org.screen_overlays', screen_id=screen_id))


@org_bp.route('/contents')
@login_required
@org_required
def contents():
    org = current_user.organization
    
    all_contents = Content.query.join(Screen).filter(
        Screen.organization_id == org.id
    ).order_by(Content.created_at.desc()).all()
    
    all_internals = InternalContent.query.join(Screen).filter(
        Screen.organization_id == org.id
    ).order_by(InternalContent.created_at.desc()).all()
    
    all_fillers = Filler.query.join(Screen).filter(
        Screen.organization_id == org.id
    ).order_by(Filler.created_at.desc()).all()
    
    screens = Screen.query.filter_by(organization_id=org.id).all()
    
    return render_template('org/contents.html',
        contents=all_contents,
        internals=all_internals,
        fillers=all_fillers,
        screens=screens
    )




@org_bp.route('/screen/<int:screen_id>/filler/<int:filler_id>/toggle', methods=['POST'])
@login_required
@org_required
def toggle_filler(screen_id, filler_id):
    screen = Screen.query.filter_by(
        id=screen_id,
        organization_id=current_user.organization_id
    ).first_or_404()
    
    filler = Filler.query.filter_by(id=filler_id, screen_id=screen_id).first_or_404()
    filler.is_active = not filler.is_active
    db.session.commit()
    
    status = 'activé' if filler.is_active else 'désactivé'
    flash(f'Filler {status}!', 'success')
    return redirect(request.referrer or url_for('org.screen_fillers', screen_id=screen_id))


@org_bp.route('/screen/<int:screen_id>/internal/<int:internal_id>/toggle', methods=['POST'])
@login_required
@org_required
def toggle_screen_internal(screen_id, internal_id):
    screen = Screen.query.filter_by(
        id=screen_id,
        organization_id=current_user.organization_id
    ).first_or_404()
    
    internal = InternalContent.query.filter_by(id=internal_id, screen_id=screen_id).first_or_404()
    internal.is_active = not internal.is_active
    db.session.commit()
    
    status = 'activé' if internal.is_active else 'désactivé'
    flash(f'Contenu interne {status}!', 'success')
    return redirect(request.referrer or url_for('org.screen_internal', screen_id=screen_id))


@org_bp.route('/screen/<int:screen_id>/internal/<int:internal_id>/delete', methods=['POST'])
@login_required
@org_required
def delete_screen_internal(screen_id, internal_id):
    screen = Screen.query.filter_by(
        id=screen_id,
        organization_id=current_user.organization_id
    ).first_or_404()
    
    internal = InternalContent.query.filter_by(id=internal_id, screen_id=screen_id).first_or_404()
    
    if internal.file_path and os.path.exists(internal.file_path):
        os.remove(internal.file_path)
    
    db.session.delete(internal)
    db.session.commit()
    
    flash('Contenu interne supprimé.', 'success')
    return redirect(request.referrer or url_for('org.screen_internal', screen_id=screen_id))


@org_bp.route('/stats')
@login_required
@org_required
def stats():
    org = current_user.organization
    
    today = datetime.utcnow().date()
    month_ago = today - timedelta(days=30)
    
    daily_revenue = db.session.query(
        func.date(Booking.created_at).label('date'),
        func.sum(Booking.total_price).label('revenue')
    ).join(Screen).filter(
        Screen.organization_id == org.id,
        Booking.payment_status == 'paid',
        Booking.created_at >= month_ago
    ).group_by(func.date(Booking.created_at)).all()
    
    screen_stats = db.session.query(
        Screen.name,
        func.sum(Booking.total_price).label('revenue'),
        func.count(Booking.id).label('bookings')
    ).join(Booking).filter(
        Screen.organization_id == org.id,
        Booking.payment_status == 'paid'
    ).group_by(Screen.id).all()
    
    period_stats = db.session.query(
        TimePeriod.name,
        func.count(Booking.id).label('count')
    ).join(Booking, Booking.time_period_id == TimePeriod.id).join(Screen).filter(
        Screen.organization_id == org.id,
        Booking.payment_status == 'paid'
    ).group_by(TimePeriod.name).all()
    
    ad_stats = db.session.query(
        Content.id,
        Content.client_name,
        Content.original_filename,
        Content.content_type,
        Content.status,
        Screen.name.label('screen_name'),
        Booking.total_price,
        Booking.start_date,
        Booking.end_date,
        Booking.num_plays,
        func.count(StatLog.id).label('play_count')
    ).select_from(Content).join(
        Screen, Content.screen_id == Screen.id
    ).outerjoin(
        Booking, Booking.content_id == Content.id
    ).outerjoin(
        StatLog, StatLog.content_id == Content.id
    ).filter(
        Screen.organization_id == org.id
    ).group_by(
        Content.id, Content.client_name, Content.original_filename, 
        Content.content_type, Content.status, Content.created_at,
        Screen.name, Booking.id, Booking.total_price, 
        Booking.start_date, Booking.end_date, Booking.num_plays
    ).order_by(Content.created_at.desc()).all()
    
    return render_template('org/stats.html',
        daily_revenue=daily_revenue,
        screen_stats=screen_stats,
        period_stats=period_stats,
        ad_stats=ad_stats
    )


@org_bp.route('/content/<int:content_id>/suspend', methods=['POST'])
@login_required
@org_required
def suspend_content(content_id):
    content = Content.query.join(Screen).filter(
        Content.id == content_id,
        Screen.organization_id == current_user.organization_id
    ).first_or_404()
    
    content.status = 'suspended'
    if content.booking:
        content.booking.status = 'suspended'
    
    db.session.commit()
    
    flash('Contenu suspendu.', 'info')
    return redirect(request.referrer or url_for('org.contents'))


@org_bp.route('/content/<int:content_id>/activate', methods=['POST'])
@login_required
@org_required
def activate_content(content_id):
    content = Content.query.join(Screen).filter(
        Content.id == content_id,
        Screen.organization_id == current_user.organization_id
    ).first_or_404()
    
    content.status = 'approved'
    if content.booking:
        content.booking.status = 'active'
    
    db.session.commit()
    
    flash('Contenu activé!', 'success')
    return redirect(request.referrer or url_for('org.contents'))


@org_bp.route('/content/<int:content_id>/delete', methods=['POST'])
@login_required
@org_required
def delete_content(content_id):
    content = Content.query.join(Screen).filter(
        Content.id == content_id,
        Screen.organization_id == current_user.organization_id
    ).first_or_404()
    
    if content.file_path and os.path.exists(content.file_path):
        os.remove(content.file_path)
    
    if content.booking:
        db.session.delete(content.booking)
    
    db.session.delete(content)
    db.session.commit()
    
    flash('Contenu supprimé.', 'success')
    return redirect(request.referrer or url_for('org.contents'))


@org_bp.route('/screen/<int:screen_id>/playlist')
@login_required
@org_required
def screen_playlist(screen_id):
    screen = Screen.query.filter_by(
        id=screen_id,
        organization_id=current_user.organization_id
    ).first_or_404()
    
    from datetime import date
    today = date.today()
    
    paid_contents = Content.query.join(Booking).filter(
        Content.screen_id == screen_id,
        Content.status == 'approved',
        Booking.status == 'active',
        ((Booking.start_date <= today) | (Booking.start_date == None)),
        ((Booking.end_date >= today) | (Booking.end_date == None))
    ).all()
    
    internal_contents = InternalContent.query.filter_by(
        screen_id=screen_id,
        is_active=True
    ).order_by(InternalContent.priority.desc()).all()
    
    fillers = Filler.query.filter_by(
        screen_id=screen_id,
        is_active=True
    ).all()
    
    overlays = ScreenOverlay.query.filter_by(
        screen_id=screen_id,
        is_active=True
    ).all()
    
    return render_template('org/screen_playlist.html',
        screen=screen,
        paid_contents=paid_contents,
        internal_contents=internal_contents,
        fillers=fillers,
        overlays=overlays
    )


@org_bp.route('/content/<int:content_id>/remove-from-playlist', methods=['POST'])
@login_required
@org_required
def remove_content_from_playlist(content_id):
    content = Content.query.join(Screen).filter(
        Content.id == content_id,
        Screen.organization_id == current_user.organization_id
    ).first_or_404()
    
    content.in_playlist = False
    db.session.commit()
    
    flash('Contenu retiré de la playlist.', 'info')
    return redirect(request.referrer or url_for('org.contents'))


@org_bp.route('/content/<int:content_id>/add-to-playlist', methods=['POST'])
@login_required
@org_required
def add_content_to_playlist(content_id):
    content = Content.query.join(Screen).filter(
        Content.id == content_id,
        Screen.organization_id == current_user.organization_id
    ).first_or_404()
    
    content.in_playlist = True
    db.session.commit()
    
    flash('Contenu ajouté à la playlist!', 'success')
    return redirect(request.referrer or url_for('org.contents'))


@org_bp.route('/filler/<int:filler_id>/remove-from-playlist', methods=['POST'])
@login_required
@org_required
def remove_filler_from_playlist(filler_id):
    filler = Filler.query.join(Screen).filter(
        Filler.id == filler_id,
        Screen.organization_id == current_user.organization_id
    ).first_or_404()
    
    filler.in_playlist = False
    db.session.commit()
    
    flash('Filler retiré de la playlist.', 'info')
    return redirect(request.referrer or url_for('org.contents'))


@org_bp.route('/filler/<int:filler_id>/add-to-playlist', methods=['POST'])
@login_required
@org_required
def add_filler_to_playlist(filler_id):
    filler = Filler.query.join(Screen).filter(
        Filler.id == filler_id,
        Screen.organization_id == current_user.organization_id
    ).first_or_404()
    
    filler.in_playlist = True
    db.session.commit()
    
    flash('Filler ajouté à la playlist!', 'success')
    return redirect(request.referrer or url_for('org.contents'))


@org_bp.route('/internal/<int:internal_id>/remove-from-playlist', methods=['POST'])
@login_required
@org_required
def remove_internal_from_playlist(internal_id):
    internal = InternalContent.query.join(Screen).filter(
        InternalContent.id == internal_id,
        Screen.organization_id == current_user.organization_id
    ).first_or_404()
    
    internal.in_playlist = False
    db.session.commit()
    
    flash('Contenu interne retiré de la playlist.', 'info')
    return redirect(request.referrer or url_for('org.contents'))


@org_bp.route('/internal/<int:internal_id>/add-to-playlist', methods=['POST'])
@login_required
@org_required
def add_internal_to_playlist(internal_id):
    internal = InternalContent.query.join(Screen).filter(
        InternalContent.id == internal_id,
        Screen.organization_id == current_user.organization_id
    ).first_or_404()
    
    internal.in_playlist = True
    db.session.commit()
    
    flash('Contenu interne ajouté à la playlist!', 'success')
    return redirect(request.referrer or url_for('org.contents'))


@org_bp.route('/booking/<int:booking_id>/receipt/image')
@login_required
@org_required
def download_receipt_image(booking_id):
    from flask import send_file, Response
    from services.receipt_generator import generate_receipt_image
    from services.qr_service import generate_qr_base64
    import io
    
    booking = Booking.query.join(Screen).filter(
        Booking.id == booking_id,
        Screen.organization_id == current_user.organization_id
    ).first_or_404()
    
    screen = booking.screen
    content = booking.content
    
    if not content:
        flash('Contenu non trouvé.', 'error')
        return redirect(url_for('org.booking_history'))
    
    booking_url = url_for('booking.screen_booking', screen_code=screen.unique_code, _external=True)
    qr_base64 = generate_qr_base64(booking_url)
    
    img = generate_receipt_image(booking, screen, content, qr_base64)
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    filename = f"recu_{booking.reservation_number or booking_id}.png"
    return send_file(buffer, mimetype='image/png', as_attachment=True, download_name=filename)


@org_bp.route('/booking/<int:booking_id>/receipt/pdf')
@login_required
@org_required
def download_receipt_pdf(booking_id):
    from flask import send_file
    from services.receipt_generator import generate_receipt_pdf
    from services.qr_service import generate_qr_base64
    
    booking = Booking.query.join(Screen).filter(
        Booking.id == booking_id,
        Screen.organization_id == current_user.organization_id
    ).first_or_404()
    
    screen = booking.screen
    content = booking.content
    
    if not content:
        flash('Contenu non trouvé.', 'error')
        return redirect(url_for('org.booking_history'))
    
    booking_url = url_for('booking.screen_booking', screen_code=screen.unique_code, _external=True)
    qr_base64 = generate_qr_base64(booking_url)
    
    pdf_buffer = generate_receipt_pdf(booking, screen, content, qr_base64)
    pdf_buffer.seek(0)
    
    filename = f"recu_{booking.reservation_number or booking_id}.pdf"
    return send_file(pdf_buffer, mimetype='application/pdf', as_attachment=True, download_name=filename)


@org_bp.route('/screen/<int:screen_id>/availability')
@login_required
@org_required
def screen_availability(screen_id):
    from services.availability_service import calculate_availability, get_period_duration_seconds
    from utils.currencies import get_currency_by_code
    from datetime import date
    
    screen = Screen.query.filter_by(
        id=screen_id,
        organization_id=current_user.organization_id
    ).first_or_404()
    
    today = date.today()
    week_end = today + timedelta(days=7)
    
    availability_data = calculate_availability(
        screen, today.isoformat(), week_end.isoformat()
    )
    
    period_capacity = []
    for period in screen.time_periods:
        period_seconds = get_period_duration_seconds(period)
        period_hours = period_seconds / 3600
        
        slot_capacities = []
        for slot in screen.time_slots:
            max_plays = period_seconds // slot.duration_seconds
            slot_capacities.append({
                'duration': slot.duration_seconds,
                'content_type': slot.content_type,
                'max_plays': max_plays,
                'price': slot.price_per_play,
                'price_with_mult': round(slot.price_per_play * period.price_multiplier, 2)
            })
        
        period_capacity.append({
            'name': period.name,
            'start_hour': period.start_hour,
            'end_hour': period.end_hour,
            'hours': period_hours,
            'seconds': period_seconds,
            'multiplier': period.price_multiplier,
            'slot_capacities': slot_capacities
        })
    
    org = current_user.organization
    currency_info = get_currency_by_code(org.currency or 'EUR')
    currency_symbol = currency_info.get('symbol', org.currency or 'EUR')
    
    return render_template('org/screen_availability.html',
        screen=screen,
        availability=availability_data,
        period_capacity=period_capacity,
        today=today,
        week_end=week_end,
        currency_symbol=currency_symbol
    )
