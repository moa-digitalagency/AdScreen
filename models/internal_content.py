from datetime import datetime, date as date_type
from app import db


class InternalContent(db.Model):
    __tablename__ = 'internal_contents'
    
    SCHEDULE_IMMEDIATE = 'immediate'
    SCHEDULE_PERIOD = 'period'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    filename = db.Column(db.String(256), nullable=False)
    content_type = db.Column(db.String(20), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    duration_seconds = db.Column(db.Float)
    priority = db.Column(db.Integer, default=80)
    is_active = db.Column(db.Boolean, default=True)
    in_playlist = db.Column(db.Boolean, default=True)
    
    schedule_type = db.Column(db.String(20), default=SCHEDULE_IMMEDIATE)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    plays_per_day = db.Column(db.Integer, default=10)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    screen_id = db.Column(db.Integer, db.ForeignKey('screens.id'), nullable=False)
    screen = db.relationship('Screen', back_populates='internal_contents')
    
    def is_currently_active(self):
        """Vérifie si le contenu doit être diffusé maintenant"""
        if not self.is_active or not self.in_playlist:
            return False
        
        if self.schedule_type == self.SCHEDULE_IMMEDIATE:
            return True
        
        today = date_type.today()
        if self.start_date and today < self.start_date:
            return False
        if self.end_date and today > self.end_date:
            return False
        
        return True
