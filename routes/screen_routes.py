from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from models import Screen, SiteSetting
from services.qr_service import generate_enhanced_qr_base64, generate_qr_base64
from services.translation_service import t

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
    
    if screen.is_active:
        flash(t('flash.screen_activated'), 'success')
    else:
        flash(t('flash.screen_deactivated'), 'success')
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
    
    flash(t('flash.screen_deleted'), 'success')
    return redirect(url_for('org.screens'))


@screen_bp.route('/<int:screen_id>/mode', methods=['POST'])
@login_required
def set_mode(screen_id):
    screen = Screen.query.filter_by(
        id=screen_id,
        organization_id=current_user.organization_id
    ).first_or_404()
    
    mode = request.form.get('mode', 'playlist')
    redirect_dashboard = request.form.get('redirect_dashboard', '')
    
    if mode not in ['playlist', 'iptv']:
        mode = 'playlist'
    
    if mode == 'iptv' and not screen.iptv_enabled:
        flash(t('flash.iptv_not_enabled'), 'error')
        if redirect_dashboard:
            return redirect(url_for('org.dashboard'))
        return redirect(url_for('org.screen_iptv', screen_id=screen_id))
    
    screen.current_mode = mode
    db.session.commit()
    
    if mode == 'iptv':
        flash(t('flash.iptv_mode_activated', name=screen.name), 'success')
    else:
        flash(t('flash.playlist_mode_activated', name=screen.name), 'success')
    
    if redirect_dashboard:
        return redirect(url_for('org.dashboard'))
    return redirect(request.referrer or url_for('org.screen_detail', screen_id=screen_id))


@screen_bp.route('/<int:screen_id>/iptv/channel', methods=['POST'])
@login_required
def set_iptv_channel(screen_id):
    screen = Screen.query.filter_by(
        id=screen_id,
        organization_id=current_user.organization_id
    ).first_or_404()
    
    if not screen.iptv_enabled:
        flash(t('flash.iptv_not_enabled'), 'error')
        return redirect(url_for('org.screen_detail', screen_id=screen_id))
    
    channel_url = request.form.get('channel_url', '')
    channel_name = request.form.get('channel_name', '')
    
    screen.current_iptv_channel = channel_url
    screen.current_iptv_channel_name = channel_name
    screen.current_mode = 'iptv'
    db.session.commit()
    
    flash(t('flash.channel_selected', name=channel_name), 'success')
    return redirect(url_for('org.screen_iptv', screen_id=screen_id))
