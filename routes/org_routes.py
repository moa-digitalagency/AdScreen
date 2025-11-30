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
    
    return render_template('org/dashboard.html',
        org=org,
        screens=screens,
        total_screens=total_screens,
        online_screens=online_screens,
        pending_validations=pending_validations,
        total_revenue=total_revenue,
        weekly_revenue=weekly_revenue,
        recent_bookings=recent_bookings
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
        
        screen = Screen(
            name=name,
            location=location,
            resolution_width=resolution_width,
            resolution_height=resolution_height,
            orientation=orientation,
            accepts_images=accepts_images,
            accepts_videos=accepts_videos,
            max_file_size_mb=max_file_size,
            organization_id=current_user.organization_id
        )
        screen.set_password(password)
        
        db.session.add(screen)
        db.session.flush()
        
        default_slots = [
            ('image', 5, 0.30),
            ('image', 10, 0.50),
            ('image', 15, 0.70),
            ('video', 10, 0.60),
            ('video', 15, 0.80),
            ('video', 30, 1.50),
        ]
        
        for content_type, duration, price in default_slots:
            slot = TimeSlot(
                screen_id=screen.id,
                content_type=content_type,
                duration_seconds=duration,
                price_per_play=price
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
    
    return render_template('org/screen_form.html', screen=None)


@org_bp.route('/screen/<int:screen_id>')
@login_required
@org_required
def screen_detail(screen_id):
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
    
    return render_template('org/screen_detail.html',
        screen=screen,
        revenue=revenue,
        weekly_revenue=weekly_revenue,
        total_plays=total_plays,
        pending_count=pending_count
    )


@org_bp.route('/screen/<int:screen_id>/edit', methods=['GET', 'POST'])
@login_required
@org_required
def edit_screen(screen_id):
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
        
        new_password = request.form.get('password')
        if new_password:
            screen.set_password(new_password)
        
        db.session.commit()
        flash('Écran mis à jour avec succès!', 'success')
        return redirect(url_for('org.screen_detail', screen_id=screen.id))
    
    return render_template('org/screen_form.html', screen=screen)


@org_bp.route('/screen/<int:screen_id>/slots', methods=['GET', 'POST'])
@login_required
@org_required
def screen_slots(screen_id):
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
    
    return render_template('org/screen_slots.html', screen=screen)


@org_bp.route('/screen/<int:screen_id>/periods', methods=['GET', 'POST'])
@login_required
@org_required
def screen_periods(screen_id):
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
    
    return render_template('org/screen_periods.html', screen=screen)


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
    
    if content.booking:
        content.booking.status = 'active'
    
    db.session.commit()
    
    flash('Contenu approuvé!', 'success')
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
        position = request.form.get('position', 'footer')
        background_color = request.form.get('background_color', '#1f2937')
        text_color = request.form.get('text_color', '#ffffff')
        font_size = int(request.form.get('font_size', 24))
        scroll_speed = int(request.form.get('scroll_speed', 50))
        is_active = 'is_active' in request.form
        
        image_path = None
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
        
        overlay = ScreenOverlay(
            screen_id=screen_id,
            overlay_type=overlay_type,
            message=message if overlay_type == 'ticker' else None,
            image_path=image_path,
            position=position,
            background_color=background_color,
            text_color=text_color,
            font_size=font_size,
            scroll_speed=scroll_speed,
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
        Booking.plays_per_hour,
        func.count(StatLog.id).label('play_count')
    ).join(Screen).outerjoin(Booking).outerjoin(
        StatLog, StatLog.content_id == Content.id
    ).filter(
        Screen.organization_id == org.id
    ).group_by(
        Content.id, Content.client_name, Content.original_filename, 
        Content.content_type, Content.status, Content.created_at,
        Screen.name, Booking.id, Booking.total_price, 
        Booking.start_date, Booking.end_date, Booking.plays_per_hour
    ).order_by(Content.created_at.desc()).all()
    
    return render_template('org/stats.html',
        daily_revenue=daily_revenue,
        screen_stats=screen_stats,
        period_stats=period_stats,
        ad_stats=ad_stats
    )
