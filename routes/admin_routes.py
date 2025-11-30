from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from app import db
from models import User, Organization, Screen, Booking, StatLog, Content
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
    online_screens = Screen.query.filter_by(status='playing').count()
    
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    
    total_revenue = db.session.query(func.sum(Booking.total_price)).filter(
        Booking.payment_status == 'paid'
    ).scalar() or 0
    
    weekly_revenue = db.session.query(func.sum(Booking.total_price)).filter(
        Booking.payment_status == 'paid',
        Booking.created_at >= week_ago
    ).scalar() or 0
    
    recent_orgs = Organization.query.order_by(Organization.created_at.desc()).limit(5).all()
    recent_bookings = Booking.query.filter_by(payment_status='paid').order_by(
        Booking.created_at.desc()
    ).limit(10).all()
    
    return render_template('admin/dashboard.html',
        total_orgs=total_orgs,
        active_orgs=active_orgs,
        total_screens=total_screens,
        online_screens=online_screens,
        total_revenue=total_revenue,
        weekly_revenue=weekly_revenue,
        recent_orgs=recent_orgs,
        recent_bookings=recent_bookings
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
    
    return render_template('admin/organization_detail.html',
        org=org,
        screens=screens,
        total_revenue=total_revenue
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
    
    if 5 <= commission <= 15:
        org.commission_rate = commission
        db.session.commit()
        flash('Commission mise à jour.', 'success')
    else:
        flash('La commission doit être entre 5% et 15%.', 'error')
    
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
