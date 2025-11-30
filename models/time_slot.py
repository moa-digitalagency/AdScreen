from app import db


class TimeSlot(db.Model):
    __tablename__ = 'time_slots'
    
    id = db.Column(db.Integer, primary_key=True)
    content_type = db.Column(db.String(20), nullable=False)
    duration_seconds = db.Column(db.Integer, nullable=False)
    price_per_play = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    screen_id = db.Column(db.Integer, db.ForeignKey('screens.id'), nullable=False)
    screen = db.relationship('Screen', back_populates='time_slots')
