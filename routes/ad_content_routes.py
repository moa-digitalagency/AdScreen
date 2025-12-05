import os
import secrets
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from werkzeug.utils import secure_filename
from app import db
from models import Organization, Screen, SiteSetting, TimePeriod, TimeSlot, Booking
from models.ad_content import AdContent, AdContentInvoice, AdContentStat
from utils.countries import get_all_countries
from utils.currencies import get_currency_by_code
from services.availability_service import calculate_availability
from sqlalchemy import func, or_

ad_content_bp = Blueprint('ad_content', __name__)


def superadmin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_superadmin():
            flash('Accès réservé aux super administrateurs.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'webm', 'mov'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@ad_content_bp.route('/ad-contents')
@login_required
@superadmin_required
def list_ads():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    status_filter = request.args.get('status', '')
    
    query = AdContent.query
    
    if status_filter:
        query = query.filter(AdContent.status == status_filter)
    
    for ad in query.all():
        ad.update_status()
    db.session.commit()
    
    ads = query.order_by(AdContent.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    total_active = AdContent.query.filter(AdContent.status == AdContent.STATUS_ACTIVE).count()
    total_scheduled = AdContent.query.filter(AdContent.status == AdContent.STATUS_SCHEDULED).count()
    total_expired = AdContent.query.filter(AdContent.status == AdContent.STATUS_EXPIRED).count()
    
    total_revenue = db.session.query(func.sum(AdContent.total_price)).filter(
        AdContent.status.in_([AdContent.STATUS_ACTIVE, AdContent.STATUS_EXPIRED])
    ).scalar() or 0
    
    return render_template('admin/ad_contents/list.html',
        ads=ads,
        status_filter=status_filter,
        total_active=total_active,
        total_scheduled=total_scheduled,
        total_expired=total_expired,
        total_revenue=total_revenue
    )


@ad_content_bp.route('/ad-content/new', methods=['GET', 'POST'])
@login_required
@superadmin_required
def create():
    countries = get_all_countries()
    organizations = Organization.query.filter_by(is_active=True).order_by(Organization.name).all()
    screens = Screen.query.filter_by(is_active=True).join(Organization).order_by(Organization.name, Screen.name).all()
    ad_settings = SiteSetting.get_ad_content_settings()
    
    cities_by_country = {}
    for org in organizations:
        country = org.country or 'FR'
        if country not in cities_by_country:
            cities_by_country[country] = set()
        if org.city:
            cities_by_country[country].add(org.city)
    cities_by_country = {k: sorted(list(v)) for k, v in cities_by_country.items()}
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        target_type = request.form.get('target_type', 'country')
        target_org_type = request.form.get('target_org_type', 'all')
        
        if not name:
            flash('Le nom du contenu est obligatoire.', 'error')
            return render_template('admin/ad_contents/form.html',
                ad=None,
                countries=countries,
                organizations=organizations,
                screens=screens,
                cities_by_country=cities_by_country,
                ad_settings=ad_settings
            )
        
        ad = AdContent(
            name=name,
            description=description,
            target_type=target_type,
            target_org_type=target_org_type,
            created_by=current_user.id,
            commission_rate=ad_settings.get('ad_commission_rate', 30.0)
        )
        ad.generate_reference()
        
        if target_type == 'country':
            ad.target_country = request.form.get('target_country', 'FR')
        elif target_type == 'city':
            ad.target_country = request.form.get('target_country_city', 'FR')
            ad.target_city = request.form.get('target_city', '')
        elif target_type == 'organization':
            org_id = request.form.get('target_organization_id')
            ad.target_organization_id = int(org_id) if org_id else None
        elif target_type == 'screen':
            screen_id = request.form.get('target_screen_id')
            ad.target_screen_id = int(screen_id) if screen_id else None
        
        selected_screen_ids_str = request.form.get('selected_screen_ids', '')
        if selected_screen_ids_str:
            screen_ids = [int(x) for x in selected_screen_ids_str.split(',') if x.strip()]
            if screen_ids:
                ad.target_type = AdContent.TARGET_SCREENS
                ad.set_selected_screen_ids(screen_ids)
        
        ad.advertiser_name = request.form.get('advertiser_name', '').strip()
        ad.advertiser_email = request.form.get('advertiser_email', '').strip()
        ad.advertiser_phone = request.form.get('advertiser_phone', '').strip()
        ad.advertiser_company = request.form.get('advertiser_company', '').strip()
        
        total_price = request.form.get('total_price', '0')
        ad.total_price = float(total_price) if total_price else 0.0
        ad.currency = request.form.get('currency', 'EUR')
        
        commission_rate = request.form.get('commission_rate', '')
        if commission_rate:
            ad.commission_rate = float(commission_rate)
        
        start_date_str = request.form.get('start_date', '')
        end_date_str = request.form.get('end_date', '')
        
        if start_date_str and end_date_str:
            ad.schedule_type = AdContent.SCHEDULE_PERIOD
            try:
                ad.start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                try:
                    ad.start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                except ValueError:
                    ad.start_date = datetime.now()
            
            try:
                ad.end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                try:
                    ad.end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                except ValueError:
                    ad.end_date = datetime.now() + timedelta(days=7)
            
            min_plays = request.form.get('min_plays', '10')
            ad.plays_per_day = int(min_plays) if min_plays else 10
            
            if ad.start_date <= datetime.now():
                ad.status = AdContent.STATUS_ACTIVE
            else:
                ad.status = AdContent.STATUS_SCHEDULED
        else:
            ad.schedule_type = AdContent.SCHEDULE_IMMEDIATE
            ad.plays_per_day = int(request.form.get('min_plays', '10'))
            ad.status = AdContent.STATUS_ACTIVE
        
        if 'content_file' in request.files:
            file = request.files['content_file']
            if file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                new_filename = f"ad_{secrets.token_hex(8)}_{filename}"
                upload_path = os.path.join('static', 'uploads', 'ad_contents')
                os.makedirs(upload_path, exist_ok=True)
                file_path = os.path.join(upload_path, new_filename)
                file.save(file_path)
                ad.file_path = file_path
                
                ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
                if ext in ['mp4', 'webm', 'mov']:
                    ad.content_type = 'video'
                else:
                    ad.content_type = 'image'
                
                ad.file_size = os.path.getsize(file_path)
        else:
            content_type = request.form.get('content_type', 'image')
            ad.content_type = content_type
        
        slot_duration = request.form.get('slot_duration', '10')
        ad.duration = int(slot_duration) if slot_duration else 10
        
        db.session.add(ad)
        db.session.commit()
        
        flash(f'Contenu publicitaire "{name}" créé avec succès! Référence: {ad.reference}', 'success')
        return redirect(url_for('ad_content.list_ads'))
    
    return render_template('admin/ad_contents/form.html',
        ad=None,
        countries=countries,
        organizations=organizations,
        screens=screens,
        cities_by_country=cities_by_country,
        ad_settings=ad_settings
    )


@ad_content_bp.route('/ad-content/<int:ad_id>/edit', methods=['GET', 'POST'])
@login_required
@superadmin_required
def edit(ad_id):
    ad = AdContent.query.get_or_404(ad_id)
    countries = get_all_countries()
    organizations = Organization.query.filter_by(is_active=True).order_by(Organization.name).all()
    screens = Screen.query.filter_by(is_active=True).join(Organization).order_by(Organization.name, Screen.name).all()
    ad_settings = SiteSetting.get_ad_content_settings()
    
    cities_by_country = {}
    for org in organizations:
        country = org.country or 'FR'
        if country not in cities_by_country:
            cities_by_country[country] = set()
        if org.city:
            cities_by_country[country].add(org.city)
    cities_by_country = {k: sorted(list(v)) for k, v in cities_by_country.items()}
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        target_type = request.form.get('target_type', 'country')
        target_org_type = request.form.get('target_org_type', 'all')
        
        if not name:
            flash('Le nom du contenu est obligatoire.', 'error')
            return render_template('admin/ad_contents/form.html',
                ad=ad,
                countries=countries,
                organizations=organizations,
                screens=screens,
                cities_by_country=cities_by_country,
                ad_settings=ad_settings
            )
        
        ad.name = name
        ad.description = description
        ad.target_type = target_type
        ad.target_org_type = target_org_type
        
        ad.target_country = None
        ad.target_city = None
        ad.target_organization_id = None
        ad.target_screen_id = None
        
        if target_type == 'country':
            ad.target_country = request.form.get('target_country', 'FR')
        elif target_type == 'city':
            ad.target_country = request.form.get('target_country_city', 'FR')
            ad.target_city = request.form.get('target_city', '')
        elif target_type == 'organization':
            org_id = request.form.get('target_organization_id')
            ad.target_organization_id = int(org_id) if org_id else None
        elif target_type == 'screen':
            screen_id = request.form.get('target_screen_id')
            ad.target_screen_id = int(screen_id) if screen_id else None
        
        ad.advertiser_name = request.form.get('advertiser_name', '').strip()
        ad.advertiser_email = request.form.get('advertiser_email', '').strip()
        ad.advertiser_phone = request.form.get('advertiser_phone', '').strip()
        ad.advertiser_company = request.form.get('advertiser_company', '').strip()
        
        total_price = request.form.get('total_price', '0')
        ad.total_price = float(total_price) if total_price else 0.0
        ad.currency = request.form.get('currency', 'EUR')
        
        commission_rate = request.form.get('commission_rate', '')
        if commission_rate:
            ad.commission_rate = float(commission_rate)
        
        schedule_type = request.form.get('schedule_type', 'immediate')
        ad.schedule_type = schedule_type
        
        if schedule_type == 'period':
            start_date_str = request.form.get('start_date', '')
            end_date_str = request.form.get('end_date', '')
            
            if start_date_str:
                try:
                    ad.start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
                except ValueError:
                    try:
                        ad.start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                    except ValueError:
                        pass
            
            if end_date_str:
                try:
                    ad.end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M')
                except ValueError:
                    try:
                        ad.end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                    except ValueError:
                        pass
        
        if 'content_file' in request.files:
            file = request.files['content_file']
            if file.filename and allowed_file(file.filename):
                if ad.file_path and os.path.exists(ad.file_path):
                    try:
                        os.remove(ad.file_path)
                    except:
                        pass
                
                filename = secure_filename(file.filename)
                new_filename = f"ad_{secrets.token_hex(8)}_{filename}"
                upload_path = os.path.join('static', 'uploads', 'ad_contents')
                os.makedirs(upload_path, exist_ok=True)
                file_path = os.path.join(upload_path, new_filename)
                file.save(file_path)
                ad.file_path = file_path
                
                ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
                if ext in ['mp4', 'webm', 'mov']:
                    ad.content_type = 'video'
                else:
                    ad.content_type = 'image'
                
                ad.file_size = os.path.getsize(file_path)
        
        duration = request.form.get('duration', '10')
        ad.duration = int(duration) if duration else 10
        
        ad.update_status()
        
        db.session.commit()
        
        flash(f'Contenu publicitaire "{name}" mis à jour avec succès!', 'success')
        return redirect(url_for('ad_content.list_ads'))
    
    return render_template('admin/ad_contents/form.html',
        ad=ad,
        countries=countries,
        organizations=organizations,
        screens=screens,
        cities_by_country=cities_by_country,
        ad_settings=ad_settings
    )


@ad_content_bp.route('/ad-content/<int:ad_id>/toggle', methods=['POST'])
@login_required
@superadmin_required
def toggle(ad_id):
    ad = AdContent.query.get_or_404(ad_id)
    
    if ad.status == AdContent.STATUS_ACTIVE:
        ad.status = AdContent.STATUS_PAUSED
        flash(f'Contenu "{ad.name}" mis en pause.', 'info')
    elif ad.status == AdContent.STATUS_PAUSED:
        ad.status = AdContent.STATUS_ACTIVE
        flash(f'Contenu "{ad.name}" réactivé.', 'success')
    elif ad.status == AdContent.STATUS_SCHEDULED:
        ad.status = AdContent.STATUS_ACTIVE
        flash(f'Contenu "{ad.name}" activé immédiatement.', 'success')
    
    db.session.commit()
    return redirect(url_for('ad_content.list_ads'))


@ad_content_bp.route('/ad-content/<int:ad_id>/delete', methods=['POST'])
@login_required
@superadmin_required
def delete(ad_id):
    ad = AdContent.query.get_or_404(ad_id)
    
    if ad.file_path and os.path.exists(ad.file_path):
        try:
            os.remove(ad.file_path)
        except:
            pass
    
    AdContentStat.query.filter_by(ad_content_id=ad_id).delete()
    AdContentInvoice.query.filter_by(ad_content_id=ad_id).delete()
    
    name = ad.name
    db.session.delete(ad)
    db.session.commit()
    
    flash(f'Contenu "{name}" supprimé.', 'success')
    return redirect(url_for('ad_content.list_ads'))


@ad_content_bp.route('/ad-content/<int:ad_id>/view')
@login_required
@superadmin_required
def view(ad_id):
    ad = AdContent.query.get_or_404(ad_id)
    screens = ad.get_target_screens()
    
    stats_by_screen = db.session.query(
        AdContentStat.screen_id,
        func.sum(AdContentStat.impressions).label('impressions'),
        func.sum(AdContentStat.total_duration).label('duration')
    ).filter(
        AdContentStat.ad_content_id == ad_id
    ).group_by(AdContentStat.screen_id).all()
    
    stats_map = {s.screen_id: {'impressions': s.impressions, 'duration': s.duration} for s in stats_by_screen}
    
    invoices = AdContentInvoice.query.filter_by(ad_content_id=ad_id).order_by(AdContentInvoice.generated_at.desc()).all()
    
    return render_template('admin/ad_contents/view.html',
        ad=ad,
        screens=screens,
        stats_map=stats_map,
        invoices=invoices
    )


@ad_content_bp.route('/ad-content/<int:ad_id>/stats')
@login_required
@superadmin_required
def stats(ad_id):
    ad = AdContent.query.get_or_404(ad_id)
    
    days_back = request.args.get('days', 30, type=int)
    start_date = date.today() - timedelta(days=days_back)
    
    daily_stats = db.session.query(
        AdContentStat.date,
        func.sum(AdContentStat.impressions).label('impressions'),
        func.sum(AdContentStat.total_duration).label('duration')
    ).filter(
        AdContentStat.ad_content_id == ad_id,
        AdContentStat.date >= start_date
    ).group_by(AdContentStat.date).order_by(AdContentStat.date).all()
    
    stats_by_org = db.session.query(
        Organization.id,
        Organization.name,
        func.sum(AdContentStat.impressions).label('impressions'),
        func.sum(AdContentStat.total_duration).label('duration')
    ).join(AdContentStat, AdContentStat.organization_id == Organization.id).filter(
        AdContentStat.ad_content_id == ad_id
    ).group_by(Organization.id, Organization.name).all()
    
    stats_by_screen = db.session.query(
        Screen.id,
        Screen.name,
        Organization.name.label('org_name'),
        func.sum(AdContentStat.impressions).label('impressions'),
        func.sum(AdContentStat.total_duration).label('duration')
    ).join(AdContentStat, AdContentStat.screen_id == Screen.id).join(
        Organization, Screen.organization_id == Organization.id
    ).filter(
        AdContentStat.ad_content_id == ad_id
    ).group_by(Screen.id, Screen.name, Organization.name).all()
    
    return render_template('admin/ad_contents/stats.html',
        ad=ad,
        daily_stats=daily_stats,
        stats_by_org=stats_by_org,
        stats_by_screen=stats_by_screen,
        days_back=days_back
    )


@ad_content_bp.route('/ad-content/invoices')
@login_required
@superadmin_required
def invoices():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    status_filter = request.args.get('status', '')
    
    query = AdContentInvoice.query
    
    if status_filter:
        query = query.filter(AdContentInvoice.status == status_filter)
    
    invoices = query.order_by(AdContentInvoice.generated_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    pending_count = AdContentInvoice.query.filter_by(status=AdContentInvoice.STATUS_PENDING).count()
    paid_count = AdContentInvoice.query.filter_by(status=AdContentInvoice.STATUS_PAID).count()
    
    total_pending = db.session.query(func.sum(AdContentInvoice.commission_amount)).filter(
        AdContentInvoice.status == AdContentInvoice.STATUS_PENDING
    ).scalar() or 0
    
    return render_template('admin/ad_contents/invoices.html',
        invoices=invoices,
        status_filter=status_filter,
        pending_count=pending_count,
        paid_count=paid_count,
        total_pending=total_pending
    )


@ad_content_bp.route('/ad-content/invoice/<int:invoice_id>/validate', methods=['POST'])
@login_required
@superadmin_required
def validate_invoice(invoice_id):
    invoice = AdContentInvoice.query.get_or_404(invoice_id)
    
    invoice.status = AdContentInvoice.STATUS_VALIDATED
    invoice.validated_at = datetime.utcnow()
    invoice.validated_by = current_user.id
    
    db.session.commit()
    
    flash(f'Facture {invoice.invoice_number} validée.', 'success')
    return redirect(url_for('ad_content.invoices'))


@ad_content_bp.route('/ad-content/invoice/<int:invoice_id>/mark-paid', methods=['POST'])
@login_required
@superadmin_required
def mark_invoice_paid(invoice_id):
    invoice = AdContentInvoice.query.get_or_404(invoice_id)
    
    invoice.status = AdContentInvoice.STATUS_PAID
    invoice.paid_at = datetime.utcnow()
    
    db.session.commit()
    
    flash(f'Facture {invoice.invoice_number} marquée comme payée.', 'success')
    return redirect(url_for('ad_content.invoices'))


@ad_content_bp.route('/ad-content/<int:ad_id>/generate-invoices', methods=['POST'])
@login_required
@superadmin_required
def generate_invoices(ad_id):
    ad = AdContent.query.get_or_404(ad_id)
    
    if ad.status not in [AdContent.STATUS_ACTIVE, AdContent.STATUS_EXPIRED]:
        flash('Les factures ne peuvent être générées que pour les contenus actifs ou expirés.', 'error')
        return redirect(url_for('ad_content.view', ad_id=ad_id))
    
    screens = ad.get_target_screens()
    if not screens:
        flash('Aucun écran ciblé par ce contenu.', 'error')
        return redirect(url_for('ad_content.view', ad_id=ad_id))
    
    orgs = {}
    for screen in screens:
        if screen.organization_id not in orgs:
            orgs[screen.organization_id] = {
                'org': screen.organization,
                'screens': [],
                'impressions': 0,
                'duration': 0
            }
        orgs[screen.organization_id]['screens'].append(screen)
        
        stats = AdContentStat.query.filter_by(
            ad_content_id=ad_id,
            screen_id=screen.id
        ).all()
        for stat in stats:
            orgs[screen.organization_id]['impressions'] += stat.impressions
            orgs[screen.organization_id]['duration'] += stat.total_duration
    
    total_screens = len(screens)
    invoices_created = 0
    
    for org_id, data in orgs.items():
        existing = AdContentInvoice.query.filter_by(
            ad_content_id=ad_id,
            organization_id=org_id
        ).first()
        if existing:
            continue
        
        org_share = len(data['screens']) / total_screens if total_screens > 0 else 0
        gross_amount = ad.total_price * org_share
        commission_amount = gross_amount * (ad.commission_rate / 100)
        
        invoice = AdContentInvoice(
            organization_id=org_id,
            ad_content_id=ad_id,
            period_start=ad.start_date.date() if ad.start_date else date.today(),
            period_end=ad.end_date.date() if ad.end_date else date.today(),
            screens_count=len(data['screens']),
            total_impressions=data['impressions'],
            total_duration=data['duration'],
            gross_amount=gross_amount,
            commission_rate=ad.commission_rate,
            commission_amount=commission_amount,
            currency=ad.currency
        )
        invoice.generate_invoice_number()
        
        db.session.add(invoice)
        invoices_created += 1
    
    db.session.commit()
    
    if invoices_created > 0:
        flash(f'{invoices_created} facture(s) générée(s) avec succès.', 'success')
    else:
        flash('Aucune nouvelle facture à générer.', 'info')
    
    return redirect(url_for('ad_content.view', ad_id=ad_id))


@ad_content_bp.route('/ad-content/settings', methods=['GET', 'POST'])
@login_required
@superadmin_required
def settings():
    if request.method == 'POST':
        settings_data = {
            'ad_commission_rate': float(request.form.get('ad_commission_rate', 30)),
            'ad_min_price_per_day': float(request.form.get('ad_min_price_per_day', 10)),
            'ad_auto_invoice': 'ad_auto_invoice' in request.form,
            'ad_invoice_frequency': request.form.get('ad_invoice_frequency', 'monthly')
        }
        SiteSetting.set_ad_content_settings(settings_data)
        
        flash('Paramètres de contenu publicitaire mis à jour.', 'success')
        return redirect(url_for('ad_content.settings'))
    
    settings = SiteSetting.get_ad_content_settings()
    return render_template('admin/ad_contents/settings.html', settings=settings)


@ad_content_bp.route('/ad-content/global-stats')
@login_required
@superadmin_required
def global_stats():
    from datetime import timedelta
    
    days_back = request.args.get('days', 30, type=int)
    start_date = date.today() - timedelta(days=days_back)
    
    total_ads = AdContent.query.count()
    active_ads = AdContent.query.filter_by(status=AdContent.STATUS_ACTIVE).count()
    total_revenue = db.session.query(func.sum(AdContent.total_price)).scalar() or 0
    total_impressions = db.session.query(func.sum(AdContent.total_impressions)).scalar() or 0
    
    daily_stats = db.session.query(
        AdContentStat.date,
        func.sum(AdContentStat.impressions).label('impressions'),
        func.sum(AdContentStat.total_duration).label('duration'),
        func.count(func.distinct(AdContentStat.ad_content_id)).label('ads_count')
    ).filter(
        AdContentStat.date >= start_date
    ).group_by(AdContentStat.date).order_by(AdContentStat.date).all()
    
    revenue_by_country = db.session.query(
        AdContent.target_country,
        func.sum(AdContent.total_price).label('revenue'),
        func.count(AdContent.id).label('count')
    ).filter(
        AdContent.target_type == AdContent.TARGET_COUNTRY
    ).group_by(AdContent.target_country).all()
    
    top_orgs = db.session.query(
        Organization.id,
        Organization.name,
        func.sum(AdContentStat.impressions).label('impressions'),
        func.sum(AdContentStat.total_duration).label('duration')
    ).join(AdContentStat, AdContentStat.organization_id == Organization.id).group_by(
        Organization.id, Organization.name
    ).order_by(func.sum(AdContentStat.impressions).desc()).limit(10).all()
    
    return render_template('admin/ad_contents/global_stats.html',
        total_ads=total_ads,
        active_ads=active_ads,
        total_revenue=total_revenue,
        total_impressions=total_impressions,
        daily_stats=daily_stats,
        revenue_by_country=revenue_by_country,
        top_orgs=top_orgs,
        days_back=days_back
    )


@ad_content_bp.route('/ad-content/calculate-screens', methods=['POST'])
@login_required
@superadmin_required
def calculate_available_screens():
    """
    Calculate available screens based on targeting criteria, dates, and minimum plays.
    This implements mass targeting logic for superadmin ad content creation.
    """
    data = request.get_json()
    
    target_type = data.get('target_type', 'country')
    target_country = data.get('target_country', 'FR')
    target_city = data.get('target_city', '')
    target_organization_id = data.get('target_organization_id')
    target_screen_id = data.get('target_screen_id')
    target_org_type = data.get('target_org_type', 'all')
    
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    slot_duration = int(data.get('slot_duration', 10))
    content_type = data.get('content_type', 'image')
    min_plays = int(data.get('min_plays', 10))
    
    if not start_date or not end_date:
        return jsonify({'error': 'Dates de debut et de fin requises'}), 400
    
    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Format de date invalide'}), 400
    
    num_days = (end_dt - start_dt).days + 1
    if num_days <= 0:
        return jsonify({'error': 'La date de fin doit etre apres la date de debut'}), 400
    
    query = Screen.query.filter_by(is_active=True).join(Organization).filter(Organization.is_active == True)
    
    if target_org_type == 'paid':
        query = query.filter(Organization.is_paid == True)
    elif target_org_type == 'free':
        query = query.filter(Organization.is_paid == False)
    
    if target_type == 'country':
        query = query.filter(Organization.country == target_country)
    elif target_type == 'city':
        query = query.filter(
            Organization.country == target_country,
            Organization.city == target_city
        )
    elif target_type == 'organization':
        if target_organization_id:
            query = query.filter(Screen.organization_id == int(target_organization_id))
    elif target_type == 'screen':
        if target_screen_id:
            query = query.filter(Screen.id == int(target_screen_id))
    
    all_screens = query.all()
    
    available_screens = []
    total_available_plays = 0
    
    for screen in all_screens:
        if content_type == 'image' and not screen.accepts_images:
            continue
        if content_type == 'video' and not screen.accepts_videos:
            continue
        
        availability = calculate_availability(
            screen, start_date, end_date, None, slot_duration, content_type
        )
        
        screen_available_plays = availability['available_plays']
        
        if screen_available_plays >= min_plays:
            org = screen.organization
            org_currency = org.currency if org and org.currency else 'EUR'
            currency_info = get_currency_by_code(org_currency)
            
            slot = TimeSlot.query.filter_by(
                screen_id=screen.id,
                content_type=content_type,
                duration_seconds=slot_duration
            ).first()
            
            price_per_play = slot.price_per_play if slot else 0.0
            estimated_price = price_per_play * min_plays
            
            available_screens.append({
                'id': screen.id,
                'name': screen.name,
                'location': screen.location or '',
                'organization_id': screen.organization_id,
                'organization_name': org.name if org else 'N/A',
                'organization_city': org.city if org else '',
                'organization_country': org.country if org else '',
                'resolution': f"{screen.resolution_width}x{screen.resolution_height}",
                'orientation': screen.orientation,
                'available_plays': screen_available_plays,
                'price_per_play': round(price_per_play, 2),
                'estimated_price': round(estimated_price, 2),
                'currency': org_currency,
                'currency_symbol': currency_info.get('symbol', org_currency),
                'accepts_images': screen.accepts_images,
                'accepts_videos': screen.accepts_videos,
                'periods': [
                    {
                        'id': p.id,
                        'name': p.name,
                        'start_hour': p.start_hour,
                        'end_hour': p.end_hour,
                        'price_multiplier': p.price_multiplier
                    } for p in screen.time_periods
                ]
            })
            total_available_plays += screen_available_plays
    
    return jsonify({
        'screens': available_screens,
        'total_screens': len(available_screens),
        'total_available_plays': total_available_plays,
        'num_days': num_days,
        'min_plays_requested': min_plays
    })


@ad_content_bp.route('/ad-content/calculate-price', methods=['POST'])
@login_required
@superadmin_required
def calculate_ad_price():
    """
    Calculate price for a set of screens based on number of plays.
    """
    data = request.get_json()
    
    screen_ids = data.get('screen_ids', [])
    num_plays = int(data.get('num_plays', 10))
    slot_duration = int(data.get('slot_duration', 10))
    content_type = data.get('content_type', 'image')
    commission_rate = float(data.get('commission_rate', 30))
    
    if not screen_ids:
        return jsonify({'error': 'Aucun ecran selectionne'}), 400
    
    screens = Screen.query.filter(Screen.id.in_(screen_ids)).all()
    
    total_price = 0
    screen_prices = []
    
    for screen in screens:
        org = screen.organization
        org_currency = org.currency if org and org.currency else 'EUR'
        
        slot = TimeSlot.query.filter_by(
            screen_id=screen.id,
            content_type=content_type,
            duration_seconds=slot_duration
        ).first()
        
        price_per_play = slot.price_per_play if slot else 0.0
        screen_total = price_per_play * num_plays
        
        screen_prices.append({
            'screen_id': screen.id,
            'screen_name': screen.name,
            'organization_name': org.name if org else 'N/A',
            'price_per_play': round(price_per_play, 2),
            'total_price': round(screen_total, 2),
            'currency': org_currency
        })
        
        total_price += screen_total
    
    commission_amount = total_price * (commission_rate / 100)
    net_revenue = total_price - commission_amount
    
    return jsonify({
        'screens': screen_prices,
        'num_screens': len(screens),
        'num_plays_per_screen': num_plays,
        'total_plays': num_plays * len(screens),
        'total_price': round(total_price, 2),
        'commission_rate': commission_rate,
        'commission_amount': round(commission_amount, 2),
        'net_revenue': round(net_revenue, 2)
    })


@ad_content_bp.route('/ad-content/get-periods/<int:screen_id>')
@login_required
@superadmin_required
def get_screen_periods(screen_id):
    """Get time periods for a specific screen."""
    screen = Screen.query.get_or_404(screen_id)
    
    periods = [
        {
            'id': p.id,
            'name': p.name,
            'start_hour': p.start_hour,
            'end_hour': p.end_hour,
            'price_multiplier': p.price_multiplier
        }
        for p in screen.time_periods
    ]
    
    return jsonify({'periods': periods})
