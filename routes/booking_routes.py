from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from app import db
from models import Screen, TimeSlot, TimePeriod, Content, Booking
from datetime import datetime, date
import os
import secrets
import base64
import io
from werkzeug.utils import secure_filename
from utils.image_utils import validate_image
from utils.video_utils import validate_video, get_video_duration
from services.qr_service import generate_qr_base64
from services.receipt_generator import save_receipt_image, get_receipt_base64

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
    
    return render_template('booking/screen.html',
        screen=screen,
        current_period=current_period,
        slots_json=slots_json
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
    
    if booking_mode == 'dates':
        calculated_plays = int(request.form.get('calculated_plays', 10))
        num_plays = calculated_plays
    else:
        num_plays = int(request.form.get('num_plays', 10))
        calculated_plays = None
    
    if 'file' not in request.files:
        flash('Veuillez sélectionner un fichier.', 'error')
        return redirect(url_for('booking.screen_booking', screen_code=screen_code))
    
    file = request.files['file']
    
    if not file.filename:
        flash('Veuillez sélectionner un fichier.', 'error')
        return redirect(url_for('booking.screen_booking', screen_code=screen_code))
    
    if not allowed_file(file.filename, content_type):
        flash('Format de fichier non supporté.', 'error')
        return redirect(url_for('booking.screen_booking', screen_code=screen_code))
    
    slot = TimeSlot.query.filter_by(
        screen_id=screen.id,
        content_type=content_type,
        duration_seconds=slot_duration
    ).first()
    
    if not slot:
        flash('Créneau non disponible.', 'error')
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
            flash(f'Image non valide: {error}', 'error')
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
            flash(f'Vidéo non valide: {error}', 'error')
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
        start_date=datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else date.today(),
        end_date=datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None,
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
    
    receipt_path = save_receipt_image(booking, screen, content, screen_qr)
    receipt_base64 = get_receipt_base64(booking, screen, content, screen_qr)
    
    return render_template('booking/success.html',
        booking=booking,
        screen=screen,
        content=content,
        reservation_qr=reservation_qr,
        booking_qr=screen_qr,
        receipt_base64=receipt_base64,
        receipt_path=receipt_path
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
    
    return jsonify({
        'price_per_play': round(price_per_play, 2),
        'total_price': round(total_price, 2),
        'num_plays': num_plays
    })


@booking_bp.route('/status/<int:booking_id>')
def booking_status(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    return render_template('booking/status.html', booking=booking)


@booking_bp.route('/receipt/<reservation_number>')
def download_receipt(reservation_number):
    booking = Booking.query.filter_by(reservation_number=reservation_number).first_or_404()
    
    receipt_path = os.path.join('static', 'uploads', 'receipts', f'receipt_{reservation_number}.png')
    
    if os.path.exists(receipt_path):
        return send_file(
            receipt_path,
            mimetype='image/png',
            as_attachment=True,
            download_name=f'recu_{reservation_number}.png'
        )
    
    booking_qr = generate_qr_base64(
        url_for('booking.screen_booking', screen_code=booking.screen.unique_code, _external=True),
        box_size=6, border=2
    )
    receipt_path = save_receipt_image(booking, booking.screen, booking.content, booking_qr)
    
    return send_file(
        receipt_path,
        mimetype='image/png',
        as_attachment=True,
        download_name=f'recu_{reservation_number}.png'
    )
