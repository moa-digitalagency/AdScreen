from datetime import datetime, time, timedelta
import secrets
from app import db


class Booking(db.Model):
    __tablename__ = 'bookings'
    
    BOOKING_MODE_PLAYS = 'plays'
    BOOKING_MODE_DATES = 'dates'
    
    id = db.Column(db.Integer, primary_key=True)
    reservation_number = db.Column(db.String(16), unique=True, nullable=True)
    booking_mode = db.Column(db.String(20), default='plays')
    slot_duration = db.Column(db.Integer, nullable=False)
    time_period_id = db.Column(db.Integer, db.ForeignKey('time_periods.id'))
    num_plays = db.Column(db.Integer, nullable=False)
    calculated_plays = db.Column(db.Integer, nullable=True)
    plays_completed = db.Column(db.Integer, default=0)
    price_per_play = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    
    vat_rate = db.Column(db.Float, default=0.0)
    vat_amount = db.Column(db.Float, default=0.0)
    total_price_with_vat = db.Column(db.Float, nullable=True)
    
    status = db.Column(db.String(20), default='pending')
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    payment_status = db.Column(db.String(20), default='pending')
    payment_reference = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    validated_date = db.Column(db.DateTime, nullable=True)  # When ad was approved/validated
    
    screen_id = db.Column(db.Integer, db.ForeignKey('screens.id'), nullable=False)
    screen = db.relationship('Screen', back_populates='bookings')
    
    content_id = db.Column(db.Integer, db.ForeignKey('contents.id'), nullable=False)
    content = db.relationship('Content', back_populates='booking')
    
    time_period = db.relationship('TimePeriod')
    
    def generate_reservation_number(self):
        """Generate a unique reservation number"""
        self.reservation_number = f"RES-{secrets.token_hex(4).upper()}"
        return self.reservation_number
    
    def calculate_vat(self, vat_rate=None):
        """Calculate and set VAT based on rate"""
        rate = vat_rate if vat_rate is not None else self.vat_rate or 0
        self.vat_rate = rate
        self.vat_amount = round(self.total_price * (rate / 100), 2) if rate > 0 else 0
        self.total_price_with_vat = round(self.total_price + self.vat_amount, 2)
        return self.vat_amount
    
    def get_total_with_vat(self):
        """Get total price including VAT"""
        if self.total_price_with_vat is not None:
            return self.total_price_with_vat
        return self.total_price + (self.vat_amount or 0)

    def is_playable_now(self):
        """Check if this booking's content should be displayed now based on start_date/start_time"""
        now = datetime.utcnow()
        today = now.date()

        # Must be approved and active
        if self.status != 'active':
            return False

        # Check start_date: content should not display before scheduled start
        if self.start_date and today < self.start_date:
            return False

        # Check start_time: if we're on start_date, verify start_time
        if self.start_date and today == self.start_date:
            if self.start_time and now.time() < self.start_time:
                return False

        # Check end_date: inclusive, so plays on end_date
        if self.end_date and today > self.end_date:
            return False

        return True

    def calculate_dynamic_plays(self):
        """
        Recalculate num_plays if validation happened after scheduled start.
        If ad was validated after start_date, adjust plays to respect contract
        by increasing frequency over remaining time window.

        Returns: adjusted play count (or original if no adjustment needed)
        """
        if not self.validated_date or not self.start_date:
            return self.num_plays

        # Convert validated_date to date for comparison
        validated_dt = self.validated_date if isinstance(self.validated_date, datetime) else datetime.combine(self.validated_date, time.min)
        validated_date = validated_dt.date()

        # If validated before or on start_date, no adjustment needed
        if validated_date <= self.start_date:
            return self.num_plays

        # Validation was late - recalculate plays per day
        end_date = self.end_date if self.end_date else validated_date + timedelta(days=30)  # 30-day fallback

        # Original intended days
        total_days = (end_date - self.start_date).days + 1
        if total_days <= 0:
            return self.num_plays

        # Remaining days from validation onwards
        remaining_days = (end_date - validated_date).days + 1
        if remaining_days <= 0:
            return self.num_plays

        # Plays per day: original num_plays / original days
        plays_per_day = self.num_plays / total_days if total_days > 0 else 1

        # Adjusted plays for remaining period: plays_per_day * remaining_days
        adjusted_plays = int(plays_per_day * remaining_days)

        # Ensure at least the original minimum
        return max(adjusted_plays, self.num_plays)
