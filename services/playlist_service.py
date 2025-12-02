from models import Screen, Content, Booking, Filler, InternalContent, Broadcast
from datetime import datetime, timedelta


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


def get_scheduled_broadcasts_for_screen(screen):
    """
    Get all scheduled broadcasts that apply to a given screen.
    
    Args:
        screen: Screen model instance
    
    Returns:
        list: List of scheduled broadcast dicts sorted by priority and scheduled time
    """
    all_broadcasts = Broadcast.query.filter(
        Broadcast.is_active == True,
        Broadcast.broadcast_type == Broadcast.BROADCAST_TYPE_CONTENT
    ).all()
    
    scheduled_broadcasts = []
    now = datetime.now()
    
    for broadcast in all_broadcasts:
        if not broadcast.applies_to_screen(screen):
            continue
        
        if broadcast.schedule_mode == Broadcast.SCHEDULE_MODE_SCHEDULED:
            if broadcast.recurrence_type == Broadcast.RECURRENCE_NONE:
                if broadcast.scheduled_datetime:
                    time_until_trigger = (broadcast.scheduled_datetime - now).total_seconds()
                    if time_until_trigger >= -broadcast.content_duration and time_until_trigger <= 300:
                        scheduled_broadcasts.append({
                            'broadcast': broadcast,
                            'trigger_time': broadcast.scheduled_datetime,
                            'priority': broadcast.schedule_priority,
                            'override': broadcast.override_playlist
                        })
            else:
                next_occurrence = broadcast.get_next_occurrence(now - timedelta(seconds=broadcast.content_duration))
                if next_occurrence:
                    time_until_trigger = (next_occurrence - now).total_seconds()
                    if time_until_trigger <= 300:
                        scheduled_broadcasts.append({
                            'broadcast': broadcast,
                            'trigger_time': next_occurrence,
                            'priority': broadcast.schedule_priority,
                            'override': broadcast.override_playlist
                        })
        else:
            if broadcast.is_currently_active():
                scheduled_broadcasts.append({
                    'broadcast': broadcast,
                    'trigger_time': now,
                    'priority': broadcast.content_priority,
                    'override': False
                })
    
    scheduled_broadcasts.sort(key=lambda x: (-x['priority'], x['trigger_time']))
    
    return scheduled_broadcasts


def build_playlist_with_scheduled(screen_id):
    """
    Build the playlist for a screen including scheduled broadcasts.
    
    This function integrates scheduled broadcasts with priority override logic:
    - Higher priority broadcasts can override/shift lower priority content
    - Override broadcasts are inserted at exact scheduled times
    - Non-override broadcasts are added based on priority
    
    Args:
        screen_id: The screen ID
    
    Returns:
        dict: Contains 'playlist' (items sorted by priority), 
              'scheduled_insertions' (broadcasts with exact timing),
              'timeline' (ordered sequence respecting scheduled times)
    """
    screen = Screen.query.get(screen_id)
    if not screen:
        return {'playlist': [], 'scheduled_insertions': [], 'timeline': []}
    
    base_playlist = build_playlist(screen_id)
    
    scheduled_broadcasts = get_scheduled_broadcasts_for_screen(screen)
    
    if not scheduled_broadcasts:
        return {
            'playlist': base_playlist,
            'scheduled_insertions': [],
            'timeline': base_playlist
        }
    
    scheduled_insertions = []
    override_broadcasts = []
    regular_broadcasts = []
    
    for sb in scheduled_broadcasts:
        broadcast = sb['broadcast']
        broadcast_item = broadcast.to_content_dict()
        broadcast_item['trigger_time'] = sb['trigger_time'].isoformat() if sb['trigger_time'] else None
        broadcast_item['schedule_priority'] = sb['priority']
        
        if sb['override']:
            override_broadcasts.append({
                'item': broadcast_item,
                'trigger_time': sb['trigger_time'],
                'priority': sb['priority'],
                'duration': broadcast.content_duration
            })
            scheduled_insertions.append(broadcast_item)
        else:
            regular_broadcasts.append(broadcast_item)
    
    for rb in regular_broadcasts:
        if not any(item.get('id') == rb['id'] for item in base_playlist):
            base_playlist.append(rb)
    
    base_playlist.sort(key=lambda x: x.get('schedule_priority', x.get('priority', 0)), reverse=True)
    
    timeline = build_timeline_with_overrides(base_playlist, override_broadcasts)
    
    return {
        'playlist': base_playlist,
        'scheduled_insertions': scheduled_insertions,
        'timeline': timeline
    }


