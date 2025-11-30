from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from app import db
from models import User, Organization, Screen, Booking, StatLog, Content, SiteSetting
from datetime import datetime, timedelta
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)


def superadmin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_superadmin():
            flash('Accès réservé aux super administrateurs.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/dashboard')
@login_required
@superadmin_required
def dashboard():
    total_orgs = Organization.query.count()
    active_orgs = Organization.query.filter_by(is_active=True).count()
    total_screens = Screen.query.count()
    online_screens = Screen.query.filter(Screen.status.in_(['online', 'playing'])).count()
    
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    total_revenue = db.session.query(func.sum(Booking.total_price)).filter(
        Booking.payment_status == 'paid'
    ).scalar() or 0
    
    weekly_revenue = db.session.query(func.sum(Booking.total_price)).filter(
        Booking.payment_status == 'paid',
        Booking.created_at >= week_ago
    ).scalar() or 0
    
    monthly_revenue = db.session.query(func.sum(Booking.total_price)).filter(
        Booking.payment_status == 'paid',
        Booking.created_at >= month_ago
    ).scalar() or 0
    
    orgs_with_revenue = db.session.query(
        Organization,
        func.sum(Booking.total_price).label('gross_revenue')
    ).join(Screen, Screen.organization_id == Organization.id).join(
        Booking, Booking.screen_id == Screen.id
    ).filter(
        Booking.payment_status == 'paid'
    ).group_by(Organization.id).all()
    
    total_platform_commission = sum(
        org.calculate_platform_commission(gross_revenue or 0) 
        for org, gross_revenue in orgs_with_revenue
    )
    
    weekly_commission = 0
    orgs_weekly = db.session.query(
        Organization,
        func.sum(Booking.total_price).label('gross_revenue')
    ).join(Screen, Screen.organization_id == Organization.id).join(
        Booking, Booking.screen_id == Screen.id
    ).filter(
        Booking.payment_status == 'paid',
        Booking.created_at >= week_ago
    ).group_by(Organization.id).all()
    
    weekly_commission = sum(
        org.calculate_platform_commission(gross_revenue or 0) 
        for org, gross_revenue in orgs_weekly
    )
    
    recent_orgs = Organization.query.order_by(Organization.created_at.desc()).limit(5).all()
    recent_bookings = Booking.query.filter_by(payment_status='paid').order_by(
        Booking.created_at.desc()
    ).limit(10).all()
    
    top_orgs = db.session.query(
        Organization,
        func.sum(Booking.total_price).label('revenue')
    ).join(Screen, Screen.organization_id == Organization.id).join(
        Booking, Booking.screen_id == Screen.id
    ).filter(
        Booking.payment_status == 'paid'
    ).group_by(Organization.id).order_by(func.sum(Booking.total_price).desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
        total_orgs=total_orgs,
        active_orgs=active_orgs,
        total_screens=total_screens,
        online_screens=online_screens,
        total_revenue=total_revenue,
        weekly_revenue=weekly_revenue,
        monthly_revenue=monthly_revenue,
        total_platform_commission=total_platform_commission,
        weekly_commission=weekly_commission,
        recent_orgs=recent_orgs,
        recent_bookings=recent_bookings,
        top_orgs=top_orgs
    )


@admin_bp.route('/organizations')
@login_required
@superadmin_required
def organizations():
    orgs = Organization.query.order_by(Organization.created_at.desc()).all()
    return render_template('admin/organizations.html', organizations=orgs)


@admin_bp.route('/organization/<int:org_id>')
@login_required
@superadmin_required
def organization_detail(org_id):
    org = Organization.query.get_or_404(org_id)
    screens = Screen.query.filter_by(organization_id=org_id).all()
    
    total_revenue = db.session.query(func.sum(Booking.total_price)).join(Screen).filter(
        Screen.organization_id == org_id,
        Booking.payment_status == 'paid'
    ).scalar() or 0
    
    platform_commission = org.calculate_platform_commission(total_revenue)
    net_revenue = org.calculate_net_revenue(total_revenue)
    
    return render_template('admin/organization_detail.html',
        org=org,
        screens=screens,
        total_revenue=total_revenue,
        platform_commission=platform_commission,
        net_revenue=net_revenue
    )


