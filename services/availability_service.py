from datetime import datetime, date, timedelta
from sqlalchemy import or_
from models import Screen, Booking, TimePeriod, TimeSlot


def get_period_duration_seconds(period):
    """Calculate the duration of a time period in seconds"""
    if period.start_hour <= period.end_hour:
        hours = period.end_hour - period.start_hour
    else:
        hours = (24 - period.start_hour) + period.end_hour
    return hours * 3600


def get_reserved_seconds_for_period(screen_id, period_id, target_date, all_periods=None, preloaded_bookings=None):
    """
    Calculate total reserved seconds for a specific period on a specific date.
    Includes:
    - Bookings explicitly assigned to this period (full seconds)
    - Bookings with no period (NULL) - prorated by period duration ratio
    
    Args:
        screen_id: The screen ID
        period_id: The period ID to check
        target_date: The date to check
        all_periods: List of all periods for the screen (for prorating NULL period bookings)
        preloaded_bookings: Optional list of pre-fetched bookings to avoid DB queries
    """
    period_bookings = []
    null_period_bookings = []
    
    if preloaded_bookings is not None:
        for booking in preloaded_bookings:
            # Check date overlap
            start_ok = booking.start_date <= target_date
            end_ok = (booking.end_date is None) or (booking.end_date >= target_date)

            if start_ok and end_ok:
                if booking.time_period_id == period_id:
                    period_bookings.append(booking)
                elif booking.time_period_id is None:
                    null_period_bookings.append(booking)
    else:
        period_bookings = Booking.query.filter(
            Booking.screen_id == screen_id,
            Booking.status.in_(['pending', 'active']),
            Booking.start_date <= target_date,
            or_(Booking.end_date >= target_date, Booking.end_date == None),
            Booking.time_period_id == period_id
        ).all()

        null_period_bookings = Booking.query.filter(
            Booking.screen_id == screen_id,
            Booking.status.in_(['pending', 'active']),
            Booking.start_date <= target_date,
            or_(Booking.end_date >= target_date, Booking.end_date == None),
            Booking.time_period_id == None
        ).all()
    
    total_reserved_seconds = 0
    for booking in period_bookings:
        if booking.start_date and booking.end_date:
            booking_days = (booking.end_date - booking.start_date).days + 1
            if booking_days > 0:
                plays_per_day = booking.num_plays / booking_days
                total_reserved_seconds += plays_per_day * booking.slot_duration
        else:
            total_reserved_seconds += booking.num_plays * booking.slot_duration
    
    if null_period_bookings and all_periods:
        total_day_seconds = sum(get_period_duration_seconds(p) for p in all_periods)
        current_period = next((p for p in all_periods if p.id == period_id), None)
        if current_period and total_day_seconds > 0:
            period_ratio = get_period_duration_seconds(current_period) / total_day_seconds
            
            for booking in null_period_bookings:
                if booking.start_date and booking.end_date:
                    booking_days = (booking.end_date - booking.start_date).days + 1
                    if booking_days > 0:
                        plays_per_day = booking.num_plays / booking_days
                        total_reserved_seconds += (plays_per_day * booking.slot_duration) * period_ratio
                else:
                    total_reserved_seconds += (booking.num_plays * booking.slot_duration) * period_ratio
    
    return total_reserved_seconds


