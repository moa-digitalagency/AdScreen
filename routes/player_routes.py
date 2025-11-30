from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from app import db
from models import Screen, Content, Booking, Filler, InternalContent, StatLog, HeartbeatLog, ScreenOverlay
from datetime import datetime

player_bp = Blueprint('player', __name__)


@player_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        screen_code = request.form.get('screen_code')
        password = request.form.get('password')
        
        screen = Screen.query.filter_by(unique_code=screen_code).first()
        
        if screen and screen.check_password(password):
            if not screen.is_active:
                flash('Cet écran a été désactivé.', 'error')
                return render_template('player/login.html')
            
            session['screen_id'] = screen.id
            session['screen_code'] = screen.unique_code
            return redirect(url_for('player.display'))
        
        flash('Code écran ou mot de passe incorrect.', 'error')
    
    return render_template('player/login.html')


@player_bp.route('/display')
def display():
    if 'screen_id' not in session:
        return redirect(url_for('player.login'))
    
    screen = Screen.query.get(session['screen_id'])
    if not screen or not screen.is_active:
        session.clear()
        return redirect(url_for('player.login'))
    
    return render_template('player/display.html', screen=screen)


@player_bp.route('/logout')
def logout():
    if 'screen_id' in session:
        screen = Screen.query.get(session['screen_id'])
        if screen:
            screen.status = 'offline'
            db.session.commit()
    
    session.clear()
    flash('Écran déconnecté.', 'info')
    return redirect(url_for('player.login'))


@player_bp.route('/api/playlist')
def get_playlist():
    if 'screen_id' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    
    screen = Screen.query.get(session['screen_id'])
    if not screen:
        return jsonify({'error': 'Écran non trouvé'}), 404
    
    playlist = []
    
    current_hour = datetime.now().hour
    current_period = None
    for period in screen.time_periods:
        if period.start_hour <= period.end_hour:
            if period.start_hour <= current_hour < period.end_hour:
                current_period = period
                break
        else:
            if current_hour >= period.start_hour or current_hour < period.end_hour:
                current_period = period
                break
    
    paid_contents = Content.query.join(Booking).filter(
        Content.screen_id == screen.id,
        Content.status == 'approved',
        Booking.status == 'active',
        Booking.plays_completed < Booking.num_plays
    ).all()
    
    for content in paid_contents:
        if current_period and content.booking.time_period_id:
            if content.booking.time_period_id != current_period.id:
                continue
        
        playlist.append({
            'id': content.id,
            'type': content.content_type,
            'url': f'/{content.file_path}',
            'duration': content.duration_seconds or 10,
            'priority': 100,
            'category': 'paid',
            'booking_id': content.booking.id
        })
    
    internal_contents = InternalContent.query.filter_by(
        screen_id=screen.id,
        is_active=True
    ).all()
    
    for internal in internal_contents:
        today = datetime.now().date()
        if internal.start_date and internal.start_date > today:
            continue
        if internal.end_date and internal.end_date < today:
            continue
        
        playlist.append({
            'id': internal.id,
            'type': internal.content_type,
            'url': f'/{internal.file_path}',
            'duration': internal.duration_seconds or 10,
            'priority': internal.priority,
            'category': 'internal'
        })
    
    fillers = Filler.query.filter_by(
        screen_id=screen.id,
        is_active=True
    ).all()
    
    for filler in fillers:
        playlist.append({
            'id': filler.id,
            'type': filler.content_type,
            'url': f'/{filler.file_path}',
            'duration': filler.duration_seconds or 10,
            'priority': 20,
            'category': 'filler'
        })
    
    playlist.sort(key=lambda x: x['priority'], reverse=True)
    
    active_overlays = []
    for overlay in screen.overlays:
        if overlay.is_currently_active():
            active_overlays.append(overlay.to_dict())
    
    return jsonify({
        'screen': {
            'id': screen.id,
            'name': screen.name,
            'resolution': f'{screen.resolution_width}x{screen.resolution_height}',
            'orientation': screen.orientation
        },
        'playlist': playlist,
        'overlays': active_overlays,
        'timestamp': datetime.utcnow().isoformat()
    })


@player_bp.route('/api/heartbeat', methods=['POST'])
def heartbeat():
    if 'screen_id' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    
    screen = Screen.query.get(session['screen_id'])
    if not screen:
        return jsonify({'error': 'Écran non trouvé'}), 404
    
    data = request.get_json() or {}
    status = data.get('status', 'online')
    
    screen.last_heartbeat = datetime.utcnow()
    screen.status = status
    
    log = HeartbeatLog(
        screen_id=screen.id,
        status=status
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'timestamp': datetime.utcnow().isoformat()
    })


@player_bp.route('/api/log-play', methods=['POST'])
def log_play():
    if 'screen_id' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    
    screen = Screen.query.get(session['screen_id'])
    if not screen:
        return jsonify({'error': 'Écran non trouvé'}), 404
    
    data = request.get_json()
    content_id = data.get('content_id')
    content_type = data.get('content_type')
    category = data.get('category')
    duration = data.get('duration')
    booking_id = data.get('booking_id')
    
    stat = StatLog(
        screen_id=screen.id,
        content_type=content_type,
        content_id=content_id,
        content_category=category,
        duration_seconds=duration
    )
    db.session.add(stat)
    
    if category == 'paid' and booking_id:
        booking = Booking.query.get(booking_id)
        if booking:
            booking.plays_completed += 1
            if booking.plays_completed >= booking.num_plays:
                booking.status = 'completed'
    
    db.session.commit()
    
    return jsonify({'success': True})
