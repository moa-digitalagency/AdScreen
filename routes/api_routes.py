"""
 * Nom de l'application : Shabaka AdScreen
 * Description : API routes for dashboard and screen management
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from models import Screen, Content, Booking, StatLog
from datetime import datetime, timedelta
from sqlalchemy import func

api_bp = Blueprint('api', __name__)


@api_bp.route('/cities/<country_code>')
def get_cities_by_country(country_code):
    from utils.currencies import get_cities_for_country
    cities = get_cities_for_country(country_code)
    return jsonify({
        'country': country_code,
        'cities': cities
    })


@api_bp.route('/screens/status')
@login_required
def screens_status():
    if current_user.is_superadmin():
        screens = Screen.query.all()
    else:
        screens = Screen.query.filter_by(organization_id=current_user.organization_id).all()
    
    now = datetime.utcnow()
    threshold = timedelta(minutes=2)
    
    result = []
    for screen in screens:
        is_online = screen.last_heartbeat and (now - screen.last_heartbeat) < threshold
        
        result.append({
            'id': screen.id,
            'name': screen.name,
            'status': screen.status if is_online else 'offline',
            'last_heartbeat': screen.last_heartbeat.isoformat() if screen.last_heartbeat else None,
            'is_active': screen.is_active
        })
    
    return jsonify(result)


@api_bp.route('/screen/<int:screen_id>/stats')
@login_required
def screen_stats(screen_id):
    if current_user.is_superadmin():
        screen = Screen.query.get_or_404(screen_id)
    else:
        screen = Screen.query.filter_by(
            id=screen_id,
            organization_id=current_user.organization_id
        ).first_or_404()
    
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    
    daily_plays = db.session.query(
        func.date(StatLog.played_at).label('date'),
        func.count(StatLog.id).label('count')
    ).filter(
        StatLog.screen_id == screen_id,
        StatLog.played_at >= week_ago
    ).group_by(func.date(StatLog.played_at)).all()
    
    category_stats = db.session.query(
        StatLog.content_category,
        func.count(StatLog.id).label('count')
    ).filter(
        StatLog.screen_id == screen_id,
        StatLog.played_at >= week_ago
    ).group_by(StatLog.content_category).all()
    
    return jsonify({
        'daily_plays': [{'date': str(d.date), 'count': d.count} for d in daily_plays],
        'category_stats': [{'category': c.content_category, 'count': c.count} for c in category_stats]
    })


@api_bp.route('/dashboard/summary')
@login_required
def dashboard_summary():
    if current_user.is_superadmin():
        total_screens = Screen.query.count()
        online_screens = Screen.query.filter(
            Screen.status.in_(['online', 'playing'])
        ).count()
        pending_contents = Content.query.filter_by(status='pending').count()
        total_revenue = db.session.query(func.sum(Booking.total_price)).filter(
            Booking.payment_status == 'paid'
        ).scalar() or 0
    else:
        org_id = current_user.organization_id
        total_screens = Screen.query.filter_by(organization_id=org_id).count()
        online_screens = Screen.query.filter(
            Screen.organization_id == org_id,
            Screen.status.in_(['online', 'playing'])
        ).count()
        pending_contents = Content.query.join(Screen).filter(
            Screen.organization_id == org_id,
            Content.status == 'pending'
        ).count()
        total_revenue = db.session.query(func.sum(Booking.total_price)).join(Screen).filter(
            Screen.organization_id == org_id,
            Booking.payment_status == 'paid'
        ).scalar() or 0
    
    return jsonify({
        'total_screens': total_screens,
        'online_screens': online_screens,
        'pending_contents': pending_contents,
        'total_revenue': float(total_revenue)
    })
