"""
Service de gestion des overlays avec priorité
"""
from datetime import datetime
from app import db
from models.screen_overlay import ScreenOverlay
from models.broadcast import Broadcast
import logging

logger = logging.getLogger(__name__)


PRIORITY_BROADCAST = 200
PRIORITY_LOCAL_HIGH = 100
PRIORITY_LOCAL_NORMAL = 50
PRIORITY_LOCAL_LOW = 20


def create_overlay_from_broadcast(broadcast, screen):
    """
    Crée un overlay local à partir d'une diffusion broadcast.
    Met en pause les overlays existants sur la même position.
    """
    existing_overlays = ScreenOverlay.query.filter_by(
        screen_id=screen.id,
        position=broadcast.overlay_position,
        is_active=True,
        is_paused=False
    ).all()
    
    for overlay in existing_overlays:
        overlay.pause(by_broadcast_id=broadcast.id)
        logger.info(f"Overlay {overlay.id} mis en pause par broadcast {broadcast.id}")
    
    new_overlay = ScreenOverlay(
        screen_id=screen.id,
        overlay_type=broadcast.overlay_type,
        message=broadcast.overlay_message,
        image_path=broadcast.overlay_image_path,
        position=broadcast.overlay_position,
        corner_position=broadcast.overlay_corner_position,
        background_color=broadcast.overlay_background_color,
        text_color=broadcast.overlay_text_color,
        font_size=broadcast.overlay_font_size,
        scroll_speed=broadcast.overlay_scroll_speed,
        corner_size=broadcast.overlay_corner_size,
        position_mode=broadcast.overlay_position_mode,
        image_width_percent=broadcast.overlay_image_width_percent,
        image_pos_x=broadcast.overlay_image_pos_x,
        image_pos_y=broadcast.overlay_image_pos_y,
        image_opacity=broadcast.overlay_image_opacity,
        priority=PRIORITY_BROADCAST,
        source=ScreenOverlay.SOURCE_BROADCAST,
        source_broadcast_id=broadcast.id,
        start_time=broadcast.start_datetime,
        end_time=broadcast.end_datetime,
        is_active=True
    )
    
    db.session.add(new_overlay)
    db.session.commit()
    
    logger.info(f"Overlay créé depuis broadcast {broadcast.id} pour écran {screen.id}")
    return new_overlay


def get_active_overlays_for_screen(screen_id, include_paused=False):
    """
    Récupère les overlays actifs pour un écran, triés par priorité.
    """
    query = ScreenOverlay.query.filter_by(
        screen_id=screen_id,
        is_active=True
    )
    
    if not include_paused:
        query = query.filter_by(is_paused=False)
    
    overlays = query.order_by(ScreenOverlay.priority.desc()).all()
    
    active_overlays = [o for o in overlays if o.is_currently_active()]
    
    return active_overlays


def get_overlays_by_position(screen_id, position=None):
    """
    Récupère les overlays groupés par position avec statut.
    """
    query = ScreenOverlay.query.filter_by(
        screen_id=screen_id,
        is_active=True
    )
    
    if position:
        query = query.filter_by(position=position)
    
    overlays = query.order_by(ScreenOverlay.priority.desc()).all()
    
    grouped = {}
    for overlay in overlays:
        pos = overlay.position
        if pos not in grouped:
            grouped[pos] = {'active': [], 'paused': []}
        
        if overlay.is_paused:
            grouped[pos]['paused'].append(overlay)
        elif overlay.is_currently_active():
            grouped[pos]['active'].append(overlay)
    
    return grouped


def pause_overlay(overlay_id, by_broadcast_id=None):
    """
    Met en pause un overlay.
    """
    overlay = ScreenOverlay.query.get(overlay_id)
    if overlay:
        overlay.pause(by_broadcast_id)
        db.session.commit()
        return True
    return False


def resume_overlay(overlay_id):
    """
    Reprend un overlay en pause.
    """
    overlay = ScreenOverlay.query.get(overlay_id)
    if overlay and overlay.is_paused:
        overlay.resume()
        db.session.commit()
        return True
    return False


def suspend_overlay(overlay_id):
    """
    Suspend un overlay (désactive temporairement).
    """
    overlay = ScreenOverlay.query.get(overlay_id)
    if overlay:
        overlay.is_active = False
        db.session.commit()
        return True
    return False


def activate_overlay(overlay_id):
    """
    Active un overlay suspendu.
    """
    overlay = ScreenOverlay.query.get(overlay_id)
    if overlay:
        overlay.is_active = True
        overlay.is_paused = False
        db.session.commit()
        return True
    return False


def delete_overlay(overlay_id):
    """
    Supprime un overlay.
    """
    overlay = ScreenOverlay.query.get(overlay_id)
    if overlay:
        paused_overlays = ScreenOverlay.query.filter_by(
            paused_by_broadcast_id=overlay.source_broadcast_id if overlay.source == ScreenOverlay.SOURCE_BROADCAST else None
        ).all()
        
        for paused in paused_overlays:
            paused.resume()
        
        db.session.delete(overlay)
        db.session.commit()
        return True
    return False


def cleanup_expired_broadcast_overlays():
    """
    Nettoie les overlays de broadcast expirés et reprend les overlays en pause.
    """
    now = datetime.utcnow()
    
    # Optimize: Check count first
    expired_count = ScreenOverlay.query.filter(
        ScreenOverlay.source == ScreenOverlay.SOURCE_BROADCAST,
        ScreenOverlay.end_time < now
    ).count()

    if expired_count == 0:
        return 0

    expired_overlays = ScreenOverlay.query.filter(
        ScreenOverlay.source == ScreenOverlay.SOURCE_BROADCAST,
        ScreenOverlay.end_time < now
    ).all()
    
    for overlay in expired_overlays:
        paused_overlays = ScreenOverlay.query.filter_by(
            screen_id=overlay.screen_id,
            position=overlay.position,
            paused_by_broadcast_id=overlay.source_broadcast_id,
            is_paused=True
        ).all()
        
        for paused in paused_overlays:
            paused.resume()
            logger.info(f"Overlay {paused.id} repris après expiration du broadcast {overlay.source_broadcast_id}")
        
        overlay.is_active = False
        logger.info(f"Overlay broadcast {overlay.id} désactivé (expiré)")
    
    db.session.commit()
    return len(expired_overlays)


def sync_broadcast_overlays(screen):
    """
    Synchronise les overlays broadcast pour un écran.
    Crée de nouveaux overlays locaux si nécessaire.
    """
    from models.broadcast import Broadcast
    
    active_broadcasts = Broadcast.query.filter_by(
        is_active=True,
        broadcast_type=Broadcast.BROADCAST_TYPE_OVERLAY
    ).all()
    
    for broadcast in active_broadcasts:
        if broadcast.applies_to_screen(screen):
            existing = ScreenOverlay.query.filter_by(
                screen_id=screen.id,
                source=ScreenOverlay.SOURCE_BROADCAST,
                source_broadcast_id=broadcast.id
            ).first()
            
            if not existing:
                create_overlay_from_broadcast(broadcast, screen)
    
    cleanup_expired_broadcast_overlays()
