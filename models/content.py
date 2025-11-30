from datetime import datetime
from app import db


class Content(db.Model):
    __tablename__ = 'contents'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), nullable=False)
    original_filename = db.Column(db.String(256))
    content_type = db.Column(db.String(20), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    file_size = db.Column(db.Integer)
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    duration_seconds = db.Column(db.Float)
    status = db.Column(db.String(20), default='pending')
    rejection_reason = db.Column(db.Text)
    client_name = db.Column(db.String(128))
    client_email = db.Column(db.String(120))
    client_phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    validated_at = db.Column(db.DateTime)
    
    screen_id = db.Column(db.Integer, db.ForeignKey('screens.id'), nullable=False)
    screen = db.relationship('Screen', back_populates='contents')
    
    booking = db.relationship('Booking', back_populates='content', uselist=False)
