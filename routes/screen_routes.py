from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from models import Screen, SiteSetting
from services.qr_service import generate_enhanced_qr_base64, generate_qr_base64

screen_bp = Blueprint('screen', __name__)


@screen_bp.route('/<int:screen_id>/qr')
@login_required
def generate_qr(screen_id):
    screen = Screen.query.filter_by(
        id=screen_id,
        organization_id=current_user.organization_id
    ).first_or_404()
    
    booking_url = url_for('booking.screen_booking', screen_code=screen.unique_code, _external=True)
    platform_name = SiteSetting.get('platform_name', 'AdScreen')
    
    enhanced_qr = generate_enhanced_qr_base64(screen, booking_url, platform_name)
    simple_qr = generate_qr_base64(booking_url)
    
    return render_template('org/screen_qr.html',
        screen=screen,
        qr_image=simple_qr,
        enhanced_qr_image=enhanced_qr,
        booking_url=booking_url,
        platform_name=platform_name
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