def build_timeline_with_overrides(base_playlist, override_broadcasts):
    """
    Build a timeline that respects scheduled override broadcasts.
    
    When an override broadcast is scheduled:
    1. It is inserted at its exact scheduled time
    2. Lower priority content that would play at that time is shifted forward
    3. The rest of the playlist continues after the override
    
    Args:
        base_playlist: The base playlist items
        override_broadcasts: List of override broadcast definitions
    
    Returns:
        list: Timeline with items in playback order, including timing info
    """
    if not override_broadcasts:
        return base_playlist
    
    now = datetime.now()
    timeline = []
    current_time = now
    
    override_broadcasts_sorted = sorted(override_broadcasts, key=lambda x: x['trigger_time'])
    
    base_playlist_copy = list(base_playlist)
    override_index = 0
    
    while base_playlist_copy or override_index < len(override_broadcasts_sorted):
        if override_index < len(override_broadcasts_sorted):
            next_override = override_broadcasts_sorted[override_index]
            
            while base_playlist_copy and current_time < next_override['trigger_time']:
                item = base_playlist_copy.pop(0)
                item_duration = item.get('duration', 10)
                item_end_time = current_time + timedelta(seconds=item_duration)
                
                if item_end_time > next_override['trigger_time']:
                    remaining_time = (next_override['trigger_time'] - current_time).total_seconds()
                    if remaining_time > 0:
                        partial_item = dict(item)
                        partial_item['partial'] = True
                        partial_item['partial_duration'] = remaining_time
                        partial_item['start_time'] = current_time.isoformat()
                        timeline.append(partial_item)
                    
                    base_playlist_copy.insert(0, item)
                    current_time = next_override['trigger_time']
                    break
                else:
                    item['start_time'] = current_time.isoformat()
                    timeline.append(item)
                    current_time = item_end_time
            
            if current_time >= next_override['trigger_time'] or not base_playlist_copy:
                override_item = dict(next_override['item'])
                override_item['start_time'] = next_override['trigger_time'].isoformat()
                override_item['is_override'] = True
                timeline.append(override_item)
                current_time = next_override['trigger_time'] + timedelta(seconds=next_override['duration'])
                override_index += 1
        else:
            for item in base_playlist_copy:
                item['start_time'] = current_time.isoformat()
                timeline.append(item)
                current_time += timedelta(seconds=item.get('duration', 10))
            base_playlist_copy = []
    
    return timeline


def get_active_scheduled_broadcast(screen):
    """
    Check if there's a scheduled broadcast that should play RIGHT NOW.
    
    This is used by the player to check if it needs to immediately
    switch to a scheduled broadcast.
    
    Args:
        screen: Screen model instance
    
    Returns:
        Broadcast or None: The broadcast that should play now, if any
    """
    all_broadcasts = Broadcast.query.filter(
        Broadcast.is_active == True,
        Broadcast.broadcast_type == Broadcast.BROADCAST_TYPE_CONTENT,
        Broadcast.schedule_mode == Broadcast.SCHEDULE_MODE_SCHEDULED,
        Broadcast.override_playlist == True
    ).all()
    
    now = datetime.now()
    
    for broadcast in all_broadcasts:
        if not broadcast.applies_to_screen(screen):
            continue
        
        if broadcast.should_trigger_now():
            return broadcast
    
    return None
