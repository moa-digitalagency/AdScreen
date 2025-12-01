from datetime import datetime, time
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
