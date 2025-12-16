from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from app import db
from models import Screen, TimeSlot, TimePeriod, Content, Booking
from services.translation_service import t
from datetime import datetime, date, time
import os
import secrets
import base64
import io
from werkzeug.utils import secure_filename
from utils.image_utils import validate_image
from utils.video_utils import validate_video, get_video_duration
from services.qr_service import generate_qr_base64
from services.receipt_generator import generate_receipt_image
from services.availability_service import calculate_availability, calculate_plays_for_dates, calculate_equitable_distribution
from utils.currencies import get_currency_by_code

booking_bp = Blueprint('booking', __name__)

ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'mov'}


def allowed_file(filename, content_type):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if content_type == 'image':
        return ext in ALLOWED_IMAGE_EXTENSIONS
    elif content_type == 'video':
        return ext in ALLOWED_VIDEO_EXTENSIONS
    return False


@booking_bp.route('/<screen_code>')
def screen_booking(screen_code):
    screen = Screen.query.filter_by(unique_code=screen_code, is_active=True).first_or_404()
    
    if not screen.organization.is_active:
        return render_template('booking/unavailable.html')
    
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
    
    slots_json = [
        {
            'id': slot.id,
            'content_type': slot.content_type,
            'duration_seconds': slot.duration_seconds,
            'price_per_play': float(slot.price_per_play)
        }
        for slot in screen.time_slots
    ]
    
    org_currency = screen.organization.currency if screen.organization else 'EUR'
    currency_info = get_currency_by_code(org_currency)
    currency_symbol = currency_info.get('symbol', org_currency)
    
    return render_template('booking/screen.html',
        screen=screen,
        current_period=current_period,
        slots_json=slots_json,
        currency_symbol=currency_symbol,
        currency_code=org_currency,
        price_per_minute=screen.price_per_minute or 2.0
    )


@booking_bp.route('/<screen_code>/submit', methods=['POST'])
def submit_booking(screen_code):
    screen = Screen.query.filter_by(unique_code=screen_code, is_active=True).first_or_404()
    
    client_name = request.form.get('client_name')
    client_email = request.form.get('client_email')
    client_phone = request.form.get('client_phone')
    content_type = request.form.get('content_type')
    slot_duration = int(request.form.get('slot_duration', 10))
    period_id = request.form.get('period_id')
    booking_mode = request.form.get('booking_mode', 'plays')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    start_time_str = request.form.get('start_time')
    end_time_str = request.form.get('end_time')
    
    if booking_mode == 'dates':
        calculated_plays = int(request.form.get('calculated_plays', 10))
        num_plays = calculated_plays
    else:
        num_plays = int(request.form.get('num_plays', 10))
        calculated_plays = None
    
    if 'file' not in request.files:
        flash(t('flash.select_file'), 'error')
        return redirect(url_for('booking.screen_booking', screen_code=screen_code))
    
    file = request.files['file']
    
    if not file.filename:
        flash(t('flash.select_file'), 'error')
        return redirect(url_for('booking.screen_booking', screen_code=screen_code))
    
    if not allowed_file(file.filename, content_type):
        flash(t('flash.file_format_not_supported'), 'error')
        return redirect(url_for('booking.screen_booking', screen_code=screen_code))
    
    slot = TimeSlot.query.filter_by(
        screen_id=screen.id,
        content_type=content_type,
        duration_seconds=slot_duration
    ).first()
    
    if not slot:
        flash(t('flash.slot_not_available'), 'error')
        return redirect(url_for('booking.screen_booking', screen_code=screen_code))
    
    period = TimePeriod.query.get(period_id) if period_id else None
    multiplier = period.price_multiplier if period else 1.0
    
    price_per_play = slot.price_per_play * multiplier
    total_price = price_per_play * num_plays
    
    filename = secure_filename(file.filename)
    new_filename = f"{secrets.token_hex(8)}_{filename}"
    upload_path = os.path.join('static', 'uploads', 'content', str(screen.id))
    os.makedirs(upload_path, exist_ok=True)
    file_path = os.path.join(upload_path, new_filename)
    file.save(file_path)
    
    width, height, duration = None, None, None
    validation_error = None
    
    if content_type == 'image':
        valid, width, height, error = validate_image(
            file_path,
            screen.resolution_width,
            screen.resolution_height
        )
        if not valid:
            os.remove(file_path)
            flash(t('flash.image_invalid', error=error), 'error')
            return redirect(url_for('booking.screen_booking', screen_code=screen_code))
    else:
        valid, width, height, duration, error = validate_video(
            file_path,
            screen.resolution_width,
            screen.resolution_height,
            slot_duration
        )
        if not valid:
            os.remove(file_path)
            flash(t('flash.video_invalid', error=error), 'error')
            return redirect(url_for('booking.screen_booking', screen_code=screen_code))
    
    content = Content(
        screen_id=screen.id,
        filename=new_filename,
        original_filename=filename,
        content_type=content_type,
        file_path=file_path,
        file_size=os.path.getsize(file_path),
        width=width,
        height=height,
        duration_seconds=duration if content_type == 'video' else slot_duration,
        status='pending',
        client_name=client_name,
        client_email=client_email,
        client_phone=client_phone
    )
    db.session.add(content)
    db.session.flush()
    
    start_time_parsed = None
    end_time_parsed = None
    if start_time_str:
        try:
            parts = start_time_str.split(':')
            start_time_parsed = time(int(parts[0]), int(parts[1]))
        except (ValueError, IndexError):
            pass
    if end_time_str:
        try:
            parts = end_time_str.split(':')
            end_time_parsed = time(int(parts[0]), int(parts[1]))
        except (ValueError, IndexError):
            pass
    
    org = screen.organization
    vat_rate = org.vat_rate if org and org.vat_rate else 0
    vat_amount = round(total_price * (vat_rate / 100), 2) if vat_rate > 0 else 0
    total_price_with_vat = round(total_price + vat_amount, 2)
    
    booking = Booking(
        screen_id=screen.id,
        content_id=content.id,
        booking_mode=booking_mode,
        slot_duration=slot_duration,
        time_period_id=period.id if period else None,
        num_plays=num_plays,
        calculated_plays=calculated_plays,
        price_per_play=price_per_play,
        total_price=total_price,
        vat_rate=vat_rate,
        vat_amount=vat_amount,
        total_price_with_vat=total_price_with_vat,
        start_date=datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else date.today(),
        end_date=datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None,
        start_time=start_time_parsed,
        end_time=end_time_parsed,
        status='pending',
        payment_status='paid'
    )
    db.session.add(booking)
    db.session.flush()
    
    booking.generate_reservation_number()
    db.session.commit()
    
    reservation_qr = generate_qr_base64(booking.reservation_number, box_size=6, border=2)
    
    screen_booking_url = url_for('booking.screen_booking', screen_code=screen.unique_code, _external=True)
    screen_qr = generate_qr_base64(screen_booking_url, box_size=6, border=2)
    
    org_currency = screen.organization.currency if hasattr(screen.organization, 'currency') and screen.organization.currency else 'EUR'
    currency_info = get_currency_by_code(org_currency)
    currency_symbol = currency_info.get('symbol', org_currency)
    
    return render_template('booking/success.html',
        booking=booking,
        screen=screen,
        content=content,
        reservation_qr=reservation_qr,
        booking_qr=screen_qr,
        currency_symbol=currency_symbol
    )


