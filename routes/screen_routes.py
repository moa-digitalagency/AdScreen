from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from models import Screen
import qrcode
import io
import base64

screen_bp = Blueprint('screen', __name__)


@screen_bp.route('/<int:screen_id>/qr')
@login_required
def generate_qr(screen_id):
    screen = Screen.query.filter_by(
        id=screen_id,
        organization_id=current_user.organization_id
    ).first_or_404()
    
    booking_url = url_for('booking.screen_booking', screen_code=screen.unique_code, _external=True)
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(booking_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return render_template('org/screen_qr.html',
        screen=screen,
        qr_image=img_base64,
        booking_url=booking_url
    )


@screen_bp.route('/<int:screen_id>/toggle', methods=['POST'])
@login_required
def toggle_screen(screen_id):
    screen = Screen.query.filter_by(
        id=screen_id,
        organization_id=current_user.organization_id
    ).first_or_404()
    
    screen.is_active = not screen.is_active
    db.session.commit()
    
    status = "activé" if screen.is_active else "désactivé"
    flash(f'Écran {status}.', 'success')
    return redirect(url_for('org.screen_detail', screen_id=screen_id))


@screen_bp.route('/<int:screen_id>/delete', methods=['POST'])
@login_required
def delete_screen(screen_id):
    screen = Screen.query.filter_by(
        id=screen_id,
        organization_id=current_user.organization_id
    ).first_or_404()
    
    db.session.delete(screen)
    db.session.commit()
    
    flash('Écran supprimé.', 'success')
    return redirect(url_for('org.screens'))
