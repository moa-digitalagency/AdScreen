from models import Screen, Content, Booking, Filler, InternalContent
from datetime import datetime


def get_current_period(screen):
    """
    Get the current time period for a screen based on the current hour.
    
    Args:
        screen: Screen model instance
    
    Returns:
        TimePeriod instance or None
    """
    current_hour = datetime.now().hour
    
    for period in screen.time_periods:
        if period.start_hour <= period.end_hour:
            if period.start_hour <= current_hour < period.end_hour:
                return period
        else:
            if current_hour >= period.start_hour or current_hour < period.end_hour:
                return period
    
    return None


def build_playlist(screen_id):
    """
    Build the playlist for a screen.
    
    The playlist is built with the following priority:
    - Paid content (priority 100)
    - Internal content (priority based on settings, default 80)
    - Filler content (priority 20)
    
    Args:
        screen_id: The screen ID
    
    Returns:
        list: List of playlist items sorted by priority
    """
    screen = Screen.query.get(screen_id)
    if not screen:
        return []
    
    current_period = get_current_period(screen)
    playlist = []
    
    paid_contents = Content.query.join(Booking).filter(
        Content.screen_id == screen_id,
        Content.status == 'approved',
        Booking.status == 'active',
        Booking.plays_completed < Booking.num_plays
    ).all()
    
    for content in paid_contents:
        if current_period and content.booking.time_period_id:
            if content.booking.time_period_id != current_period.id:
                continue
        
        playlist.append({
            'id': content.id,
            'type': content.content_type,
            'url': f'/{content.file_path}',
            'duration': content.duration_seconds or 10,
            'priority': 100,
            'category': 'paid',
            'booking_id': content.booking.id,
            'remaining_plays': content.booking.num_plays - content.booking.plays_completed
        })
    
    internal_contents = InternalContent.query.filter_by(
        screen_id=screen_id,
        is_active=True
    ).all()
    
    today = datetime.now().date()
    for internal in internal_contents:
        if internal.start_date and internal.start_date > today:
            continue
        if internal.end_date and internal.end_date < today:
            continue
        
        playlist.append({
            'id': internal.id,
            'type': internal.content_type,
            'url': f'/{internal.file_path}',
            'duration': internal.duration_seconds or 10,
            'priority': internal.priority,
            'category': 'internal',
            'name': internal.name
        })
    
    fillers = Filler.query.filter_by(
        screen_id=screen_id,
        is_active=True
    ).all()
    
    for filler in fillers:
        playlist.append({
            'id': filler.id,
            'type': filler.content_type,
            'url': f'/{filler.file_path}',
            'duration': filler.duration_seconds or 10,
            'priority': 20,
            'category': 'filler'
        })
    
    playlist.sort(key=lambda x: x['priority'], reverse=True)
    
    return playlist


def get_playlist_duration(playlist):
    """
    Calculate the total duration of a playlist.
    
    Args:
        playlist: List of playlist items
    
    Returns:
        float: Total duration in seconds
    """
    return sum(item.get('duration', 0) for item in playlist)


def calculate_daily_capacity(screen):
    """
    Calculate the maximum number of plays possible per day for a screen.
    
    Args:
        screen: Screen model instance
    
    Returns:
        dict: Capacity information per time period
    """
    capacity = {}
    
    for period in screen.time_periods:
        if period.start_hour <= period.end_hour:
            hours = period.end_hour - period.start_hour
        else:
            hours = (24 - period.start_hour) + period.end_hour
        
        minutes = hours * 60
        
        for slot in screen.time_slots:
            plays_per_minute = 60 / slot.duration_seconds
            total_plays = int(minutes * plays_per_minute)
            
            key = f"{period.name}_{slot.content_type}_{slot.duration_seconds}s"
            capacity[key] = {
                'period': period.name,
                'content_type': slot.content_type,
                'duration': slot.duration_seconds,
                'max_plays': total_plays,
                'hours': hours
            }
    
    return capacity
