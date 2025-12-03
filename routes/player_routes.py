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
    Convert MPEG-TS stream to HLS on-the-fly using FFmpeg.
    This route provides better browser compatibility for MPEG-TS streams.
    """
    from flask import stream_with_context
    import subprocess
    import os
    import tempfile
    import shutil
    import time
    import threading
    
    screen = Screen.query.filter_by(unique_code=screen_code).first()
    
    if not screen:
        return jsonify({'error': 'Écran non trouvé'}), 404
    
    if not screen.current_iptv_channel:
        return jsonify({'error': 'Aucune chaîne IPTV configurée'}), 400
    
    if screen.current_mode != 'iptv':
        return jsonify({'error': 'Écran pas en mode IPTV'}), 400
    
    source_url = screen.current_iptv_channel
    logger.info(f'Starting MPEG-TS to HLS conversion for screen {screen_code}')
    logger.info(f'Source URL: {source_url[:80]}...' if len(source_url) > 80 else f'Source URL: {source_url}')
    
    try:
        temp_dir = tempfile.mkdtemp(prefix='hls_')
        playlist_path = os.path.join(temp_dir, 'stream.m3u8')
        
        ffmpeg_cmd = [
            'ffmpeg',
            '-y',
            '-hide_banner',
            '-loglevel', 'warning',
            '-fflags', '+genpts+discardcorrupt',
            '-user_agent', 'VLC/3.0.18 LibVLC/3.0.18',
            '-i', source_url,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-f', 'hls',
            '-hls_time', '4',
            '-hls_list_size', '3',
            '-hls_flags', 'delete_segments+append_list+independent_segments',
            '-hls_segment_filename', os.path.join(temp_dir, 'segment_%03d.ts'),
            playlist_path
        ]
        
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        for _ in range(50):
            if os.path.exists(playlist_path) and os.path.getsize(playlist_path) > 0:
                break
            time.sleep(0.1)
        else:
            process.terminate()
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.error('FFmpeg timeout: HLS playlist not created')
            return jsonify({'error': 'Timeout lors de la conversion du flux'}), 500
        
        def cleanup_later():
            time.sleep(30)
            process.terminate()
            try:
                process.wait(timeout=5)
            except Exception:
                process.kill()
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.info(f'Cleaned up temp dir {temp_dir}')
        
        cleanup_thread = threading.Thread(target=cleanup_later, daemon=True)
        cleanup_thread.start()
        
        with open(playlist_path, 'r') as f:
            playlist_content = f.read()
        
        resp = Response(playlist_content, content_type='application/vnd.apple.mpegurl')
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return resp
        
    except Exception as e:
        logger.error(f'Stream conversion failed: {str(e)}')
        return jsonify({'error': f'Erreur de conversion: {str(e)}'}), 500


@player_bp.route('/tv-stream/<screen_code>/segment/<segment_name>')
def tv_stream_segment(screen_code, segment_name):
    """Serve HLS segments for the tv-stream."""
    import os
    import tempfile
    
    temp_base = tempfile.gettempdir()
    
    for dir_name in os.listdir(temp_base):
        if dir_name.startswith('hls_'):
            segment_path = os.path.join(temp_base, dir_name, segment_name)
            if os.path.exists(segment_path):
                with open(segment_path, 'rb') as f:
                    content = f.read()
                resp = Response(content, content_type='video/mp2t')
                resp.headers['Access-Control-Allow-Origin'] = '*'
                resp.headers['Cache-Control'] = 'no-cache'
                return resp
    
    return jsonify({'error': 'Segment not found'}), 404