@booking_bp.route('/<screen_code>/calculate', methods=['POST'])
def calculate_price(screen_code):
    screen = Screen.query.filter_by(unique_code=screen_code, is_active=True).first_or_404()
    
    data = request.get_json()
    content_type = data.get('content_type')
    slot_duration = int(data.get('slot_duration', 10))
    period_id = data.get('period_id')
    num_plays = int(data.get('num_plays', 10))
    
    slot = TimeSlot.query.filter_by(
        screen_id=screen.id,
        content_type=content_type,
        duration_seconds=slot_duration
    ).first()
    
    if not slot:
        return jsonify({'error': 'Créneau non disponible'}), 400
    
    period = TimePeriod.query.get(period_id) if period_id else None
    multiplier = period.price_multiplier if period else 1.0
    
    price_per_play = slot.price_per_play * multiplier
    total_price = price_per_play * num_plays
    
    org = screen.organization
    vat_rate = org.vat_rate if org and org.vat_rate else 0
    vat_amount = round(total_price * (vat_rate / 100), 2) if vat_rate > 0 else 0
    total_price_with_vat = round(total_price + vat_amount, 2)
    
    return jsonify({
        'price_per_play': round(price_per_play, 2),
        'total_price': round(total_price, 2),
        'vat_rate': vat_rate,
        'vat_amount': vat_amount,
        'total_price_with_vat': total_price_with_vat,
        'num_plays': num_plays
    })


