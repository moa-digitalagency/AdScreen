from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, make_response
from flask_login import login_required, current_user
from functools import wraps
from app import db
from models import Screen, Booking, Organization, Invoice, PaymentProof, User
from models.site_setting import SiteSetting
from services.translation_service import t
from datetime import datetime, timedelta, date
from sqlalchemy import func, and_
import os
import secrets
from werkzeug.utils import secure_filename
import io
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

billing_bp = Blueprint('billing', __name__)

UPLOAD_FOLDER = 'static/uploads/payment_proofs'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def org_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.is_superadmin():
            return redirect(url_for('admin.dashboard'))
        if not current_user.organization_id:
            flash(t('flash.org_required'), 'error')
            return redirect(url_for('auth.logout'))
        return f(*args, **kwargs)
    return decorated_function


def paid_org_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.is_superadmin():
            return redirect(url_for('admin.dashboard'))
        if not current_user.organization_id:
            flash(t('flash.org_required'), 'error')
            return redirect(url_for('auth.logout'))
        org = current_user.organization
        if not org.is_paid:
            flash(t('flash.billing_not_available_free'), 'error')
            return redirect(url_for('org.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def get_week_dates(reference_date=None):
    """Get the start and end dates for the week containing the reference date."""
    if reference_date is None:
        reference_date = datetime.utcnow().date()
    
    start_of_week = reference_date - timedelta(days=reference_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    return start_of_week, end_of_week


def get_previous_weeks(count=12):
    """Get the previous N weeks as (start_date, end_date) tuples."""
    weeks = []
    today = datetime.utcnow().date()
    
    current_week_start = today - timedelta(days=today.weekday())
    
    for i in range(1, count + 1):
        week_start = current_week_start - timedelta(weeks=i)
        week_end = week_start + timedelta(days=6)
        weeks.append((week_start, week_end))
    
    return weeks


def get_last_week():
    """Get the previous week (Monday to Sunday) as (start_date, end_date) tuple."""
    today = datetime.utcnow().date()
    current_week_start = today - timedelta(days=today.weekday())
    last_week_start = current_week_start - timedelta(weeks=1)
    last_week_end = last_week_start + timedelta(days=6)
    return last_week_start, last_week_end


def is_invoice_generation_time():
    """
    Check if it's time to generate invoices (Sunday 23:00-23:59 in platform timezone).
    Returns True if we should generate invoices for the previous week.
    """
    platform_timezone = SiteSetting.get('platform_timezone', 'UTC')
    try:
        tz = ZoneInfo(platform_timezone)
    except Exception:
        tz = ZoneInfo('UTC')
    
    now = datetime.now(tz)
    is_sunday = now.weekday() == 6
    is_late_night = now.hour == 23
    
    return is_sunday and is_late_night


def should_generate_weekly_invoice():
    """
    Determine if weekly invoice generation should happen.
    Returns (should_generate, week_start, week_end)
    """
    if not is_invoice_generation_time():
        return False, None, None
    
    last_week_start, last_week_end = get_last_week()
    return True, last_week_start, last_week_end


def run_scheduled_invoice_generation():
    """
    Generate invoices for all organizations for the previous week.
    This should be called by a scheduled task (cron) on Sundays at 23:59.
    Returns the number of invoices generated.
    """
    if not is_invoice_generation_time():
        return 0, "Not invoice generation time"
    
    last_week_start, last_week_end = get_last_week()
    all_orgs = Organization.query.filter_by(is_active=True).all()
    
    generated_count = 0
    for org in all_orgs:
        existing = Invoice.query.filter_by(
            organization_id=org.id,
            week_start_date=last_week_start,
            week_end_date=last_week_end
        ).first()
        if not existing:
            invoice = generate_invoice_for_week(org.id, last_week_start, last_week_end)
            if invoice:
                generated_count += 1
    
    return generated_count, f"Generated {generated_count} invoices for week {last_week_start} to {last_week_end}"


def generate_invoice_for_week(organization_id, week_start, week_end):
    """
    Generate an invoice for a specific week for an organization.
    - Only generates if gross_revenue > 0
    - One invoice per organization (all screens combined)
    - Updates existing invoice if not validated
    """
    from models import SiteSetting
    
    org = Organization.query.get(organization_id)
    if not org:
        return None
    
    existing_invoice = Invoice.query.filter_by(
        organization_id=organization_id,
        week_start_date=week_start,
        week_end_date=week_end
    ).first()
    
    screen_ids = [s.id for s in org.screens]
    
    if not screen_ids:
        gross_revenue = 0
        bookings_count = 0
    else:
        gross_revenue = db.session.query(func.sum(Booking.total_price)).filter(
            Booking.screen_id.in_(screen_ids),
            Booking.payment_status == 'paid',
            Booking.created_at >= datetime.combine(week_start, datetime.min.time()),
            Booking.created_at <= datetime.combine(week_end, datetime.max.time())
        ).scalar() or 0
        
        bookings_count = db.session.query(func.count(Booking.id)).filter(
            Booking.screen_id.in_(screen_ids),
            Booking.payment_status == 'paid',
            Booking.created_at >= datetime.combine(week_start, datetime.min.time()),
            Booking.created_at <= datetime.combine(week_end, datetime.max.time())
        ).scalar() or 0
    
    if gross_revenue <= 0 and not existing_invoice:
        return None
    
    commission_rate = org.commission_rate or 10.0
    commission_amount = round(gross_revenue * (commission_rate / 100), 2)
    net_revenue = round(gross_revenue - commission_amount, 2)
    
    platform_vat_rate = SiteSetting.get('platform_vat_rate', 0) or 0
    vat_amount = round(commission_amount * (platform_vat_rate / 100), 2) if platform_vat_rate > 0 else 0
    commission_with_vat = round(commission_amount + vat_amount, 2)
    
    platform_business_name = SiteSetting.get('platform_business_name', '')
    platform_vat_number = SiteSetting.get('platform_vat_number', '')
    platform_registration_number = SiteSetting.get('platform_registration_number', '')
    
    if existing_invoice:
        if existing_invoice.status not in [Invoice.STATUS_VALIDATED]:
            existing_invoice.gross_revenue = gross_revenue
            existing_invoice.commission_rate = commission_rate
            existing_invoice.commission_amount = commission_amount
            existing_invoice.net_revenue = net_revenue
            existing_invoice.bookings_count = bookings_count
            existing_invoice.vat_rate = platform_vat_rate
            existing_invoice.vat_amount = vat_amount
            existing_invoice.commission_with_vat = commission_with_vat
            existing_invoice.platform_business_name = platform_business_name
            existing_invoice.platform_vat_number = platform_vat_number
            existing_invoice.platform_registration_number = platform_registration_number
            existing_invoice.generated_at = datetime.utcnow()
            db.session.commit()
        return existing_invoice
    else:
        invoice = Invoice(
            organization_id=organization_id,
            week_start_date=week_start,
            week_end_date=week_end,
            gross_revenue=gross_revenue,
            commission_rate=commission_rate,
            commission_amount=commission_amount,
            net_revenue=net_revenue,
            currency=org.currency or 'EUR',
            bookings_count=bookings_count,
            vat_rate=platform_vat_rate,
            vat_amount=vat_amount,
            commission_with_vat=commission_with_vat,
            platform_business_name=platform_business_name,
            platform_vat_number=platform_vat_number,
            platform_registration_number=platform_registration_number
        )
        invoice.generate_invoice_number()
        db.session.add(invoice)
        db.session.commit()
        return invoice


@billing_bp.route('/invoices')
@login_required
@paid_org_required
def invoices():
    from utils.currencies import get_currency_by_code
    
    org = current_user.organization
    
    should_generate, week_start, week_end = should_generate_weekly_invoice()
    if should_generate:
        existing = Invoice.query.filter_by(
            organization_id=org.id,
            week_start_date=week_start,
            week_end_date=week_end
        ).first()
        if not existing:
            generate_invoice_for_week(org.id, week_start, week_end)
    
    status_filter = request.args.get('status', 'all')
    
    query = Invoice.query.filter_by(organization_id=org.id)
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    invoices = query.order_by(Invoice.week_start_date.desc()).all()
    
    total_pending = sum(i.commission_amount for i in invoices if i.status == Invoice.STATUS_PENDING)
    total_paid = sum(i.commission_amount for i in invoices if i.status in [Invoice.STATUS_PAID, Invoice.STATUS_VALIDATED])
    total_validated = sum(i.commission_amount for i in invoices if i.status == Invoice.STATUS_VALIDATED)
    
    currency_info = get_currency_by_code(org.currency or 'EUR')
    currency_symbol = currency_info.get('symbol', org.currency or 'EUR')
    
    return render_template('org/billing/invoices.html',
        org=org,
        invoices=invoices,
        status_filter=status_filter,
        total_pending=total_pending,
        total_paid=total_paid,
        total_validated=total_validated,
        currency_symbol=currency_symbol
    )


@billing_bp.route('/invoice/<int:invoice_id>')
@login_required
@paid_org_required
def invoice_detail(invoice_id):
    from utils.currencies import get_currency_by_code
    
    org = current_user.organization
    
    invoice = Invoice.query.filter_by(
        id=invoice_id,
        organization_id=org.id
    ).first_or_404()
    
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
    
    return render_template('org/billing/invoice_detail.html',
        org=org,
        invoice=invoice,
        bookings=bookings,
        currency_symbol=currency_symbol
    )


@billing_bp.route('/invoice/<int:invoice_id>/regenerate', methods=['POST'])
@login_required
@paid_org_required
def regenerate_invoice(invoice_id):
    org = current_user.organization
    
    invoice = Invoice.query.filter_by(
        id=invoice_id,
        organization_id=org.id
    ).first_or_404()
    
    if invoice.status == Invoice.STATUS_VALIDATED:
        flash(t('flash.invoice_validated_readonly'), 'error')
        return redirect(url_for('billing.invoice_detail', invoice_id=invoice_id))
    
    generate_invoice_for_week(org.id, invoice.week_start_date, invoice.week_end_date)
    
    flash(t('flash.invoice_regenerated'), 'success')
    return redirect(url_for('billing.invoice_detail', invoice_id=invoice_id))


@billing_bp.route('/invoice/<int:invoice_id>/upload_proof', methods=['POST'])
@login_required
@paid_org_required
def upload_payment_proof(invoice_id):
    org = current_user.organization
    
    invoice = Invoice.query.filter_by(
        id=invoice_id,
        organization_id=org.id
    ).first_or_404()
    
    if invoice.status == Invoice.STATUS_VALIDATED:
        flash(t('flash.invoice_already_validated'), 'error')
        return redirect(url_for('billing.invoice_detail', invoice_id=invoice_id))
    
    if 'proof_file' not in request.files:
        flash(t('flash.no_file_selected'), 'error')
        return redirect(url_for('billing.invoice_detail', invoice_id=invoice_id))
    
    file = request.files['proof_file']
    notes = request.form.get('notes', '')
    
    if file.filename == '':
        flash(t('flash.no_file_selected'), 'error')
        return redirect(url_for('billing.invoice_detail', invoice_id=invoice_id))
    
    if not allowed_file(file.filename):
        flash(t('flash.file_type_not_allowed'), 'error')
        return redirect(url_for('billing.invoice_detail', invoice_id=invoice_id))
    
    filename = secure_filename(file.filename)
    unique_filename = f"{secrets.token_hex(8)}_{filename}"
    
    upload_path = os.path.join(UPLOAD_FOLDER, str(org.id))
    os.makedirs(upload_path, exist_ok=True)
    
    file_path = os.path.join(upload_path, unique_filename)
    file.save(file_path)
    
    file_size = os.path.getsize(file_path)
    
    proof = PaymentProof(
        invoice_id=invoice.id,
        file_path=file_path,
        file_name=filename,
        file_size=file_size,
        notes=notes,
        uploaded_by=current_user.id
    )
    db.session.add(proof)
    
    invoice.status = Invoice.STATUS_PAID
    invoice.paid_at = datetime.utcnow()
    
    db.session.commit()
    
    flash(t('flash.payment_proof_uploaded'), 'success')
    return redirect(url_for('billing.invoice_detail', invoice_id=invoice_id))


@billing_bp.route('/invoice/<int:invoice_id>/download')
@login_required
@paid_org_required
def download_invoice(invoice_id):
    from utils.currencies import get_currency_by_code
    
    org = current_user.organization
    
    invoice = Invoice.query.filter_by(
        id=invoice_id,
        organization_id=org.id
    ).first_or_404()
    
    currency_info = get_currency_by_code(org.currency or 'EUR')
    currency_symbol = currency_info.get('symbol', org.currency or 'EUR')
    
    screen_ids = [s.id for s in org.screens]
    bookings = []
    if screen_ids:
        bookings = Booking.query.filter(
            Booking.screen_id.in_(screen_ids),
            Booking.payment_status == 'paid',
            Booking.created_at >= datetime.combine(invoice.week_start_date, datetime.min.time()),
            Booking.created_at <= datetime.combine(invoice.week_end_date, datetime.max.time())
        ).order_by(Booking.created_at.desc()).all()
    
    html_content = render_template('org/billing/invoice_pdf.html',
        org=org,
        invoice=invoice,
        bookings=bookings,
        currency_symbol=currency_symbol
    )
    
    response = make_response(html_content)
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename=facture_{invoice.invoice_number}.html'
    
    return response


@billing_bp.route('/cron/generate-invoices', methods=['POST'])
def cron_generate_invoices():
    """
    Cron endpoint to trigger scheduled invoice generation.
    Should be called by an external scheduler on Sundays at 23:59 (platform timezone).
    Requires a valid cron secret for authentication.
    """
    import os
    cron_secret = request.headers.get('X-Cron-Secret', '')
    expected_secret = os.environ.get('CRON_SECRET', '')
    
    if not expected_secret or cron_secret != expected_secret:
        return {'error': 'Unauthorized'}, 401
    
    count, message = run_scheduled_invoice_generation()
    
    return {
        'success': True,
        'invoices_generated': count,
        'message': message
    }, 200
