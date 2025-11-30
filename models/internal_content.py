from datetime import datetime
from app import db


class InternalContent(db.Model):
    __tablename__ = 'internal_contents'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    filename = db.Column(db.String(256), nullable=False)
    content_type = db.Column(db.String(20), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    duration_seconds = db.Column(db.Float)
    priority = db.Column(db.Integer, default=80)
    is_active = db.Column(db.Boolean, default=True)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    screen_id = db.Column(db.Integer, db.ForeignKey('screens.id'), nullable=False)
    screen = db.relationship('Screen', back_populates='internal_contents')