def calculate_availability(screen, start_date, end_date, period_id=None, slot_duration=None, content_type='image', preloaded_bookings=None):
    """
    Calculate available slots for a screen during a date range.
    
    Returns a dict with:
    - total_available_seconds: Total free seconds across all days
    - available_plays: Number of plays available for given slot duration
    - daily_breakdown: List of availability per day
    - periods: List of periods with their availability
    """
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    periods = screen.time_periods
    if period_id:
        periods = [p for p in periods if p.id == period_id]
    
    if not periods:
        return {
            'total_available_seconds': 0,
            'available_plays': 0,
            'daily_breakdown': [],
            'periods': []
        }
    
    slots = screen.time_slots
    if content_type:
        slots = [s for s in slots if s.content_type == content_type]
    if slot_duration:
        slots = [s for s in slots if s.duration_seconds == slot_duration]
    
    if not slots:
        return {
            'total_available_seconds': 0,
            'available_plays': 0,
            'daily_breakdown': [],
            'periods': []
        }
    
    target_slot_duration = slot_duration if slot_duration else (slots[0].duration_seconds if slots else 15)
    
    # Pre-fetch all relevant bookings for the entire date range
    if preloaded_bookings is not None:
        # Filter preloaded bookings to ensure they match date range and status
        # Note: Caller is responsible for passing bookings for this screen
        all_bookings = [
            b for b in preloaded_bookings
            if b.status in ['pending', 'active'] and
               b.start_date <= end_date and
               (b.end_date is None or b.end_date >= start_date)
        ]
    else:
        all_bookings = Booking.query.filter(
            Booking.screen_id == screen.id,
            Booking.status.in_(['pending', 'active']),
            Booking.start_date <= end_date,
            or_(Booking.end_date >= start_date, Booking.end_date == None)
        ).all()

    total_available_seconds = 0
    daily_breakdown = []
    period_summary = {}
    
    current_date = start_date
    now_dt = datetime.now()
    buffer_delta = timedelta(minutes=screen.security_buffer_minutes or 30)
    min_start_dt = now_dt + buffer_delta
    
    while current_date <= end_date:
        day_info = {
            'date': current_date.isoformat(),
            'periods': [],
            'total_available_seconds': 0
        }
        
        all_screen_periods = screen.time_periods
        
        for period in periods:
            # Check if period is in the past considering security buffer
            period_start_dt = datetime.combine(current_date, datetime.min.time().replace(hour=period.start_hour))
            if period_start_dt < min_start_dt:
                # If period is completely in the past (before buffer), it's not available
                # If it's partially in the past, we could be more precise, but for now we skip or adjust
                # Let's adjust available time if it's today and overlaps with buffer
                if current_date == now_dt.date():
                    # Calculate how much of the period is left after min_start_dt
                    period_end_hour = period.end_hour if period.end_hour > period.start_hour else 24
                    period_end_dt = datetime.combine(current_date, datetime.min.time().replace(hour=period_end_hour % 24))
                    if period_end_hour == 24:
                        period_end_dt += timedelta(days=1)
                    
                    if min_start_dt >= period_end_dt:
                        # Period is completely before security buffer
                        available = 0
                    else:
                        # Period is partially after security buffer
                        effective_start = max(period_start_dt, min_start_dt)
                        available_duration = (period_end_dt - effective_start).total_seconds()
                        period_duration = get_period_duration_seconds(period)
                        reserved = get_reserved_seconds_for_period(
                            screen.id, period.id, current_date, all_screen_periods, all_bookings
                        )
                        available = max(0, available_duration - reserved)
                else:
                    available = 0
            else:
                period_duration = get_period_duration_seconds(period)
                reserved = get_reserved_seconds_for_period(
                    screen.id, period.id, current_date, all_screen_periods, all_bookings
                )
                available = max(0, period_duration - reserved)
            
            available_plays = int(available / target_slot_duration)
            
            day_info['periods'].append({
                'period_id': period.id,
                'period_name': period.name,
                'start_hour': period.start_hour,
                'end_hour': period.end_hour,
                'total_seconds': period_duration,
                'reserved_seconds': reserved,
                'available_seconds': available,
                'available_plays': available_plays,
                'price_multiplier': period.price_multiplier
            })
            
            day_info['total_available_seconds'] += available
            
            if period.id not in period_summary:
                period_summary[period.id] = {
                    'period_id': period.id,
                    'period_name': period.name,
                    'total_available_seconds': 0,
                    'total_available_plays': 0,
                    'price_multiplier': period.price_multiplier
                }
            period_summary[period.id]['total_available_seconds'] += available
            period_summary[period.id]['total_available_plays'] += available_plays
        
        total_available_seconds += day_info['total_available_seconds']
        daily_breakdown.append(day_info)
        current_date += timedelta(days=1)
    
    total_available_plays = int(total_available_seconds / target_slot_duration) if target_slot_duration else 0
    
    return {
        'total_available_seconds': total_available_seconds,
        'available_plays': total_available_plays,
        'slot_duration': target_slot_duration,
        'num_days': len(daily_breakdown),
        'daily_breakdown': daily_breakdown,
        'periods': list(period_summary.values())
    }


def calculate_equitable_distribution(num_plays, start_date, end_date, period_id=None):
    """
    Calculate how plays should be distributed equitably across days and periods.
    
    Returns a dict with:
    - plays_per_day: Number of plays per day
    - distribution: List of (date, plays) tuples
    """
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    num_days = (end_date - start_date).days + 1
    if num_days <= 0:
        return {
            'plays_per_day': num_plays,
            'distribution': [(start_date.isoformat(), num_plays)]
        }
    
    base_plays = num_plays // num_days
    remainder = num_plays % num_days
    
    distribution = []
    current_date = start_date
    remaining_extra = remainder
    
    while current_date <= end_date:
        day_plays = base_plays
        if remaining_extra > 0:
            day_plays += 1
            remaining_extra -= 1
        
        distribution.append({
            'date': current_date.isoformat(),
            'plays': day_plays
        })
        current_date += timedelta(days=1)
    
    return {
        'plays_per_day': base_plays,
        'extra_plays_first_days': remainder,
        'distribution': distribution
    }


def calculate_plays_for_dates(screen, start_date, end_date, period_id=None, slot_duration=None, content_type='image'):
    """
    Calculate the recommended number of plays for a date range based on availability.
    This implements the algorithm logic for calculating plays when booking by dates.
    """
    availability = calculate_availability(
        screen, start_date, end_date, period_id, slot_duration, content_type
    )
    
    available_plays = availability['available_plays']
    
    if available_plays == 0:
        return {
            'recommended_plays': 0,
            'max_available': 0,
            'availability': availability
        }
    
    reasonable_usage = min(available_plays, int(available_plays * 0.1))
    reasonable_usage = max(10, reasonable_usage)
    reasonable_usage = min(reasonable_usage, available_plays)
    
    return {
        'recommended_plays': reasonable_usage,
        'max_available': available_plays,
        'availability': availability
    }