@booking_bp.route('/status/<int:booking_id>')
def booking_status(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    return render_template('booking/status.html', booking=booking)


@booking_bp.route('/receipt/<reservation_number>')
def download_receipt(reservation_number):
    booking = Booking.query.filter_by(reservation_number=reservation_number).first_or_404()
    
    booking_qr = generate_qr_base64(
        url_for('booking.screen_booking', screen_code=booking.screen.unique_code, _external=True),
        box_size=6, border=2
    )
    
    img = generate_receipt_image(booking, booking.screen, booking.content, booking_qr)
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    response = send_file(
        buffer,
        mimetype='image/png',
        as_attachment=True,
        download_name=f'recu_{reservation_number}.png'
    )
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@booking_bp.route('/<screen_code>/availability', methods=['POST'])
def get_availability(screen_code):
    """
    Calculate availability for a screen based on date range and options.
    This implements the reservation algorithm for showing available slots.
    """
    screen = Screen.query.filter_by(unique_code=screen_code, is_active=True).first_or_404()
    
    data = request.get_json()
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    period_id = data.get('period_id')
    slot_duration = data.get('slot_duration')
    content_type = data.get('content_type', 'image')
    
    if not start_date or not end_date:
        return jsonify({'error': 'Dates de debut et de fin requises'}), 400
    
    try:
        if slot_duration:
            slot_duration = int(slot_duration)
    except (ValueError, TypeError):
        slot_duration = None
    
    try:
        if period_id:
            period_id = int(period_id)
    except (ValueError, TypeError):
        period_id = None
    
    availability = calculate_availability(
        screen, start_date, end_date, period_id, slot_duration, content_type
    )
    
    distribution = calculate_equitable_distribution(
        availability['available_plays'],
        start_date,
        end_date,
        period_id
    )
    
    slot = None
    if slot_duration:
        slot = TimeSlot.query.filter_by(
            screen_id=screen.id,
            content_type=content_type,
            duration_seconds=slot_duration
        ).first()
    
    period = TimePeriod.query.get(period_id) if period_id else None
    multiplier = period.price_multiplier if period else 1.0
    
    price_per_play = (slot.price_per_play * multiplier) if slot else 0
    
    return jsonify({
        'availability': {
            'total_available_seconds': availability['total_available_seconds'],
            'available_plays': availability['available_plays'],
            'slot_duration': availability.get('slot_duration', slot_duration),
            'num_days': availability['num_days'],
            'periods': availability['periods']
        },
        'distribution': distribution,
        'price_per_play': round(price_per_play, 2),
        'recommended_plays': min(availability['available_plays'], max(10, availability['available_plays'] // 10))
    })


@booking_bp.route('/<screen_code>/calculate-dates', methods=['POST'])
def calculate_from_dates(screen_code):
    """
    Calculate the number of plays and cost for a date range.
    Implements the algorithm for the 'dates' booking mode.
    """
    screen = Screen.query.filter_by(unique_code=screen_code, is_active=True).first_or_404()
    
    data = request.get_json()
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    period_id = data.get('period_id')
    slot_duration = int(data.get('slot_duration', 10))
    content_type = data.get('content_type', 'image')
    plays_per_day = int(data.get('plays_per_day', 20))
    
    if not start_date or not end_date:
        return jsonify({'error': 'Dates requises'}), 400
    
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Format de date invalide'}), 400
    
    num_days = (end - start).days + 1
    if num_days <= 0:
        return jsonify({'error': 'La date de fin doit etre apres la date de debut'}), 400
    
    total_plays = plays_per_day * num_days
    
    availability = calculate_availability(
        screen, start_date, end_date, period_id, slot_duration, content_type
    )
    
    if total_plays > availability['available_plays']:
        total_plays = availability['available_plays']
        plays_per_day = total_plays // num_days if num_days > 0 else total_plays
    
    slot = TimeSlot.query.filter_by(
        screen_id=screen.id,
        content_type=content_type,
        duration_seconds=slot_duration
    ).first()
    
    if not slot:
        return jsonify({'error': 'Creneau non disponible'}), 400
    
    period = TimePeriod.query.get(period_id) if period_id else None
    multiplier = period.price_multiplier if period else 1.0
    
    price_per_play = slot.price_per_play * multiplier
    total_price = price_per_play * total_plays
    
    org = screen.organization
    vat_rate = org.vat_rate if org and org.vat_rate else 0
    vat_amount = round(total_price * (vat_rate / 100), 2) if vat_rate > 0 else 0
    total_price_with_vat = round(total_price + vat_amount, 2)
    
    distribution = calculate_equitable_distribution(total_plays, start_date, end_date, period_id)
    
    return jsonify({
        'num_days': num_days,
        'plays_per_day': plays_per_day,
        'total_plays': total_plays,
        'max_available_plays': availability['available_plays'],
        'price_per_play': round(price_per_play, 2),
        'total_price': round(total_price, 2),
        'vat_rate': vat_rate,
        'vat_amount': vat_amount,
        'total_price_with_vat': total_price_with_vat,
        'distribution': distribution['distribution']
    })
