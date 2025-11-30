from datetime import datetime
from app import db


class Booking(db.Model):
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    slot_duration = db.Column(db.Integer, nullable=False)
    time_period_id = db.Column(db.Integer, db.ForeignKey('time_periods.id'))
    num_plays = db.Column(db.Integer, nullable=False)
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
