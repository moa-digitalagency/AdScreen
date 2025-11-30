from datetime import datetime
from app import db


class ScreenOverlay(db.Model):
    __tablename__ = 'screen_overlays'
    
    id = db.Column(db.Integer, primary_key=True)
    screen_id = db.Column(db.Integer, db.ForeignKey('screens.id'), nullable=False)
    
    overlay_type = db.Column(db.String(20), default='ticker')
    message = db.Column(db.Text)
    image_path = db.Column(db.String(500))
    position = db.Column(db.String(20), default='footer')
    
    background_color = db.Column(db.String(20), default='#000000')
    text_color = db.Column(db.String(20), default='#FFFFFF')
    font_size = db.Column(db.Integer, default=24)
    scroll_speed = db.Column(db.Integer, default=50)
    
    is_active = db.Column(db.Boolean, default=True)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    screen = db.relationship('Screen', back_populates='overlays')
    
    TYPE_TICKER = 'ticker'
    TYPE_IMAGE = 'image'
    
    POSITION_HEADER = 'header'
    POSITION_BODY = 'body'
    POSITION_FOOTER = 'footer'
    
    def is_currently_active(self):
        if not self.is_active:
            return False
        
        now = datetime.utcnow()
        if self.start_time and now < self.start_time:
            return False
        if self.end_time and now > self.end_time:
            return False
        
        return True
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.overlay_type,
            'message': self.message,
            'image_path': self.image_path,
            'position': self.position,
            'background_color': self.background_color,
            'text_color': self.text_color,
            'font_size': self.font_size,
            'scroll_speed': self.scroll_speed,
            'is_active': self.is_currently_active()
        }
