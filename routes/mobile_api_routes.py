"""
 * Nom de l'application : Shabaka AdScreen
 * Description : Mobile API routes for players and management
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""
from flask import Blueprint, jsonify, request, g
from app import db
from models import Screen, User, Content, Booking, StatLog, HeartbeatLog
from models.ad_content import AdContent
from datetime import datetime, timedelta
from sqlalchemy import func
import logging

from services.jwt_service import (
    generate_tokens, 
    refresh_access_token, 
    jwt_required, 
    screen_jwt_required, 
    user_jwt_required,
    superadmin_required
)
from services.rate_limiter import limiter, get_rate_limit
from services.input_validator import (
    validate_json_request,
    handle_validation_errors,
    validate_email_address,
    validate_screen_code,
    sanitize_string,
    validate_positive_integer,
    validate_date_string,
    validate_content_type,
    ValidationError
)

logger = logging.getLogger(__name__)

mobile_api_bp = Blueprint('mobile_api', __name__)


@mobile_api_bp.route('/auth/login', methods=['POST'])
@limiter.limit(get_rate_limit("auth", "login"))
@validate_json_request("email", "password")
@handle_validation_errors
def api_login():
    data = request.get_json()
    
    email = validate_email_address(data.get("email"))
    password = data.get("password")
    
    if not password:
        return jsonify({
            "error": "Password is required",
            "code": "MISSING_PASSWORD"
        }), 400
    
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password):
        logger.warning(f"Failed login attempt for: {email}")
        return jsonify({
            "error": "Invalid email or password",
            "code": "INVALID_CREDENTIALS"
        }), 401
    
    if not user.is_active:
        return jsonify({
            "error": "Account is disabled",
            "code": "ACCOUNT_DISABLED"
        }), 403
    
    tokens = generate_tokens(user_id=user.id, role=user.role)
    
    logger.info(f"User logged in via API: {email}")
    
    return jsonify({
        "success": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "organization_id": user.organization_id
        },
        **tokens
    })


@mobile_api_bp.route('/auth/screen-login', methods=['POST'])
@limiter.limit(get_rate_limit("auth", "login"))
@validate_json_request("screen_code", "password")
@handle_validation_errors
def api_screen_login():
    data = request.get_json()
    
    screen_code = validate_screen_code(data.get("screen_code"))
    password = data.get("password")
    
    if not password:
        return jsonify({
            "error": "Password is required",
            "code": "MISSING_PASSWORD"
        }), 400
    
    screen = Screen.query.filter_by(unique_code=screen_code).first()
    
    if not screen or not screen.check_password(password):
        logger.warning(f"Failed screen login attempt for: {screen_code}")
        return jsonify({
            "error": "Invalid screen code or password",
            "code": "INVALID_CREDENTIALS"
        }), 401
    
    if not screen.is_active:
        return jsonify({
            "error": "Screen is disabled",
            "code": "SCREEN_DISABLED"
        }), 403
    
    tokens = generate_tokens(screen_id=screen.id)
    
    logger.info(f"Screen logged in via API: {screen_code}")
    
    return jsonify({
        "success": True,
        "screen": {
            "id": screen.id,
            "name": screen.name,
            "unique_code": screen.unique_code,
            "resolution": f"{screen.resolution_width}x{screen.resolution_height}",
            "orientation": screen.orientation
        },
        **tokens
    })


@mobile_api_bp.route('/auth/refresh', methods=['POST'])
@limiter.limit(get_rate_limit("auth", "refresh"))
@validate_json_request("refresh_token")
def api_refresh_token():
    data = request.get_json()
    refresh_token = data.get("refresh_token")
    
    try:
        new_tokens = refresh_access_token(refresh_token)
        return jsonify({
            "success": True,
            **new_tokens
        })
    except ValueError as e:
        return jsonify({
            "error": str(e),
            "code": "REFRESH_FAILED"
        }), 401


@mobile_api_bp.route('/screen/mode', methods=['GET'])
@limiter.limit(get_rate_limit("player", "playlist"))
@screen_jwt_required
def api_screen_mode():
    screen = Screen.query.get(g.screen_id)
    
    if not screen:
        return jsonify({
            "error": "Screen not found",
            "code": "SCREEN_NOT_FOUND"
        }), 404
    
    return jsonify({
        "mode": screen.current_mode or "playlist",
        "iptv_enabled": screen.iptv_enabled,
        "iptv_channel_url": screen.get_iptv_url() if screen.current_mode == "iptv" else None,
        "iptv_channel_name": screen.current_iptv_channel_name if screen.current_mode == "iptv" else None,
        "timestamp": datetime.utcnow().isoformat()
    })


@mobile_api_bp.route('/screen/playlist', methods=['GET'])
@limiter.limit(get_rate_limit("player", "playlist"))
@screen_jwt_required
def api_screen_playlist():
    db.session.expire_all()
    
    screen = Screen.query.get(g.screen_id)
    
    if not screen:
        return jsonify({
            "error": "Screen not found",
            "code": "SCREEN_NOT_FOUND"
        }), 404
    
    if screen.current_mode == "iptv" and screen.iptv_enabled and screen.current_iptv_channel:
        from services.overlay_service import sync_broadcast_overlays, get_active_overlays_for_screen
        
        sync_broadcast_overlays(screen)
        active_overlay_objects = get_active_overlays_for_screen(screen.id)
        iptv_overlays = [o.to_dict() for o in active_overlay_objects]
        iptv_overlays.sort(key=lambda x: x.get("priority", 50), reverse=True)
        
        return jsonify({
            "screen": {
                "id": screen.id,
                "name": screen.name,
                "resolution": f"{screen.resolution_width}x{screen.resolution_height}",
                "orientation": screen.orientation
            },
            "mode": "iptv",
            "iptv": {
                "url": screen.get_iptv_url(),
                "name": screen.current_iptv_channel_name
            },
            "playlist": [],
            "overlays": iptv_overlays,
            "timestamp": datetime.utcnow().isoformat()
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
        Content.status == "approved",
        Content.in_playlist == True,
        Booking.status == "active",
        Booking.plays_completed < Booking.num_plays
    ).all()
    
    for content in paid_contents:
        if current_period and content.booking.time_period_id:
            if content.booking.time_period_id != current_period.id:
                continue
        
        duration = content.booking.slot_duration if content.booking else (content.duration_seconds or 10)
        remaining = content.booking.num_plays - content.booking.plays_completed if content.booking else 0
        
        playlist.append({
            "id": content.id,
            "type": content.content_type,
            "url": f"/{content.file_path}",
            "duration": duration,
            "priority": 100,
            "category": "paid",
            "booking_id": content.booking.id if content.booking else None,
            "remaining_plays": remaining,
            "name": content.original_filename or content.filename
        })
    
    from models import InternalContent, Filler, Broadcast
    
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
            "id": internal.id,
            "type": internal.content_type,
            "url": f"/{internal.file_path}",
            "duration": internal.duration_seconds or 10,
            "priority": internal.priority,
            "category": "internal",
            "name": internal.name
        })
    
    fillers = Filler.query.filter_by(
        screen_id=screen.id,
        is_active=True,
        in_playlist=True
    ).all()
    
    for filler in fillers:
        playlist.append({
            "id": filler.id,
            "type": filler.content_type,
            "url": f"/{filler.file_path}",
            "duration": filler.duration_seconds or 10,
            "priority": 20,
            "category": "filler",
            "name": filler.filename
        })
    
    playlist.sort(key=lambda x: x["priority"], reverse=True)
    
    from services.overlay_service import sync_broadcast_overlays, get_active_overlays_for_screen
    
    sync_broadcast_overlays(screen)
    active_overlay_objects = get_active_overlays_for_screen(screen.id)
    active_overlays = [o.to_dict() for o in active_overlay_objects]
    active_overlays.sort(key=lambda x: x.get("priority", 50), reverse=True)
    
    active_broadcasts = Broadcast.query.filter_by(is_active=True).all()
    for broadcast in active_broadcasts:
        if broadcast.applies_to_screen(screen):
            if broadcast.broadcast_type == "content":
                playlist.append(broadcast.to_content_dict())
    
    active_ad_contents = AdContent.query.filter(
        AdContent.status.in_([AdContent.STATUS_ACTIVE, AdContent.STATUS_SCHEDULED])
    ).all()
    
    for ad in active_ad_contents:
        ad.update_status()
        if ad.is_currently_active() and ad.applies_to_screen(screen):
            ad_dict = ad.to_content_dict()
            ad_dict["priority"] = 50
            playlist.append(ad_dict)
    
    db.session.commit()
    
    playlist.sort(key=lambda x: x["priority"], reverse=True)
    
    return jsonify({
        "screen": {
            "id": screen.id,
            "name": screen.name,
            "resolution": f"{screen.resolution_width}x{screen.resolution_height}",
            "orientation": screen.orientation
        },
        "mode": "playlist",
        "playlist": playlist,
        "overlays": active_overlays,
        "timestamp": datetime.utcnow().isoformat()
    })


@mobile_api_bp.route('/screen/heartbeat', methods=['POST'])
@limiter.limit(get_rate_limit("player", "heartbeat"))
@screen_jwt_required
def api_screen_heartbeat():
    screen = Screen.query.get(g.screen_id)
    
    if not screen:
        return jsonify({
            "error": "Screen not found",
            "code": "SCREEN_NOT_FOUND"
        }), 404
    
    data = request.get_json() or {}
    status = data.get("status", "online")
    
    if status not in ["online", "playing", "offline"]:
        status = "online"
    
    screen.last_heartbeat = datetime.utcnow()
    screen.status = status
    
    log = HeartbeatLog(
        screen_id=screen.id,
        status=status
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "timestamp": datetime.utcnow().isoformat()
    })


@mobile_api_bp.route('/screen/log-play', methods=['POST'])
@limiter.limit(get_rate_limit("player", "log_play"))
@screen_jwt_required
@validate_json_request("content_id", "content_type", "category")
@handle_validation_errors
def api_screen_log_play():
    screen = Screen.query.get(g.screen_id)
    
    if not screen:
        return jsonify({
            "error": "Screen not found",
            "code": "SCREEN_NOT_FOUND"
        }), 404
    
    data = request.get_json()
    content_id = data.get("content_id")
    content_type = validate_content_type(data.get("content_type"))
    category = sanitize_string(data.get("category"), max_length=50)
    duration = validate_positive_integer(data.get("duration", 10), "duration", min_val=1, max_val=300)
    booking_id = data.get("booking_id")
    
    stat = StatLog(
        screen_id=screen.id,
        content_type=content_type,
        content_id=content_id,
        content_category=category,
        duration_seconds=duration
    )
    db.session.add(stat)
    
    exhausted = False
    if category == "paid" and booking_id:
        booking = Booking.query.get(booking_id)
        if booking:
            booking.plays_completed += 1
            if booking.plays_completed >= booking.num_plays:
                booking.status = "completed"
                exhausted = True
    
    if category == "ad_content" and content_id:
        from models.ad_content import AdContentStat
        ad_id_str = str(content_id)
        if ad_id_str.startswith("ad_"):
            ad_id = int(ad_id_str.replace("ad_", ""))
            AdContentStat.record_impression(
                ad_content_id=ad_id,
                screen_id=screen.id,
                organization_id=screen.organization_id,
                duration=duration
            )
    
    db.session.commit()
    
    return jsonify({
        "success": True,
        "exhausted": exhausted
    })


@mobile_api_bp.route('/dashboard/screens', methods=['GET'])
@limiter.limit(get_rate_limit("api", "read"))
@user_jwt_required
def api_dashboard_screens():
    user = User.query.get(g.user_id)
    
    if not user:
        return jsonify({
            "error": "User not found",
            "code": "USER_NOT_FOUND"
        }), 404
    
    if g.role == "superadmin":
        screens = Screen.query.all()
    else:
        screens = Screen.query.filter_by(organization_id=user.organization_id).all()
    
    now = datetime.utcnow()
    threshold = timedelta(minutes=2)
    
    result = []
    for screen in screens:
        is_online = screen.last_heartbeat and (now - screen.last_heartbeat) < threshold
        
        result.append({
            "id": screen.id,
            "name": screen.name,
            "unique_code": screen.unique_code,
            "status": screen.status if is_online else "offline",
            "last_heartbeat": screen.last_heartbeat.isoformat() if screen.last_heartbeat else None,
            "is_active": screen.is_active,
            "current_mode": screen.current_mode,
            "resolution": f"{screen.resolution_width}x{screen.resolution_height}",
            "orientation": screen.orientation
        })
    
    return jsonify({
        "screens": result,
        "total": len(result)
    })


@mobile_api_bp.route('/dashboard/screen/<int:screen_id>/stats', methods=['GET'])
@limiter.limit(get_rate_limit("api", "read"))
@user_jwt_required
@handle_validation_errors
def api_screen_stats(screen_id):
    user = User.query.get(g.user_id)
    
    if g.role == "superadmin":
        screen = Screen.query.get(screen_id)
    else:
        screen = Screen.query.filter_by(
            id=screen_id,
            organization_id=user.organization_id
        ).first()
    
    if not screen:
        return jsonify({
            "error": "Screen not found or access denied",
            "code": "SCREEN_NOT_FOUND"
        }), 404
    
    days = validate_positive_integer(request.args.get("days", 7), "days", min_val=1, max_val=90)
    
    today = datetime.utcnow().date()
    start_date = today - timedelta(days=days)
    
    daily_plays = db.session.query(
        func.date(StatLog.played_at).label("date"),
        func.count(StatLog.id).label("count")
    ).filter(
        StatLog.screen_id == screen_id,
        StatLog.played_at >= start_date
    ).group_by(func.date(StatLog.played_at)).all()
    
    category_stats = db.session.query(
        StatLog.content_category,
        func.count(StatLog.id).label("count")
    ).filter(
        StatLog.screen_id == screen_id,
        StatLog.played_at >= start_date
    ).group_by(StatLog.content_category).all()
    
    return jsonify({
        "screen_id": screen_id,
        "period_days": days,
        "daily_plays": [{"date": str(d.date), "count": d.count} for d in daily_plays],
        "category_stats": [{"category": c.content_category, "count": c.count} for c in category_stats],
        "total_plays": sum(d.count for d in daily_plays)
    })


@mobile_api_bp.route('/dashboard/summary', methods=['GET'])
@limiter.limit(get_rate_limit("api", "read"))
@user_jwt_required
def api_dashboard_summary():
    user = User.query.get(g.user_id)
    
    if g.role == "superadmin":
        total_screens = Screen.query.count()
        online_screens = Screen.query.filter(
            Screen.status.in_(["online", "playing"])
        ).count()
        pending_contents = Content.query.filter_by(status="pending").count()
        total_revenue = db.session.query(func.sum(Booking.total_price)).filter(
            Booking.payment_status == "paid"
        ).scalar() or 0
    else:
        org_id = user.organization_id
        total_screens = Screen.query.filter_by(organization_id=org_id).count()
        online_screens = Screen.query.filter(
            Screen.organization_id == org_id,
            Screen.status.in_(["online", "playing"])
        ).count()
        pending_contents = Content.query.join(Screen).filter(
            Screen.organization_id == org_id,
            Content.status == "pending"
        ).count()
        total_revenue = db.session.query(func.sum(Booking.total_price)).join(Screen).filter(
            Screen.organization_id == org_id,
            Booking.payment_status == "paid"
        ).scalar() or 0
    
    return jsonify({
        "total_screens": total_screens,
        "online_screens": online_screens,
        "pending_contents": pending_contents,
        "total_revenue": float(total_revenue)
    })


@mobile_api_bp.route('/health', methods=['GET'])
def api_health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0"
    })
