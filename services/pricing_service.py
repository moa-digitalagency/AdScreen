from models import Screen, TimeSlot, TimePeriod


def calculate_booking_price(screen_id, content_type, duration, period_id, num_plays):
    """
    Calculate the total price for a booking.
    
    Args:
        screen_id: The screen ID
        content_type: 'image' or 'video'
        duration: Slot duration in seconds
        period_id: Time period ID (optional)
        num_plays: Number of plays requested
    
    Returns:
        dict: Pricing details or None if slot not found
    """
    slot = TimeSlot.query.filter_by(
        screen_id=screen_id,
        content_type=content_type,
        duration_seconds=duration
    ).first()
    
    if not slot:
        return None
    
    multiplier = 1.0
    period_name = "Toute la journée"
    
    if period_id:
        period = TimePeriod.query.get(period_id)
        if period:
            multiplier = period.price_multiplier
            period_name = period.name
    
    base_price = slot.price_per_play
    adjusted_price = base_price * multiplier
    total_price = adjusted_price * num_plays
    
    return {
        'base_price_per_play': round(base_price, 2),
        'multiplier': multiplier,
        'period_name': period_name,
        'price_per_play': round(adjusted_price, 2),
        'num_plays': num_plays,
        'total_price': round(total_price, 2),
        'duration_seconds': duration,
        'content_type': content_type
    }


def get_available_slots(screen_id, content_type=None):
    """
    Get available time slots for a screen.
    
    Args:
        screen_id: The screen ID
        content_type: Optional filter by content type
    
    Returns:
        list: Available slots with pricing info
    """
    query = TimeSlot.query.filter_by(screen_id=screen_id, is_active=True)
    
    if content_type:
        query = query.filter_by(content_type=content_type)
    
    slots = query.all()
    
    return [{
        'id': slot.id,
        'content_type': slot.content_type,
        'duration': slot.duration_seconds,
        'price': slot.price_per_play
    } for slot in slots]


def get_time_periods(screen_id):
    """
    Get time periods for a screen with multiplier info.
    
    Args:
        screen_id: The screen ID
    
    Returns:
        list: Time periods with pricing multipliers
    """
    periods = TimePeriod.query.filter_by(screen_id=screen_id).all()
    
    return [{
        'id': period.id,
        'name': period.name,
        'start_hour': period.start_hour,
        'end_hour': period.end_hour,
        'multiplier': period.price_multiplier,
        'display': f"{period.name} ({period.start_hour}h-{period.end_hour}h) x{period.price_multiplier}"
    } for period in periods]


def estimate_revenue(screen_id, days=30):
    """
    Estimate potential revenue for a screen based on full capacity.
    
    Args:
        screen_id: The screen ID
        days: Number of days to calculate for
    
    Returns:
        dict: Revenue estimates
    """
    screen = Screen.query.get(screen_id)
    if not screen:
        return None
    
    daily_revenue = 0
    
    for period in screen.time_periods:
        if period.start_hour <= period.end_hour:
            hours = period.end_hour - period.start_hour
        else:
            hours = (24 - period.start_hour) + period.end_hour
        
        minutes = hours * 60
        
        for slot in screen.time_slots:
            if not slot.is_active:
                continue
            
            plays_per_minute = 60 / slot.duration_seconds
            total_plays = minutes * plays_per_minute
            
            revenue = total_plays * slot.price_per_play * period.price_multiplier
            daily_revenue += revenue
    
    return {
        'daily_potential': round(daily_revenue, 2),
        'weekly_potential': round(daily_revenue * 7, 2),
        'monthly_potential': round(daily_revenue * days, 2),
        'days': days
    }
