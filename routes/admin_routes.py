import math
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user
from functools import wraps
from app import db
from models import User, Organization, Screen, Booking, StatLog, Content, SiteSetting, RegistrationRequest, Invoice, PaymentProof, Broadcast
from datetime import datetime, timedelta
from sqlalchemy import func
from services.currency_service import (
    convert_to_base_currency, 
    get_conversion_rate, 
    calculate_revenue_in_base_currency,
    get_rates_last_updated,
    refresh_rates
)

admin_bp = Blueprint('admin', __name__)


def parse_float_safe(value, default=0.0):
    """Safely parse a float value, returning default if invalid."""
    if value is None or value == '':
        return default
    try:
        result = float(str(value).replace(',', '.'))
        if math.isnan(result) or math.isinf(result):
            return default
        return result
    except (ValueError, TypeError):
        return default


def superadmin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_superadmin():
            flash('Accès réservé aux super administrateurs.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(permission=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Veuillez vous connecter.', 'error')
                return redirect(url_for('auth.login'))
            
            if not current_user.is_admin():
                flash('Accès réservé aux administrateurs.', 'error')
                return redirect(url_for('auth.login'))
            
            if permission and not current_user.has_permission(permission):
                flash('Vous n\'avez pas accès à cette fonctionnalité.', 'error')
                return redirect(url_for('admin.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@admin_bp.route('/dashboard')
@login_required
@admin_required('dashboard')
def dashboard():
    from utils.currencies import get_currency_by_code
    
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
    
    revenue_by_currency = db.session.query(
        Organization.currency,
        func.sum(Booking.total_price).label('total'),
        func.sum(Booking.total_price * Organization.commission_rate / 100).label('commission')
    ).join(Screen, Screen.organization_id == Organization.id).join(
        Booking, Booking.screen_id == Screen.id
    ).filter(
        Booking.payment_status == 'paid'
    ).group_by(Organization.currency).all()
    
    currency_stats = []
    for currency_code, total, commission in revenue_by_currency:
        currency_info = get_currency_by_code(currency_code or 'EUR')
        currency_stats.append({
            'code': currency_code or 'EUR',
            'name': currency_info.get('name', currency_code),
            'flag': currency_info.get('flag', ''),
            'symbol': currency_info.get('symbol', currency_code),
            'total': total or 0,
            'commission': commission or 0
        })
    
    from utils.currencies import get_country_by_code
    
    orgs_by_country = db.session.query(
        Organization.country,
        func.count(Organization.id).label('org_count')
    ).group_by(Organization.country).all()
    
    screens_by_country = db.session.query(
        Organization.country,
        func.count(Screen.id).label('screen_count')
    ).join(Screen, Screen.organization_id == Organization.id).group_by(Organization.country).all()
    
    orgs_count_map = {c: count for c, count in orgs_by_country}
    screens_count_map = {c: count for c, count in screens_by_country}
    
    revenue_by_country = db.session.query(
        Organization.country,
        Organization.currency,
        func.sum(Booking.total_price).label('total'),
        func.sum(Booking.total_price * Organization.commission_rate / 100).label('commission')
    ).join(Screen, Screen.organization_id == Organization.id).join(
        Booking, Booking.screen_id == Screen.id
    ).filter(
        Booking.payment_status == 'paid'
    ).group_by(Organization.country, Organization.currency).all()
    
    revenue_by_country_daily = db.session.query(
        Organization.country,
        Organization.currency,
        func.sum(Booking.total_price).label('total'),
        func.sum(Booking.total_price * Organization.commission_rate / 100).label('commission')
    ).join(Screen, Screen.organization_id == Organization.id).join(
        Booking, Booking.screen_id == Screen.id
    ).filter(
        Booking.payment_status == 'paid',
        Booking.created_at >= today
    ).group_by(Organization.country, Organization.currency).all()
    
    revenue_by_country_weekly = db.session.query(
        Organization.country,
        Organization.currency,
        func.sum(Booking.total_price).label('total'),
        func.sum(Booking.total_price * Organization.commission_rate / 100).label('commission')
    ).join(Screen, Screen.organization_id == Organization.id).join(
        Booking, Booking.screen_id == Screen.id
    ).filter(
        Booking.payment_status == 'paid',
        Booking.created_at >= week_ago
    ).group_by(Organization.country, Organization.currency).all()
    
    revenue_by_country_monthly = db.session.query(
        Organization.country,
        Organization.currency,
        func.sum(Booking.total_price).label('total'),
        func.sum(Booking.total_price * Organization.commission_rate / 100).label('commission')
    ).join(Screen, Screen.organization_id == Organization.id).join(
        Booking, Booking.screen_id == Screen.id
    ).filter(
        Booking.payment_status == 'paid',
        Booking.created_at >= month_ago
    ).group_by(Organization.country, Organization.currency).all()
    
    avg_commission_by_country = db.session.query(
        Organization.country,
        func.avg(Organization.commission_rate).label('avg_commission')
    ).group_by(Organization.country).all()
    avg_commission_map = {c: avg for c, avg in avg_commission_by_country}
    
    def build_currency_map(data):
        result = {}
        for country_code, currency_code, total, commission in data:
            cc = country_code or 'FR'
            if cc not in result:
                result[cc] = {}
            currency_info = get_currency_by_code(currency_code or 'EUR')
            result[cc][currency_code or 'EUR'] = {
                'currency_code': currency_code or 'EUR',
                'currency_symbol': currency_info.get('symbol', currency_code),
                'total': total or 0,
                'commission': commission or 0
            }
        return result
    
    daily_map = build_currency_map(revenue_by_country_daily)
    weekly_map = build_currency_map(revenue_by_country_weekly)
    monthly_map = build_currency_map(revenue_by_country_monthly)
    
    country_data = {}
    for country_code, currency_code, total, commission in revenue_by_country:
        cc = country_code or 'FR'
        if cc not in country_data:
            country_info = get_country_by_code(cc)
            country_data[cc] = {
                'country_code': cc,
                'country_name': country_info.get('name', cc),
                'country_flag': country_info.get('flag', ''),
                'org_count': orgs_count_map.get(cc, 0),
                'screen_count': screens_count_map.get(cc, 0),
                'avg_commission': avg_commission_map.get(cc, 0),
                'currencies': []
            }
        currency_info = get_currency_by_code(currency_code or 'EUR')
        curr_code = currency_code or 'EUR'
        country_data[cc]['currencies'].append({
            'currency_code': curr_code,
            'currency_symbol': currency_info.get('symbol', currency_code),
            'total': total or 0,
            'commission': commission or 0,
            'daily_total': daily_map.get(cc, {}).get(curr_code, {}).get('total', 0),
            'daily_commission': daily_map.get(cc, {}).get(curr_code, {}).get('commission', 0),
            'weekly_total': weekly_map.get(cc, {}).get(curr_code, {}).get('total', 0),
            'weekly_commission': weekly_map.get(cc, {}).get(curr_code, {}).get('commission', 0),
            'monthly_total': monthly_map.get(cc, {}).get(curr_code, {}).get('total', 0),
            'monthly_commission': monthly_map.get(cc, {}).get(curr_code, {}).get('commission', 0)
        })
    
    for cc in orgs_count_map:
        if cc not in country_data:
            country_info = get_country_by_code(cc)
            country_data[cc] = {
                'country_code': cc,
                'country_name': country_info.get('name', cc),
                'country_flag': country_info.get('flag', ''),
                'org_count': orgs_count_map.get(cc, 0),
                'screen_count': screens_count_map.get(cc, 0),
                'avg_commission': avg_commission_map.get(cc, 0),
                'currencies': []
            }
    
    country_stats = list(country_data.values())
    
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
    
    admin_base_currency = SiteSetting.get('admin_base_currency', 'EUR')
    admin_currency_info = get_currency_by_code(admin_base_currency)
    
    revenues_by_currency = {}
    commissions_by_currency = {}
    for currency_code, total, commission in revenue_by_currency:
        code = currency_code or 'EUR'
        revenues_by_currency[code] = total or 0
        commissions_by_currency[code] = commission or 0
    
    converted_revenue = calculate_revenue_in_base_currency(revenues_by_currency, admin_base_currency)
    converted_commission = calculate_revenue_in_base_currency(commissions_by_currency, admin_base_currency)
    
    weekly_revenues_by_currency = db.session.query(
        Organization.currency,
        func.sum(Booking.total_price).label('total')
    ).join(Screen, Screen.organization_id == Organization.id).join(
        Booking, Booking.screen_id == Screen.id
    ).filter(
        Booking.payment_status == 'paid',
        Booking.created_at >= week_ago
    ).group_by(Organization.currency).all()
    
    weekly_rev_dict = {(c or 'EUR'): t or 0 for c, t in weekly_revenues_by_currency}
    converted_weekly_revenue = calculate_revenue_in_base_currency(weekly_rev_dict, admin_base_currency)
    
    monthly_revenues_by_currency = db.session.query(
        Organization.currency,
        func.sum(Booking.total_price).label('total')
    ).join(Screen, Screen.organization_id == Organization.id).join(
        Booking, Booking.screen_id == Screen.id
    ).filter(
        Booking.payment_status == 'paid',
        Booking.created_at >= month_ago
    ).group_by(Organization.currency).all()
    
    monthly_rev_dict = {(c or 'EUR'): t or 0 for c, t in monthly_revenues_by_currency}
    converted_monthly_revenue = calculate_revenue_in_base_currency(monthly_rev_dict, admin_base_currency)
    
    for stat in currency_stats:
        stat['converted_total'] = convert_to_base_currency(stat['total'], stat['code'], admin_base_currency)
        stat['converted_commission'] = convert_to_base_currency(stat['commission'], stat['code'], admin_base_currency)
        stat['conversion_rate'] = get_conversion_rate(stat['code'], admin_base_currency)
    
    for stat in country_stats:
        for curr in stat.get('currencies', []):
            curr['converted_total'] = convert_to_base_currency(curr['total'], curr['currency_code'], admin_base_currency)
            curr['converted_commission'] = convert_to_base_currency(curr['commission'], curr['currency_code'], admin_base_currency)
            curr['converted_monthly_total'] = convert_to_base_currency(curr['monthly_total'], curr['currency_code'], admin_base_currency)
            curr['converted_weekly_total'] = convert_to_base_currency(curr['weekly_total'], curr['currency_code'], admin_base_currency)
            curr['converted_daily_total'] = convert_to_base_currency(curr['daily_total'], curr['currency_code'], admin_base_currency)
    
    rates_last_updated = get_rates_last_updated()
    
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
        currency_stats=currency_stats,
        country_stats=country_stats,
        recent_orgs=recent_orgs,
        recent_bookings=recent_bookings,
        top_orgs=top_orgs,
        admin_base_currency=admin_base_currency,
        admin_currency_symbol=admin_currency_info.get('symbol', admin_base_currency),
        converted_revenue=converted_revenue,
        converted_commission=converted_commission,
        converted_weekly_revenue=converted_weekly_revenue,
        converted_monthly_revenue=converted_monthly_revenue,
        rates_last_updated=rates_last_updated
    )


@admin_bp.route('/organizations')
@login_required
@admin_required('organizations')
def organizations():
    orgs = Organization.query.order_by(Organization.created_at.desc()).all()
    return render_template('admin/organizations.html', organizations=orgs)


@admin_bp.route('/organization/<int:org_id>')
@login_required
@admin_required('organizations')
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
@admin_required('organizations')
def toggle_organization(org_id):
    org = Organization.query.get_or_404(org_id)
    org.is_active = not org.is_active
    db.session.commit()
    
    status = "activé" if org.is_active else "désactivé"
    flash(f'Établissement {status} avec succès.', 'success')
    return redirect(url_for('admin.organizations'))


@admin_bp.route('/organization/new', methods=['GET', 'POST'])
@login_required
@admin_required('organizations')
def organization_new():
    from utils.currencies import get_currency_choices, get_country_choices
    currencies = get_currency_choices()
    countries = get_country_choices()
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        org_email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        country = request.form.get('country', 'FR')
        city = request.form.get('city', '').strip()
        currency = request.form.get('currency', 'EUR')
        commission_rate = parse_float_safe(request.form.get('commission_rate'), 
            SiteSetting.get('default_commission_rate', 10.0))
        
        username = request.form.get('username', '').strip()
        manager_email = request.form.get('manager_email', '').strip() or org_email
        password = request.form.get('password', '')
        
        if not name or not org_email:
            flash('Le nom et l\'email sont obligatoires.', 'error')
            return render_template('admin/organization_form.html', org=None, currencies=currencies, countries=countries)
        
        if not username or not password or len(password) < 6:
            flash('Le nom d\'utilisateur et un mot de passe (min 6 caractères) sont obligatoires.', 'error')
            return render_template('admin/organization_form.html', org=None, currencies=currencies, countries=countries)
        
        if Organization.query.filter_by(email=org_email).first():
            flash('Un établissement avec cet email existe déjà.', 'error')
            return render_template('admin/organization_form.html', org=None, currencies=currencies, countries=countries)
        
        if User.query.filter_by(email=manager_email).first():
            flash('Cet email gestionnaire est déjà utilisé.', 'error')
            return render_template('admin/organization_form.html', org=None, currencies=currencies, countries=countries)
        
        if User.query.filter_by(username=username).first():
            flash('Ce nom d\'utilisateur est déjà utilisé.', 'error')
            return render_template('admin/organization_form.html', org=None, currencies=currencies, countries=countries)
        
        is_paid = request.form.get('is_paid', '1') == '1'
        has_iptv = 'has_iptv' in request.form
        iptv_m3u_url = request.form.get('iptv_m3u_url', '').strip() if has_iptv else None
        
        try:
            org = Organization(
                name=name,
                email=org_email,
                phone=phone,
                address=address,
                country=country,
                city=city,
                currency=currency,
                is_paid=is_paid,
                commission_rate=commission_rate if is_paid else 0,
                commission_set_by=current_user.id,
                commission_updated_at=datetime.utcnow(),
                has_iptv=has_iptv,
                iptv_m3u_url=iptv_m3u_url
            )
            db.session.add(org)
            db.session.flush()
            
            user = User(
                username=username,
                email=manager_email,
                role='org',
                organization_id=org.id,
                is_active=True
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            flash(f'Établissement "{name}" créé avec succès!', 'success')
            return redirect(url_for('admin.organizations'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création: {str(e)}', 'error')
            return render_template('admin/organization_form.html', org=None, currencies=currencies, countries=countries)
    
    return render_template('admin/organization_form.html', org=None, currencies=currencies, countries=countries)


@admin_bp.route('/organization/<int:org_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required('organizations')
def organization_edit(org_id):
    from utils.currencies import get_currency_choices, get_country_choices
    currencies = get_currency_choices()
    countries = get_country_choices()
    
    org = Organization.query.get_or_404(org_id)
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        country = request.form.get('country', org.country or 'FR')
        city = request.form.get('city', '').strip()
        currency = request.form.get('currency', org.currency or 'EUR')
        
        if not name or not email:
            flash('Le nom et l\'email sont obligatoires.', 'error')
            return render_template('admin/organization_form.html', org=org, currencies=currencies, countries=countries)
        
        existing = Organization.query.filter(
            Organization.email == email,
            Organization.id != org_id
        ).first()
        if existing:
            flash('Un autre établissement avec cet email existe déjà.', 'error')
            return render_template('admin/organization_form.html', org=org, currencies=currencies, countries=countries)
        
        is_paid = request.form.get('is_paid', '1') == '1'
        has_iptv = 'has_iptv' in request.form
        iptv_m3u_url = request.form.get('iptv_m3u_url', '').strip() if has_iptv else None
        
        org.name = name
        org.email = email
        org.phone = phone
        org.address = address
        org.country = country
        org.city = city
        org.currency = currency
        org.is_paid = is_paid
        org.has_iptv = has_iptv
        org.iptv_m3u_url = iptv_m3u_url
        if not is_paid:
            org.commission_rate = 0
        db.session.commit()
        
        flash(f'Établissement "{name}" mis à jour!', 'success')
        return redirect(url_for('admin.organization_detail', org_id=org_id))
    
    return render_template('admin/organization_form.html', org=org, currencies=currencies, countries=countries)


@admin_bp.route('/organization/<int:org_id>/delete', methods=['POST'])
@login_required
@admin_required('organizations')
def organization_delete(org_id):
    org = Organization.query.get_or_404(org_id)
    
    active_bookings = Booking.query.join(Screen).filter(
        Screen.organization_id == org_id,
        Booking.status.in_(['confirmed', 'pending'])
    ).count()
    
    if active_bookings > 0:
        flash(f'Impossible de supprimer: {active_bookings} réservation(s) active(s).', 'error')
        return redirect(url_for('admin.organization_detail', org_id=org_id))
    
    org_users = User.query.filter_by(organization_id=org_id).all()
    for user in org_users:
        db.session.delete(user)
    
    org_name = org.name
    db.session.delete(org)
    db.session.commit()
    
    flash(f'Établissement "{org_name}" supprimé.', 'success')
    return redirect(url_for('admin.organizations'))


@admin_bp.route('/organization/<int:org_id>/commission', methods=['POST'])
@login_required
@admin_required('organizations')
def update_commission(org_id):
    org = Organization.query.get_or_404(org_id)
    
    try:
        commission_str = request.form.get('commission', '10').replace(',', '.')
        commission = float(commission_str)
    except (ValueError, TypeError):
        flash('Valeur de commission invalide.', 'error')
        return redirect(url_for('admin.organization_detail', org_id=org_id))
    
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
@admin_required('screens')
def screens():
    all_screens = Screen.query.join(Organization).order_by(Screen.created_at.desc()).all()
    return render_template('admin/screens.html', screens=all_screens)


@admin_bp.route('/refresh-exchange-rates', methods=['POST'])
@login_required
@admin_required('settings')
def refresh_exchange_rates():
    """Force refresh exchange rates from API."""
    result = refresh_rates()
    if result.get('success'):
        flash(f'Taux de change actualisés avec succès ({result.get("rates_count", 0)} devises).', 'success')
    else:
        flash(f'Erreur lors de la mise à jour des taux: {result.get("message", "Erreur inconnue")}', 'error')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/stats')
@login_required
@admin_required('stats')
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
    import os
    import secrets
    from werkzeug.utils import secure_filename
    from utils.currencies import get_all_currencies
    
    currencies = get_all_currencies()
    
    if request.method == 'POST':
        min_rate = parse_float_safe(request.form.get('min_commission_rate'), 5.0)
        max_rate = parse_float_safe(request.form.get('max_commission_rate'), 30.0)
        default_rate = parse_float_safe(request.form.get('default_commission_rate'), 10.0)
        
        min_rate = max(0, min(min_rate, 100))
        max_rate = max(0, min(max_rate, 100))
        default_rate = max(0, min(default_rate, 100))
        
        if min_rate > max_rate:
            min_rate, max_rate = max_rate, min_rate
        default_rate = max(min_rate, min(default_rate, max_rate))
        
        string_settings = {
            'site_title': 'seo',
            'site_description': 'seo',
            'meta_keywords': 'seo',
            'google_analytics_id': 'seo',
            'platform_name': 'platform',
            'support_email': 'platform',
            'admin_whatsapp_number': 'platform',
            'head_code': 'platform',
            'default_currency': 'platform',
            'platform_timezone': 'platform',
            'registration_number_label': 'platform',
            'copyright_text': 'platform',
            'made_with_text': 'platform',
            'platform_business_name': 'platform',
            'platform_registration_number': 'platform',
            'platform_vat_number': 'platform',
            'facebook_url': 'social',
            'instagram_url': 'social',
            'twitter_url': 'social',
            'linkedin_url': 'social',
            'youtube_url': 'social',
            'contact_phone': 'contact',
            'contact_address': 'contact',
        }
        
        for key, category in string_settings.items():
            value = request.form.get(key, '')
            SiteSetting.set(key, value, 'string', category)
        
        if 'og_image_file' in request.files:
            file = request.files['og_image_file']
            if file.filename:
                filename = secure_filename(file.filename)
                new_filename = f"og_{secrets.token_hex(8)}_{filename}"
                upload_path = os.path.join('static', 'uploads', 'site')
                os.makedirs(upload_path, exist_ok=True)
                file_path = os.path.join(upload_path, new_filename)
                file.save(file_path)
                SiteSetting.set('og_image', '/' + file_path, 'string', 'seo')
        
        if 'favicon_file' in request.files:
            file = request.files['favicon_file']
            if file.filename:
                filename = secure_filename(file.filename)
                new_filename = f"favicon_{secrets.token_hex(4)}_{filename}"
                upload_path = os.path.join('static', 'uploads', 'site')
                os.makedirs(upload_path, exist_ok=True)
                file_path = os.path.join(upload_path, new_filename)
                file.save(file_path)
                SiteSetting.set('favicon', '/' + file_path, 'string', 'platform')
        
        SiteSetting.set('min_commission_rate', min_rate, 'float', 'platform')
        SiteSetting.set('max_commission_rate', max_rate, 'float', 'platform')
        SiteSetting.set('default_commission_rate', default_rate, 'float', 'platform')
        
        platform_vat_rate = parse_float_safe(request.form.get('platform_vat_rate'), 0)
        platform_vat_rate = max(0, min(platform_vat_rate, 100))
        SiteSetting.set('platform_vat_rate', platform_vat_rate, 'float', 'platform')
        
        maintenance = 'true' if 'maintenance_mode' in request.form else 'false'
        SiteSetting.set('maintenance_mode', maintenance, 'boolean', 'platform')
        
        flash('Paramètres enregistrés avec succès.', 'success')
        return redirect(url_for('admin.settings'))
    
    seo_settings = SiteSetting.get_seo_settings()
    platform_settings = SiteSetting.get_platform_settings()
    platform_settings['admin_whatsapp_number'] = SiteSetting.get('admin_whatsapp_number', '')
    platform_settings['head_code'] = SiteSetting.get('head_code', '')
    platform_settings['favicon'] = SiteSetting.get('favicon', '')
    platform_settings['default_currency'] = SiteSetting.get('default_currency', 'EUR')
    platform_settings['platform_timezone'] = SiteSetting.get('platform_timezone', 'UTC')
    platform_settings['registration_number_label'] = SiteSetting.get('registration_number_label', "Numéro d'immatriculation")
    platform_settings['copyright_text'] = SiteSetting.get('copyright_text', '© Shabaka AdScreen. Tous droits réservés.')
    platform_settings['made_with_text'] = SiteSetting.get('made_with_text', 'Fait avec ❤️ en France')
    platform_settings['facebook_url'] = SiteSetting.get('facebook_url', '')
    platform_settings['instagram_url'] = SiteSetting.get('instagram_url', '')
    platform_settings['twitter_url'] = SiteSetting.get('twitter_url', '')
    platform_settings['linkedin_url'] = SiteSetting.get('linkedin_url', '')
    platform_settings['youtube_url'] = SiteSetting.get('youtube_url', '')
    platform_settings['contact_phone'] = SiteSetting.get('contact_phone', '')
    platform_settings['contact_address'] = SiteSetting.get('contact_address', '')
    platform_settings['platform_business_name'] = SiteSetting.get('platform_business_name', '')
    platform_settings['platform_registration_number'] = SiteSetting.get('platform_registration_number', '')
    platform_settings['platform_vat_number'] = SiteSetting.get('platform_vat_number', '')
    platform_settings['platform_vat_rate'] = SiteSetting.get('platform_vat_rate', 0)
    
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
    
    return render_template('admin/settings.html',
        seo_settings=seo_settings,
        platform_settings=platform_settings,
        currencies=currencies,
        timezones=timezones
    )


@admin_bp.route('/clean-database', methods=['POST'])
@login_required
@superadmin_required
def clean_database():
    """Clean all data except superadmin accounts"""
    import os
    import shutil
    from models import (
        Organization, Screen, TimeSlot, TimePeriod,
        Content, Booking, Filler, InternalContent, StatLog, HeartbeatLog,
        RegistrationRequest, ScreenOverlay, Invoice, PaymentProof,
        Broadcast
    )
    
    try:
        HeartbeatLog.query.delete()
        StatLog.query.delete()
        PaymentProof.query.delete()
        Invoice.query.delete()
        Booking.query.delete()
        Content.query.delete()
        ScreenOverlay.query.delete()
        Broadcast.query.delete()
        InternalContent.query.delete()
        Filler.query.delete()
        TimePeriod.query.delete()
        TimeSlot.query.delete()
        Screen.query.delete()
        
        User.query.filter(User.role != 'superadmin').delete()
        
        Organization.query.delete()
        
        RegistrationRequest.query.delete()
        
        db.session.commit()
        
        uploads_dir = 'static/uploads'
        if os.path.exists(uploads_dir):
            for folder in ['contents', 'fillers', 'internal']:
                folder_path = os.path.join(uploads_dir, folder)
                if os.path.exists(folder_path):
                    shutil.rmtree(folder_path)
                    os.makedirs(folder_path, exist_ok=True)
        
        flash('Base de données nettoyée avec succès. Seuls les comptes superadmin ont été conservés.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors du nettoyage: {str(e)}', 'error')
    
    return redirect(url_for('admin.settings'))


@admin_bp.route('/screen/<int:screen_id>/toggle-featured', methods=['POST'])
@login_required
@superadmin_required
def toggle_featured(screen_id):
    screen = Screen.query.get_or_404(screen_id)
    screen.is_featured = not screen.is_featured
    db.session.commit()
    
    status = "mis en vedette" if screen.is_featured else "retiré de la vedette"
    flash(f'Écran {status}.', 'success')
    return redirect(request.referrer or url_for('admin.screens'))


@admin_bp.route('/screen/<int:screen_id>/assign', methods=['GET', 'POST'])
@login_required
@superadmin_required
def assign_screen(screen_id):
    screen = Screen.query.get_or_404(screen_id)
    organizations = Organization.query.filter_by(is_active=True).order_by(Organization.name).all()
    
    if request.method == 'POST':
        new_org_id = request.form.get('organization_id')
        if new_org_id:
            new_org = Organization.query.get(new_org_id)
            if new_org:
                old_org_name = screen.organization.name if screen.organization else 'Aucun'
                screen.organization_id = new_org.id
                db.session.commit()
                flash(f'Écran "{screen.name}" transféré de "{old_org_name}" vers "{new_org.name}".', 'success')
                return redirect(url_for('admin.screens'))
            else:
                flash('Établissement non trouvé.', 'error')
        else:
            flash('Veuillez sélectionner un établissement.', 'error')
    
    return render_template('admin/assign_screen.html', 
        screen=screen, 
        organizations=organizations
    )


@admin_bp.route('/registration-requests')
@login_required
@superadmin_required
def registration_requests():
    requests = RegistrationRequest.query.order_by(RegistrationRequest.created_at.desc()).all()
    pending_count = RegistrationRequest.get_pending_count()
    return render_template('admin/registration_requests.html', 
        requests=requests,
        pending_count=pending_count
    )


@admin_bp.route('/registration-request/<int:request_id>/approve', methods=['POST'])
@login_required
@superadmin_required
def approve_registration(request_id):
    reg_request = RegistrationRequest.query.get_or_404(request_id)
    
    if reg_request.status != 'pending':
        flash('Cette demande a déjà été traitée.', 'warning')
        return redirect(url_for('admin.registration_requests'))
    
    commission_rate = parse_float_safe(request.form.get('commission_rate'), 
        SiteSetting.get('default_commission_rate', 10.0))
    password = request.form.get('password', '')
    
    if not password or len(password) < 6:
        flash('Le mot de passe doit contenir au moins 6 caractères.', 'error')
        return redirect(url_for('admin.registration_requests'))
    
    org = Organization(
        name=reg_request.org_name,
        email=reg_request.email,
        phone=reg_request.phone,
        address=reg_request.address,
        currency=reg_request.currency or 'EUR',
        commission_rate=commission_rate,
        commission_set_by=current_user.id,
        commission_updated_at=datetime.utcnow()
    )
    db.session.add(org)
    db.session.flush()
    
    user = User(
        username=reg_request.name,
        email=reg_request.email,
        role='org',
        organization_id=org.id
    )
    user.set_password(password)
    db.session.add(user)
    
    reg_request.status = 'approved'
    reg_request.processed_at = datetime.utcnow()
    reg_request.processed_by = current_user.id
    
    db.session.commit()
    
    flash(f'Demande approuvée! Compte créé pour {reg_request.org_name}.', 'success')
    return redirect(url_for('admin.registration_requests'))


@admin_bp.route('/registration-request/<int:request_id>/reject', methods=['POST'])
@login_required
@superadmin_required
def reject_registration(request_id):
    reg_request = RegistrationRequest.query.get_or_404(request_id)
    
    if reg_request.status != 'pending':
        flash('Cette demande a déjà été traitée.', 'warning')
        return redirect(url_for('admin.registration_requests'))
    
    reg_request.status = 'rejected'
    reg_request.processed_at = datetime.utcnow()
    reg_request.processed_by = current_user.id
    reg_request.notes = request.form.get('notes', '')
    
    db.session.commit()
    
    flash('Demande rejetée.', 'info')
    return redirect(url_for('admin.registration_requests'))


@admin_bp.route('/billing')
@login_required
@superadmin_required
def billing():
    from utils.currencies import get_currency_by_code
    from routes.billing_routes import should_generate_weekly_invoice, generate_invoice_for_week
    
    all_orgs = Organization.query.filter_by(is_active=True).all()
    org_ids = [org.id for org in all_orgs]
    
    should_generate, week_start, week_end = should_generate_weekly_invoice()
    
    if should_generate:
        for org_id in org_ids:
            existing = Invoice.query.filter_by(
                organization_id=org_id,
                week_start_date=week_start,
                week_end_date=week_end
            ).first()
            if not existing:
                generate_invoice_for_week(org_id, week_start, week_end)
    
    status_filter = request.args.get('status', 'all')
    org_filter = request.args.get('org_id', '')
    
    query = Invoice.query.join(Organization)
    
    if status_filter != 'all':
        query = query.filter(Invoice.status == status_filter)
    
    if org_filter:
        query = query.filter(Invoice.organization_id == int(org_filter))
    
    invoices = query.order_by(Invoice.week_start_date.desc(), Organization.name).all()
    
    pending_invoices = Invoice.query.filter_by(status=Invoice.STATUS_PENDING).count()
    awaiting_validation = Invoice.query.filter_by(status=Invoice.STATUS_PAID).count()
    validated_invoices = Invoice.query.filter_by(status=Invoice.STATUS_VALIDATED).count()
    
    total_pending_amount = db.session.query(func.sum(Invoice.commission_amount)).filter(
        Invoice.status == Invoice.STATUS_PENDING
    ).scalar() or 0
    
    total_awaiting_amount = db.session.query(func.sum(Invoice.commission_amount)).filter(
        Invoice.status == Invoice.STATUS_PAID
    ).scalar() or 0
    
    total_validated_amount = db.session.query(func.sum(Invoice.commission_amount)).filter(
        Invoice.status == Invoice.STATUS_VALIDATED
    ).scalar() or 0
    
    organizations = Organization.query.filter_by(is_active=True).order_by(Organization.name).all()
    
    return render_template('admin/billing/invoices.html',
        invoices=invoices,
        organizations=organizations,
        status_filter=status_filter,
        org_filter=org_filter,
        pending_invoices=pending_invoices,
        awaiting_validation=awaiting_validation,
        validated_invoices=validated_invoices,
        total_pending_amount=total_pending_amount,
        total_awaiting_amount=total_awaiting_amount,
        total_validated_amount=total_validated_amount
    )


@admin_bp.route('/billing/invoice/<int:invoice_id>')
@login_required
@superadmin_required
def billing_invoice_detail(invoice_id):
    from utils.currencies import get_currency_by_code
    
    invoice = Invoice.query.get_or_404(invoice_id)
    org = invoice.organization
    
    screen_ids = [s.id for s in org.screens]
    bookings = []
    if screen_ids:
        bookings = Booking.query.filter(
            Booking.screen_id.in_(screen_ids),
            Booking.payment_status == 'paid',
            Booking.created_at >= datetime.combine(invoice.week_start_date, datetime.min.time()),
            Booking.created_at <= datetime.combine(invoice.week_end_date, datetime.max.time())
        ).order_by(Booking.created_at.desc()).all()
    
    currency_info = get_currency_by_code(org.currency or 'EUR')
    currency_symbol = currency_info.get('symbol', org.currency or 'EUR')
    
    return render_template('admin/billing/invoice_detail.html',
        invoice=invoice,
        org=org,
        bookings=bookings,
        currency_symbol=currency_symbol
    )


@admin_bp.route('/billing/invoice/<int:invoice_id>/validate', methods=['POST'])
@login_required
@superadmin_required
def validate_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    if invoice.status != Invoice.STATUS_PAID:
        flash('Cette facture ne peut pas être validée.', 'error')
        return redirect(url_for('admin.billing_invoice_detail', invoice_id=invoice_id))
    
    latest_proof = invoice.get_latest_proof()
    if latest_proof:
        latest_proof.status = PaymentProof.STATUS_APPROVED
        latest_proof.reviewed_at = datetime.utcnow()
        latest_proof.reviewed_by = current_user.id
    
    invoice.status = Invoice.STATUS_VALIDATED
    invoice.validated_at = datetime.utcnow()
    invoice.validated_by = current_user.id
    
    db.session.commit()
    
    flash(f'Facture {invoice.invoice_number} validée avec succès!', 'success')
    return redirect(url_for('admin.billing_invoice_detail', invoice_id=invoice_id))


@admin_bp.route('/billing/invoice/<int:invoice_id>/reject', methods=['POST'])
@login_required
@superadmin_required
def reject_invoice_proof(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    if invoice.status != Invoice.STATUS_PAID:
        flash('Aucune preuve de paiement à rejeter.', 'error')
        return redirect(url_for('admin.billing_invoice_detail', invoice_id=invoice_id))
    
    reason = request.form.get('reason', 'Preuve de paiement non conforme')
    
    latest_proof = invoice.get_latest_proof()
    if latest_proof:
        latest_proof.status = PaymentProof.STATUS_REJECTED
        latest_proof.reviewed_at = datetime.utcnow()
        latest_proof.reviewed_by = current_user.id
        latest_proof.review_notes = reason
    
    invoice.status = Invoice.STATUS_PENDING
    invoice.paid_at = None
    
    db.session.commit()
    
    flash('Preuve de paiement refusée. L\'établissement devra soumettre une nouvelle preuve.', 'info')
    return redirect(url_for('admin.billing_invoice_detail', invoice_id=invoice_id))


@admin_bp.route('/billing/proof/<int:proof_id>/view')
@login_required
@superadmin_required
def view_payment_proof(proof_id):
    import os
    proof = PaymentProof.query.get_or_404(proof_id)
    
    if os.path.exists(proof.file_path):
        return send_file(proof.file_path, as_attachment=False)
    else:
        flash('Fichier non trouvé.', 'error')
        return redirect(url_for('admin.billing_invoice_detail', invoice_id=proof.invoice_id))


@admin_bp.route('/broadcasts')
@login_required
@superadmin_required
def broadcasts():
    all_broadcasts = Broadcast.query.order_by(Broadcast.created_at.desc()).all()
    active_count = Broadcast.query.filter_by(is_active=True).count()
    
    for b in all_broadcasts:
        b.target_screens_count = len(b.get_target_screens())
    
    return render_template('admin/broadcasts/list.html',
        broadcasts=all_broadcasts,
        active_count=active_count
    )


@admin_bp.route('/broadcast/new', methods=['GET', 'POST'])
@login_required
@superadmin_required
def broadcast_new():
    import os
    import secrets
    from werkzeug.utils import secure_filename
    from utils.countries import get_all_countries
    from utils.world_data import WORLD_CITIES
    from models.broadcast import COMMON_TIMEZONES
    
    countries = get_all_countries()
    organizations = Organization.query.filter_by(is_active=True).order_by(Organization.name).all()
    screens = Screen.query.filter_by(is_active=True).join(Organization).order_by(Organization.name, Screen.name).all()
    
    cities_by_country = WORLD_CITIES
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        target_type = request.form.get('target_type', 'country')
        target_org_type = request.form.get('target_org_type', 'all')
        broadcast_type = request.form.get('broadcast_type', 'overlay')
        timezone = request.form.get('timezone', 'Europe/Paris')
        
        if not name:
            flash('Le nom de la diffusion est obligatoire.', 'error')
            return render_template('admin/broadcasts/form.html',
                broadcast=None,
                countries=countries,
                organizations=organizations,
                screens=screens,
                cities_by_country=cities_by_country,
                timezones=COMMON_TIMEZONES
            )
        
        broadcast = Broadcast(
            name=name,
            target_type=target_type,
            target_org_type=target_org_type,
            broadcast_type=broadcast_type,
            timezone=timezone,
            created_by=current_user.id
        )
        
        if target_type == 'country':
            broadcast.target_country = request.form.get('target_country', 'FR')
        elif target_type == 'city':
            broadcast.target_country = request.form.get('target_country_city', 'FR')
            broadcast.target_city = request.form.get('target_city', '')
        elif target_type == 'organization':
            org_id = request.form.get('target_organization_id')
            broadcast.target_organization_id = int(org_id) if org_id else None
        elif target_type == 'screen':
            screen_id = request.form.get('target_screen_id')
            broadcast.target_screen_id = int(screen_id) if screen_id else None
        
        if broadcast_type == 'overlay':
            overlay_type = request.form.get('overlay_type', 'ticker')
            broadcast.overlay_type = overlay_type
            broadcast.overlay_message = request.form.get('overlay_message', '')
            broadcast.overlay_position = request.form.get('overlay_position', 'footer')
            broadcast.overlay_background_color = request.form.get('overlay_background_color', '#000000')
            broadcast.overlay_text_color = request.form.get('overlay_text_color', '#FFFFFF')
            broadcast.overlay_font_size = int(request.form.get('overlay_font_size', 24))
            broadcast.overlay_scroll_speed = int(request.form.get('overlay_scroll_speed', 50))
            
            if overlay_type == 'image' or overlay_type == 'corner':
                broadcast.overlay_corner_position = request.form.get('overlay_corner_position', 'top_left')
                broadcast.overlay_corner_size = int(request.form.get('overlay_corner_size', 15))
                broadcast.overlay_image_width_percent = float(request.form.get('overlay_image_width_percent', 20))
                broadcast.overlay_image_pos_x = int(request.form.get('overlay_image_pos_x', 0))
                broadcast.overlay_image_pos_y = int(request.form.get('overlay_image_pos_y', 0))
                broadcast.overlay_image_opacity = float(request.form.get('overlay_image_opacity', 1.0))
                
                if overlay_type == 'image':
                    image_position = request.form.get('overlay_image_position', 'top_right')
                    if image_position in ['header', 'body', 'footer']:
                        broadcast.overlay_position = image_position
                        broadcast.overlay_position_mode = 'linear'
                    elif image_position == 'custom':
                        broadcast.overlay_position = 'custom'
                        broadcast.overlay_position_mode = 'custom'
                    else:
                        broadcast.overlay_position = 'corner'
                        broadcast.overlay_position_mode = 'corner'
                        broadcast.overlay_corner_position = image_position
                
                if 'overlay_image' in request.files:
                    file = request.files['overlay_image']
                    if file.filename:
                        filename = secure_filename(file.filename)
                        new_filename = f"broadcast_{secrets.token_hex(8)}_{filename}"
                        upload_path = os.path.join('static', 'uploads', 'broadcasts')
                        os.makedirs(upload_path, exist_ok=True)
                        file_path = os.path.join(upload_path, new_filename)
                        file.save(file_path)
                        broadcast.overlay_image_path = file_path
        else:
            broadcast.content_duration = int(request.form.get('content_duration', 10))
            broadcast.content_priority = int(request.form.get('content_priority', 200))
            
            if 'content_file' in request.files:
                file = request.files['content_file']
                if file.filename:
                    filename = secure_filename(file.filename)
                    new_filename = f"broadcast_{secrets.token_hex(8)}_{filename}"
                    upload_path = os.path.join('static', 'uploads', 'broadcasts')
                    os.makedirs(upload_path, exist_ok=True)
                    file_path = os.path.join(upload_path, new_filename)
                    file.save(file_path)
                    broadcast.content_file_path = file_path
                    
                    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
                    if ext in ['mp4', 'webm', 'mov', 'avi']:
                        broadcast.content_type = 'video'
                    else:
                        broadcast.content_type = 'image'
        
        broadcast.is_active = 'is_active' in request.form
        
        schedule_mode = request.form.get('schedule_mode', 'immediate')
        broadcast.schedule_mode = schedule_mode
        
        if schedule_mode == 'scheduled':
            scheduled_datetime_str = request.form.get('scheduled_datetime', '')
            if scheduled_datetime_str:
                try:
                    broadcast.scheduled_datetime = datetime.fromisoformat(scheduled_datetime_str)
                except ValueError:
                    pass
            
            schedule_priority = request.form.get('schedule_priority', '100')
            broadcast.schedule_priority = int(schedule_priority) if schedule_priority else 100
            broadcast.override_playlist = 'override_playlist' in request.form
            
            recurrence_type = request.form.get('recurrence_type', 'none')
            broadcast.recurrence_type = recurrence_type
            
            if recurrence_type != 'none':
                recurrence_interval = request.form.get('recurrence_interval', '1')
                broadcast.recurrence_interval = int(recurrence_interval) if recurrence_interval else 1
                
                recurrence_time_str = request.form.get('recurrence_time', '')
                if recurrence_time_str:
                    try:
                        from datetime import time as dt_time
                        time_parts = recurrence_time_str.split(':')
                        broadcast.recurrence_time = dt_time(int(time_parts[0]), int(time_parts[1]), int(time_parts[2]) if len(time_parts) > 2 else 0)
                    except (ValueError, IndexError):
                        pass
                
                recurrence_end_date_str = request.form.get('recurrence_end_date', '')
                if recurrence_end_date_str:
                    try:
                        broadcast.recurrence_end_date = datetime.strptime(recurrence_end_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        pass
                
                if recurrence_type == 'weekly' or recurrence_type == 'custom':
                    days = request.form.getlist('recurrence_days[]')
                    broadcast.recurrence_days_of_week = ','.join(days) if days else None
        else:
            start_datetime_str = request.form.get('start_datetime', '')
            end_datetime_str = request.form.get('end_datetime', '')
            
            if start_datetime_str:
                try:
                    broadcast.start_datetime = datetime.fromisoformat(start_datetime_str)
                except ValueError:
                    pass
            
            if end_datetime_str:
                try:
                    broadcast.end_datetime = datetime.fromisoformat(end_datetime_str)
                except ValueError:
                    pass
        
        db.session.add(broadcast)
        db.session.commit()
        
        flash(f'Diffusion "{name}" créée avec succès!', 'success')
        return redirect(url_for('admin.broadcasts'))
    
    return render_template('admin/broadcasts/form.html',
        broadcast=None,
        countries=countries,
        organizations=organizations,
        screens=screens,
        cities_by_country=cities_by_country,
        timezones=COMMON_TIMEZONES
    )


@admin_bp.route('/broadcast/<int:broadcast_id>/edit', methods=['GET', 'POST'])
@login_required
@superadmin_required
def broadcast_edit(broadcast_id):
    import os
    import secrets
    from werkzeug.utils import secure_filename
    from utils.countries import get_all_countries
    from utils.world_data import WORLD_CITIES
    from models.broadcast import COMMON_TIMEZONES
    
    broadcast = Broadcast.query.get_or_404(broadcast_id)
    countries = get_all_countries()
    organizations = Organization.query.filter_by(is_active=True).order_by(Organization.name).all()
    screens = Screen.query.filter_by(is_active=True).join(Organization).order_by(Organization.name, Screen.name).all()
    
    cities_by_country = WORLD_CITIES
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        target_type = request.form.get('target_type', 'country')
        target_org_type = request.form.get('target_org_type', 'all')
        broadcast_type = request.form.get('broadcast_type', 'overlay')
        timezone = request.form.get('timezone', 'Europe/Paris')
        
        if not name:
            flash('Le nom de la diffusion est obligatoire.', 'error')
            return render_template('admin/broadcasts/form.html',
                broadcast=broadcast,
                countries=countries,
                organizations=organizations,
                screens=screens,
                cities_by_country=cities_by_country,
                timezones=COMMON_TIMEZONES
            )
        
        broadcast.name = name
        broadcast.target_type = target_type
        broadcast.target_org_type = target_org_type
        broadcast.broadcast_type = broadcast_type
        broadcast.timezone = timezone
        
        broadcast.target_country = None
        broadcast.target_city = None
        broadcast.target_organization_id = None
        broadcast.target_screen_id = None
        
        if target_type == 'country':
            broadcast.target_country = request.form.get('target_country', 'FR')
        elif target_type == 'city':
            broadcast.target_country = request.form.get('target_country_city', 'FR')
            broadcast.target_city = request.form.get('target_city', '')
        elif target_type == 'organization':
            org_id = request.form.get('target_organization_id')
            broadcast.target_organization_id = int(org_id) if org_id else None
        elif target_type == 'screen':
            screen_id = request.form.get('target_screen_id')
            broadcast.target_screen_id = int(screen_id) if screen_id else None
        
        if broadcast_type == 'overlay':
            overlay_type = request.form.get('overlay_type', 'ticker')
            broadcast.overlay_type = overlay_type
            broadcast.overlay_message = request.form.get('overlay_message', '')
            broadcast.overlay_position = request.form.get('overlay_position', 'footer')
            broadcast.overlay_background_color = request.form.get('overlay_background_color', '#000000')
            broadcast.overlay_text_color = request.form.get('overlay_text_color', '#FFFFFF')
            broadcast.overlay_font_size = int(request.form.get('overlay_font_size', 24))
            broadcast.overlay_scroll_speed = int(request.form.get('overlay_scroll_speed', 50))
            
            if overlay_type == 'image' or overlay_type == 'corner':
                broadcast.overlay_corner_position = request.form.get('overlay_corner_position', 'top_left')
                broadcast.overlay_corner_size = int(request.form.get('overlay_corner_size', 15))
                broadcast.overlay_image_width_percent = float(request.form.get('overlay_image_width_percent', 20))
                broadcast.overlay_image_pos_x = int(request.form.get('overlay_image_pos_x', 0))
                broadcast.overlay_image_pos_y = int(request.form.get('overlay_image_pos_y', 0))
                broadcast.overlay_image_opacity = float(request.form.get('overlay_image_opacity', 1.0))
                
                if overlay_type == 'image':
                    image_position = request.form.get('overlay_image_position', 'top_right')
                    if image_position in ['header', 'body', 'footer']:
                        broadcast.overlay_position = image_position
                        broadcast.overlay_position_mode = 'linear'
                    elif image_position == 'custom':
                        broadcast.overlay_position = 'custom'
                        broadcast.overlay_position_mode = 'custom'
                    else:
                        broadcast.overlay_position = 'corner'
                        broadcast.overlay_position_mode = 'corner'
                        broadcast.overlay_corner_position = image_position
                
                if 'overlay_image' in request.files:
                    file = request.files['overlay_image']
                    if file.filename:
                        if broadcast.overlay_image_path and os.path.exists(broadcast.overlay_image_path):
                            os.remove(broadcast.overlay_image_path)
                        
                        filename = secure_filename(file.filename)
                        new_filename = f"broadcast_{secrets.token_hex(8)}_{filename}"
                        upload_path = os.path.join('static', 'uploads', 'broadcasts')
                        os.makedirs(upload_path, exist_ok=True)
                        file_path = os.path.join(upload_path, new_filename)
                        file.save(file_path)
                        broadcast.overlay_image_path = file_path
        else:
            broadcast.content_duration = int(request.form.get('content_duration', 10))
            broadcast.content_priority = int(request.form.get('content_priority', 200))
            
            if 'content_file' in request.files:
                file = request.files['content_file']
                if file.filename:
                    if broadcast.content_file_path and os.path.exists(broadcast.content_file_path):
                        os.remove(broadcast.content_file_path)
                    
                    filename = secure_filename(file.filename)
                    new_filename = f"broadcast_{secrets.token_hex(8)}_{filename}"
                    upload_path = os.path.join('static', 'uploads', 'broadcasts')
                    os.makedirs(upload_path, exist_ok=True)
                    file_path = os.path.join(upload_path, new_filename)
                    file.save(file_path)
                    broadcast.content_file_path = file_path
                    
                    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
                    if ext in ['mp4', 'webm', 'mov', 'avi']:
                        broadcast.content_type = 'video'
                    else:
                        broadcast.content_type = 'image'
        
        broadcast.is_active = 'is_active' in request.form
        
        schedule_mode = request.form.get('schedule_mode', 'immediate')
        broadcast.schedule_mode = schedule_mode
        
        if schedule_mode == 'scheduled':
            scheduled_datetime_str = request.form.get('scheduled_datetime', '')
            if scheduled_datetime_str:
                try:
                    broadcast.scheduled_datetime = datetime.fromisoformat(scheduled_datetime_str)
                except ValueError:
                    pass
            else:
                broadcast.scheduled_datetime = None
            
            schedule_priority = request.form.get('schedule_priority', '100')
            broadcast.schedule_priority = int(schedule_priority) if schedule_priority else 100
            broadcast.override_playlist = 'override_playlist' in request.form
            
            recurrence_type = request.form.get('recurrence_type', 'none')
            broadcast.recurrence_type = recurrence_type
            
            if recurrence_type != 'none':
                recurrence_interval = request.form.get('recurrence_interval', '1')
                broadcast.recurrence_interval = int(recurrence_interval) if recurrence_interval else 1
                
                recurrence_time_str = request.form.get('recurrence_time', '')
                if recurrence_time_str:
                    try:
                        from datetime import time as dt_time
                        time_parts = recurrence_time_str.split(':')
                        broadcast.recurrence_time = dt_time(int(time_parts[0]), int(time_parts[1]), int(time_parts[2]) if len(time_parts) > 2 else 0)
                    except (ValueError, IndexError):
                        pass
                else:
                    broadcast.recurrence_time = None
                
                recurrence_end_date_str = request.form.get('recurrence_end_date', '')
                if recurrence_end_date_str:
                    try:
                        broadcast.recurrence_end_date = datetime.strptime(recurrence_end_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        pass
                else:
                    broadcast.recurrence_end_date = None
                
                if recurrence_type == 'weekly' or recurrence_type == 'custom':
                    days = request.form.getlist('recurrence_days[]')
                    broadcast.recurrence_days_of_week = ','.join(days) if days else None
                else:
                    broadcast.recurrence_days_of_week = None
            else:
                broadcast.recurrence_interval = 1
                broadcast.recurrence_time = None
                broadcast.recurrence_end_date = None
                broadcast.recurrence_days_of_week = None
        else:
            broadcast.scheduled_datetime = None
            broadcast.schedule_priority = 100
            broadcast.override_playlist = False
            broadcast.recurrence_type = 'none'
            broadcast.recurrence_interval = 1
            broadcast.recurrence_time = None
            broadcast.recurrence_end_date = None
            broadcast.recurrence_days_of_week = None
            
            start_datetime_str = request.form.get('start_datetime', '')
            end_datetime_str = request.form.get('end_datetime', '')
            
            broadcast.start_datetime = None
            broadcast.end_datetime = None
            
            if start_datetime_str:
                try:
                    broadcast.start_datetime = datetime.fromisoformat(start_datetime_str)
                except ValueError:
                    pass
            
            if end_datetime_str:
                try:
                    broadcast.end_datetime = datetime.fromisoformat(end_datetime_str)
                except ValueError:
                    pass
        
        db.session.commit()
        
        flash(f'Diffusion "{name}" mise à jour!', 'success')
        return redirect(url_for('admin.broadcasts'))
    
    return render_template('admin/broadcasts/form.html',
        broadcast=broadcast,
        countries=countries,
        organizations=organizations,
        screens=screens,
        cities_by_country=cities_by_country,
        timezones=COMMON_TIMEZONES
    )


@admin_bp.route('/broadcast/<int:broadcast_id>/toggle', methods=['POST'])
@login_required
@superadmin_required
def broadcast_toggle(broadcast_id):
    broadcast = Broadcast.query.get_or_404(broadcast_id)
    broadcast.is_active = not broadcast.is_active
    db.session.commit()
    
    status = "activée" if broadcast.is_active else "désactivée"
    flash(f'Diffusion {status}.', 'success')
    return redirect(url_for('admin.broadcasts'))


@admin_bp.route('/broadcast/<int:broadcast_id>/delete', methods=['POST'])
@login_required
@superadmin_required
def broadcast_delete(broadcast_id):
    import os
    broadcast = Broadcast.query.get_or_404(broadcast_id)
    
    if broadcast.overlay_image_path and os.path.exists(broadcast.overlay_image_path):
        os.remove(broadcast.overlay_image_path)
    
    if broadcast.content_file_path and os.path.exists(broadcast.content_file_path):
        os.remove(broadcast.content_file_path)
    
    name = broadcast.name
    db.session.delete(broadcast)
    db.session.commit()
    
    flash(f'Diffusion "{name}" supprimée.', 'success')
    return redirect(url_for('admin.broadcasts'))


@admin_bp.route('/api/cities/<country_code>')
@login_required
@superadmin_required
def get_cities_by_country(country_code):
    from flask import jsonify
    
    cities = db.session.query(Organization.city).filter(
        Organization.country == country_code,
        Organization.city.isnot(None),
        Organization.city != ''
    ).distinct().order_by(Organization.city).all()
    
    city_list = [city[0] for city in cities if city[0]]
    return jsonify(city_list)


@admin_bp.route('/users')
@login_required
@superadmin_required
def admin_users():
    from models.user import ADMIN_PERMISSIONS
    admin_users = User.query.filter(User.role.in_(['superadmin', 'admin'])).order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', 
                           admin_users=admin_users, 
                           permissions=ADMIN_PERMISSIONS)


@admin_bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@superadmin_required
def admin_user_new():
    from models.user import ADMIN_PERMISSIONS
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        selected_permissions = request.form.getlist('permissions')
        
        if not username or not email or not password:
            flash('Tous les champs sont obligatoires.', 'error')
            return render_template('admin/user_form.html', user=None, permissions=ADMIN_PERMISSIONS)
        
        if len(password) < 6:
            flash('Le mot de passe doit contenir au moins 6 caractères.', 'error')
            return render_template('admin/user_form.html', user=None, permissions=ADMIN_PERMISSIONS)
        
        if User.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé.', 'error')
            return render_template('admin/user_form.html', user=None, permissions=ADMIN_PERMISSIONS)
        
        if User.query.filter_by(username=username).first():
            flash('Ce nom d\'utilisateur est déjà utilisé.', 'error')
            return render_template('admin/user_form.html', user=None, permissions=ADMIN_PERMISSIONS)
        
        try:
            user = User(
                username=username,
                email=email,
                role='admin',
                is_active=True
            )
            user.set_password(password)
            user.set_permissions(selected_permissions)
            db.session.add(user)
            db.session.commit()
            
            flash(f'Administrateur "{username}" créé avec succès!', 'success')
            return redirect(url_for('admin.admin_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création: {str(e)}', 'error')
            return render_template('admin/user_form.html', user=None, permissions=ADMIN_PERMISSIONS)
    
    return render_template('admin/user_form.html', user=None, permissions=ADMIN_PERMISSIONS)


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@superadmin_required
def admin_user_edit(user_id):
    from models.user import ADMIN_PERMISSIONS
    
    user = User.query.get_or_404(user_id)
    
    if user.role == 'superadmin' and user.id != current_user.id:
        flash('Vous ne pouvez pas modifier un autre super administrateur.', 'error')
        return redirect(url_for('admin.admin_users'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        selected_permissions = request.form.getlist('permissions')
        is_active = 'is_active' in request.form
        
        if not username or not email:
            flash('Le nom d\'utilisateur et l\'email sont obligatoires.', 'error')
            return render_template('admin/user_form.html', user=user, permissions=ADMIN_PERMISSIONS)
        
        existing_email = User.query.filter(User.email == email, User.id != user_id).first()
        if existing_email:
            flash('Cet email est déjà utilisé par un autre utilisateur.', 'error')
            return render_template('admin/user_form.html', user=user, permissions=ADMIN_PERMISSIONS)
        
        existing_username = User.query.filter(User.username == username, User.id != user_id).first()
        if existing_username:
            flash('Ce nom d\'utilisateur est déjà utilisé.', 'error')
            return render_template('admin/user_form.html', user=user, permissions=ADMIN_PERMISSIONS)
        
        try:
            user.username = username
            user.email = email
            user.is_active = is_active
            
            if user.role != 'superadmin':
                user.set_permissions(selected_permissions)
            
            if password and len(password) >= 6:
                user.set_password(password)
            elif password and len(password) < 6:
                flash('Le mot de passe doit contenir au moins 6 caractères.', 'error')
                return render_template('admin/user_form.html', user=user, permissions=ADMIN_PERMISSIONS)
            
            db.session.commit()
            flash(f'Administrateur "{username}" mis à jour!', 'success')
            return redirect(url_for('admin.admin_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la mise à jour: {str(e)}', 'error')
            return render_template('admin/user_form.html', user=user, permissions=ADMIN_PERMISSIONS)
    
    return render_template('admin/user_form.html', user=user, permissions=ADMIN_PERMISSIONS)


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@superadmin_required
def admin_user_delete(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.role == 'superadmin':
        flash('Impossible de supprimer un super administrateur.', 'error')
        return redirect(url_for('admin.admin_users'))
    
    if user.id == current_user.id:
        flash('Vous ne pouvez pas supprimer votre propre compte.', 'error')
        return redirect(url_for('admin.admin_users'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    flash(f'Administrateur "{username}" supprimé.', 'success')
    return redirect(url_for('admin.admin_users'))


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@superadmin_required
def admin_user_toggle(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.role == 'superadmin':
        flash('Impossible de désactiver un super administrateur.', 'error')
        return redirect(url_for('admin.admin_users'))
    
    if user.id == current_user.id:
        flash('Vous ne pouvez pas désactiver votre propre compte.', 'error')
        return redirect(url_for('admin.admin_users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = "activé" if user.is_active else "désactivé"
    flash(f'Administrateur {status}.', 'success')
    return redirect(url_for('admin.admin_users'))
