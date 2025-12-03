# pyright: reportArgumentType=false
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify, Response
from app import db
from models import Screen, Content, Booking, Filler, InternalContent, StatLog, HeartbeatLog, ScreenOverlay, Broadcast
from datetime import datetime
import urllib.parse
import urllib3
import logging
import re

urllib3.disable_warnings()

logger = logging.getLogger(__name__)

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


@player_bp.route('/api/screen-mode')
def get_screen_mode():
    if 'screen_id' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    
    db.session.expire_all()
    
    screen = Screen.query.get(session['screen_id'])
    if not screen:
        return jsonify({'error': 'Écran non trouvé'}), 404
    
    return jsonify({
        'mode': screen.current_mode or 'playlist',
        'iptv_enabled': screen.iptv_enabled,
        'iptv_channel_url': screen.get_iptv_url() if screen.current_mode == 'iptv' else None,
        'iptv_channel_name': screen.current_iptv_channel_name if screen.current_mode == 'iptv' else None,
        'timestamp': datetime.utcnow().isoformat()
    })


@player_bp.route('/api/playlist')
def get_playlist():
    if 'screen_id' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    
    db.session.expire_all()
    
    screen = Screen.query.get(session['screen_id'])
    if not screen:
        return jsonify({'error': 'Écran non trouvé'}), 404
    
    if screen.current_mode == 'iptv' and screen.iptv_enabled and screen.current_iptv_channel:
        return jsonify({
            'screen': {
                'id': screen.id,
                'name': screen.name,
                'resolution': f'{screen.resolution_width}x{screen.resolution_height}',
                'orientation': screen.orientation
            },
            'mode': 'iptv',
            'iptv': {
                'url': screen.get_iptv_url(),
                'name': screen.current_iptv_channel_name
            },
            'playlist': [],
            'overlays': [],
            'timestamp': datetime.utcnow().isoformat()
        })
    
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
        Content.in_playlist == True,
        Booking.status == 'active',
        Booking.plays_completed < Booking.num_plays
    ).all()
    
    for content in paid_contents:
        if current_period and content.booking.time_period_id:
            if content.booking.time_period_id != current_period.id:
                continue
        
        duration = content.booking.slot_duration if content.booking else (content.duration_seconds or 10)
        remaining = content.booking.num_plays - content.booking.plays_completed if content.booking else 0
        
        playlist.append({
            'id': content.id,
            'type': content.content_type,
            'url': f'/{content.file_path}',
            'duration': duration,
            'priority': 100,
            'category': 'paid',
            'booking_id': content.booking.id if content.booking else None,
            'remaining_plays': remaining,
            'name': content.original_filename or content.filename
        })
    
    internal_contents = InternalContent.query.filter_by(
        screen_id=screen.id,
        is_active=True,
        in_playlist=True
    ).all()
    
    today = datetime.now().date()
    for internal in internal_contents:
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
            'category': 'internal',
            'name': internal.name
        })
    
    fillers = Filler.query.filter_by(
        screen_id=screen.id,
        is_active=True,
        in_playlist=True
    ).all()
    
    for filler in fillers:
        playlist.append({
            'id': filler.id,
            'type': filler.content_type,
            'url': f'/{filler.file_path}',
            'duration': filler.duration_seconds or 10,
            'priority': 20,
            'category': 'filler',
            'name': filler.filename
        })
    
    playlist.sort(key=lambda x: x['priority'], reverse=True)
    
    active_overlays = []
    for overlay in screen.overlays:
        if overlay.is_currently_active():
            active_overlays.append(overlay.to_dict())
    
    active_broadcasts = Broadcast.query.filter_by(is_active=True).all()
    for broadcast in active_broadcasts:
        if broadcast.applies_to_screen(screen):
            if broadcast.broadcast_type == 'overlay':
                active_overlays.append(broadcast.to_overlay_dict())
            else:
                playlist.append(broadcast.to_content_dict())
    
    playlist.sort(key=lambda x: x['priority'], reverse=True)
    
    return jsonify({
        'screen': {
            'id': screen.id,
            'name': screen.name,
            'resolution': f'{screen.resolution_width}x{screen.resolution_height}',
            'orientation': screen.orientation
        },
        'mode': 'playlist',
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
    
    exhausted = False
    if category == 'paid' and booking_id:
        booking = Booking.query.get(booking_id)
        if booking:
            booking.plays_completed += 1
            if booking.plays_completed >= booking.num_plays:
                booking.status = 'completed'
                exhausted = True
    
    db.session.commit()
    
    return jsonify({'success': True, 'exhausted': exhausted})


@player_bp.route('/api/stream-proxy')
def stream_proxy():
    """
    Proxy for IPTV/HLS streams to bypass CORS restrictions.
    Uses urllib3 for better gevent compatibility with stream_with_context.
    """
    from flask import stream_with_context
    
    if 'screen_id' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL manquante'}), 400
    
    if not url.startswith(('http://', 'https://')):
        return jsonify({'error': 'URL invalide'}), 400
    
    is_manifest = '.m3u' in url.lower() or '.m3u8' in url.lower()
    is_ts_segment = '.ts' in url.lower()
    is_mpegts_stream = 'output=mpegts' in url.lower() or 'type=m3u_plus' in url.lower()
    
    url_path = urllib.parse.urlparse(url).path
    has_no_extension = '.' not in url_path.split('/')[-1] if '/' in url_path else '.' not in url_path
    is_numeric_ending = bool(re.match(r'.*\/\d+$', url_path))
    
    if has_no_extension or is_numeric_ending:
        is_mpegts_stream = True
        logger.info(f"Detected MPEG-TS stream: {url}")
    
    try:
        http = urllib3.PoolManager(
            timeout=urllib3.Timeout(connect=10.0, read=None),
            retries=urllib3.Retry(total=3, redirect=10)
        )
        
        headers = {
            'User-Agent': 'VLC/3.0.18 LibVLC/3.0.18',
            'Accept': '*/*',
            'Connection': 'keep-alive',
        }
        
        if is_manifest:
            response = http.request('GET', url, headers=headers, timeout=30)
            
            content_type = response.headers.get('Content-Type', 'application/vnd.apple.mpegurl')
            
            try:
                text_content = response.data.decode('utf-8')
            except Exception:
                text_content = response.data.decode('latin-1')
            
            base_url = url.rsplit('/', 1)[0] + '/'
            lines = text_content.split('\n')
            modified_lines = []
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    if not line.startswith(('http://', 'https://')):
                        line = base_url + line
                modified_lines.append(line)
            
            content = '\n'.join(modified_lines).encode('utf-8')
            
            resp = Response(content, content_type=content_type)
            resp.headers['Access-Control-Allow-Origin'] = '*'
            resp.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, Range'
            resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            return resp
        else:
            logger.info(f"Starting stream proxy for: {url}")
            
            upstream_response = http.request(
                'GET', url, 
                headers=headers, 
                preload_content=False,
                timeout=urllib3.Timeout(connect=15.0, read=None)
            )
            
            logger.info(f"Upstream response status: {upstream_response.status}")
            
            def generate_stream():
                bytes_sent = 0
                try:
                    while True:
                        chunk = upstream_response.read(32768)
                        if not chunk:
                            logger.info(f"Stream ended after {bytes_sent} bytes")
                            break
                        bytes_sent += len(chunk)
                        yield chunk
                except GeneratorExit:
                    logger.info(f"Client disconnected after {bytes_sent} bytes")
                except Exception as e:
                    logger.error(f"Stream error after {bytes_sent} bytes: {str(e)}")
                finally:
                    try:
                        upstream_response.release_conn()
                    except Exception:
                        pass
            
            content_type = 'video/mp2t' if (is_ts_segment or is_mpegts_stream) else 'application/octet-stream'
            
            resp = Response(
                stream_with_context(generate_stream()), 
                content_type=content_type,
                direct_passthrough=True
            )
            resp.headers['Access-Control-Allow-Origin'] = '*'
            resp.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, Range'
            resp.headers['Access-Control-Expose-Headers'] = 'Content-Length, Content-Range'
            resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            resp.headers['Transfer-Encoding'] = 'chunked'
            return resp
            
    except Exception as e:
        logger.error(f"Error proxying stream: {str(e)}")
        return jsonify({'error': 'Erreur lors du chargement du stream'}), 500


@player_bp.route('/api/stream-proxy', methods=['OPTIONS'])
def stream_proxy_options():
    """Handle CORS preflight requests for the stream proxy."""
    resp = Response('')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return resp


@player_bp.route('/tv-stream/<screen_code>')
def tv_stream(screen_code):
    """
    Convert MPEG-TS stream to HLS and save segments to disk.
    Returns M3U8 manifest with rewritten segment URLs.
    """
    from services.hls_converter import HLSConverter
    import time
    
    db.session.expire_all()
    
    screen = Screen.query.filter_by(unique_code=screen_code).first()
    
    if not screen:
        return jsonify({'error': 'Écran non trouvé'}), 404
    
    if not screen.current_iptv_channel:
        return jsonify({'error': 'Aucune chaîne IPTV configurée'}), 400
    
    if screen.current_mode != 'iptv':
        return jsonify({'error': 'Écran pas en mode IPTV'}), 400
    
    source_url = screen.current_iptv_channel
    channel_name = screen.current_iptv_channel_name or 'Unknown'
    
    current_url = HLSConverter.get_current_url(screen_code)
    if current_url and current_url != source_url:
        logger.info(f'[{screen_code}] CHANNEL CHANGED! Stopping old stream...')
        HLSConverter.stop_existing_process(screen_code)
        time.sleep(0.3)
    
    try:
        if not HLSConverter.is_running(screen_code):
            logger.info(f'[{screen_code}] Starting new HLS conversion for: {channel_name}')
            HLSConverter.start_conversion(source_url, screen_code)
        
        manifest_path = HLSConverter.get_manifest_path(screen_code)
        
        for _ in range(30):
            if manifest_path.exists():
                break
            time.sleep(0.1)
        
        if not manifest_path.exists():
            logger.error(f'[{screen_code}] Manifest still not found')
            return jsonify({'error': 'Manifest not available'}), 503
        
        manifest_content = HLSConverter.get_fresh_manifest(screen_code)
        
        if not manifest_content:
            return jsonify({'error': 'Manifest not available yet'}), 503
        
        manifest_content = HLSConverter.rewrite_manifest(manifest_content, screen_code)
        
        resp = Response(manifest_content, content_type='application/vnd.apple.mpegurl')
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = '0'
        resp.headers['X-Accel-Buffering'] = 'no'
        return resp
        
    except Exception as e:
        logger.error(f'[{screen_code}] Stream conversion failed: {str(e)}')
        return jsonify({'error': f'Erreur de conversion: {str(e)}'}), 500


@player_bp.route('/tv-segment/<screen_code>/<segment_name>')
def tv_segment(screen_code, segment_name):
    """Serve HLS segments (.ts files) from disk."""
    from flask import send_file
    from services.hls_converter import HLSConverter
    
    segment_path = HLSConverter.get_segment_path(screen_code, segment_name)
    
    if not segment_path:
        logger.warning(f'[{screen_code}] Segment not found: {segment_name}')
        return jsonify({'error': 'Segment not found'}), 404
    
    try:
        resp = send_file(
            segment_path,
            mimetype='video/mp2t',
            as_attachment=False,
            max_age=0
        )
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = '0'
        return resp
    except Exception as e:
        logger.error(f'[{screen_code}] Segment error: {e}')
        return jsonify({'error': 'Segment error'}), 500


@player_bp.route('/tv-stop/<screen_code>', methods=['POST'])
def stop_tv_stream(screen_code):
    """Stop the TV stream for a screen (kill FFmpeg process)."""
    from services.hls_converter import HLSConverter
    
    try:
        logger.info(f'[{screen_code}] Received stop request')
        HLSConverter.stop_stream(screen_code)
        return jsonify({'status': 'stopped', 'screen_code': screen_code}), 200
    except Exception as e:
        logger.error(f'[{screen_code}] Stop error: {e}')
        return jsonify({'error': str(e)}), 500


@player_bp.route('/change-channel/<screen_code>', methods=['POST'])
def change_channel(screen_code):
    """Change la chaîne TV - attend que FFmpeg soit prêt"""
    from services.hls_converter import HLSConverter
    import time
    
    try:
        data = request.get_json()
        channel_url = data.get('channel_url')
        channel_name = data.get('channel_name')
        
        if not channel_url:
            return jsonify({'error': 'No channel URL'}), 400
        
        screen = Screen.query.filter_by(unique_code=screen_code).first()
        if not screen:
            return jsonify({'error': 'Screen not found'}), 404
        
        logger.info(f'[{screen_code}] Channel change request: {channel_name}')
        
        logger.info(f'[{screen_code}] Stopping old FFmpeg process...')
        HLSConverter.stop_existing_process(screen_code)
        time.sleep(0.5)
        
        logger.info(f'[{screen_code}] Starting new FFmpeg process...')
        try:
            manifest_path = HLSConverter.convert_mpegts_to_hls_file(
                channel_url,
                screen_code,
                wait_for_manifest=True
            )
            logger.info(f'[{screen_code}] FFmpeg ready with manifest')
        except Exception as e:
            logger.error(f'[{screen_code}] FFmpeg failed: {e}')
            return jsonify({'error': f'FFmpeg failed: {str(e)}'}), 500
        
        screen.current_iptv_channel = channel_url
        screen.current_iptv_channel_name = channel_name
        screen.current_mode = 'iptv'
        db.session.commit()
        logger.info(f'[{screen_code}] Database updated')
        
        return jsonify({
            'status': 'ready',
            'channel': channel_name,
            'message': 'New channel ready'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f'[{screen_code}] Error: {e}')
        return jsonify({'error': str(e)}), 500