@admin_bp.route('/organization/<int:org_id>/toggle', methods=['POST'])
@login_required
@superadmin_required
def toggle_organization(org_id):
    org = Organization.query.get_or_404(org_id)
    org.is_active = not org.is_active
    db.session.commit()
    
    status = "activé" if org.is_active else "désactivé"
    flash(f'Établissement {status} avec succès.', 'success')
    return redirect(url_for('admin.organizations'))


@admin_bp.route('/organization/<int:org_id>/commission', methods=['POST'])
@login_required
@superadmin_required
def update_commission(org_id):
    org = Organization.query.get_or_404(org_id)
    commission = float(request.form.get('commission', 10))
    
    min_rate = SiteSetting.get('min_commission_rate', 5.0)
    max_rate = SiteSetting.get('max_commission_rate', 30.0)
    
    if min_rate <= commission <= max_rate:
        org.commission_rate = commission
        org.commission_set_by = current_user.id
        org.commission_updated_at = datetime.utcnow()
        db.session.commit()
        flash(f'Commission mise à jour à {commission}%.', 'success')
    else:
        flash(f'La commission doit être entre {min_rate}% et {max_rate}%.', 'error')
    
    return redirect(url_for('admin.organization_detail', org_id=org_id))


@admin_bp.route('/screens')
@login_required
@superadmin_required
def screens():
    all_screens = Screen.query.join(Organization).order_by(Screen.created_at.desc()).all()
    return render_template('admin/screens.html', screens=all_screens)


@admin_bp.route('/stats')
@login_required
@superadmin_required
def stats():
    today = datetime.utcnow().date()
    month_ago = today - timedelta(days=30)
    
    daily_stats = db.session.query(
        func.date(Booking.created_at).label('date'),
        func.sum(Booking.total_price).label('revenue'),
        func.count(Booking.id).label('count')
    ).filter(
        Booking.payment_status == 'paid',
        Booking.created_at >= month_ago
    ).group_by(func.date(Booking.created_at)).all()
    
    org_stats = db.session.query(
        Organization.name,
        Organization.commission_rate,
        func.sum(Booking.total_price).label('revenue')
    ).join(Screen, Screen.organization_id == Organization.id).join(
        Booking, Booking.screen_id == Screen.id
    ).filter(
        Booking.payment_status == 'paid'
    ).group_by(Organization.id).order_by(func.sum(Booking.total_price).desc()).limit(10).all()
    
    return render_template('admin/stats.html',
        daily_stats=daily_stats,
        org_stats=org_stats
    )


@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@superadmin_required
def settings():
    if request.method == 'POST':
        settings_data = {
            'site_title': ('string', 'seo'),
            'site_description': ('string', 'seo'),
            'meta_keywords': ('string', 'seo'),
            'og_image': ('string', 'seo'),
            'google_analytics_id': ('string', 'seo'),
            'platform_name': ('string', 'platform'),
            'support_email': ('string', 'platform'),
            'default_commission_rate': ('float', 'platform'),
            'min_commission_rate': ('float', 'platform'),
            'max_commission_rate': ('float', 'platform'),
            'maintenance_mode': ('boolean', 'platform'),
        }
        
        for key, (value_type, category) in settings_data.items():
            value = request.form.get(key, '')
            if value_type == 'boolean':
                value = 'true' if key in request.form else 'false'
            SiteSetting.set(key, value, value_type, category)
        
        flash('Paramètres enregistrés avec succès.', 'success')
        return redirect(url_for('admin.settings'))
    
    seo_settings = SiteSetting.get_seo_settings()
    platform_settings = SiteSetting.get_platform_settings()
    
    return render_template('admin/settings.html',
        seo_settings=seo_settings,
        platform_settings=platform_settings
    )
