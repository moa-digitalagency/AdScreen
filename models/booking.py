from datetime import datetime
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
    status = db.Column(db.String(20), default='pending')
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
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
