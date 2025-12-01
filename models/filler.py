from datetime import datetime
from app import db


class Filler(db.Model):
    __tablename__ = 'fillers'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), nullable=False)
    content_type = db.Column(db.String(20), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    duration_seconds = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=True)
    in_playlist = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    screen_id = db.Column(db.Integer, db.ForeignKey('screens.id'), nullable=False)
    screen = db.relationship('Screen', back_populates='fillers')
