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
    corner_position = db.Column(db.String(20), default='top_left')
    
    background_color = db.Column(db.String(20), default='#000000')
    text_color = db.Column(db.String(20), default='#FFFFFF')
    font_size = db.Column(db.Integer, default=24)
    scroll_speed = db.Column(db.Integer, default=50)
    
    display_duration = db.Column(db.Integer, default=10)
    passage_limit = db.Column(db.Integer, default=0)
    frequency_unit = db.Column(db.String(20), default='hour')
    current_passage_count = db.Column(db.Integer, default=0)
    last_passage_reset = db.Column(db.DateTime)
    
    is_active = db.Column(db.Boolean, default=True)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    screen = db.relationship('Screen', back_populates='overlays')
    
    TYPE_TICKER = 'ticker'
    TYPE_IMAGE = 'image'
    TYPE_CORNER = 'corner'
    
    POSITION_HEADER = 'header'
    POSITION_BODY = 'body'
    POSITION_FOOTER = 'footer'
    
    CORNER_TOP_LEFT = 'top_left'
    CORNER_TOP_RIGHT = 'top_right'
    CORNER_BOTTOM_LEFT = 'bottom_left'
    CORNER_BOTTOM_RIGHT = 'bottom_right'
    
    FREQUENCY_HOUR = 'hour'
    FREQUENCY_MORNING = 'morning'
    FREQUENCY_NOON = 'noon'
    FREQUENCY_AFTERNOON = 'afternoon'
    FREQUENCY_EVENING = 'evening'
    FREQUENCY_NIGHT = 'night'
    FREQUENCY_DAY = 'day'
    FREQUENCY_WEEK = 'week'
    FREQUENCY_MONTH = 'month'
    
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
            'corner_position': self.corner_position,
            'background_color': self.background_color,
            'text_color': self.text_color,
            'font_size': self.font_size,
            'scroll_speed': self.scroll_speed,
            'display_duration': self.display_duration,
            'passage_limit': self.passage_limit,
            'frequency_unit': self.frequency_unit,
            'is_active': self.is_currently_active()
        }
    
    def should_display(self):
        if not self.is_currently_active():
            return False
        
        if self.passage_limit <= 0:
            return True
        
        now = datetime.utcnow()
        if self.last_passage_reset:
            should_reset = False
            if self.frequency_unit == 'hour':
                should_reset = (now - self.last_passage_reset).total_seconds() >= 3600
            elif self.frequency_unit == 'day':
                should_reset = (now - self.last_passage_reset).days >= 1
            elif self.frequency_unit == 'week':
                should_reset = (now - self.last_passage_reset).days >= 7
            elif self.frequency_unit == 'month':
                should_reset = (now - self.last_passage_reset).days >= 30
            elif self.frequency_unit in ['morning', 'noon', 'afternoon', 'evening', 'night']:
                current_hour = now.hour
                period_changed = False
                if self.frequency_unit == 'morning' and not (6 <= current_hour < 12):
                    period_changed = True
                elif self.frequency_unit == 'noon' and not (12 <= current_hour < 14):
                    period_changed = True
                elif self.frequency_unit == 'afternoon' and not (14 <= current_hour < 18):
                    period_changed = True
                elif self.frequency_unit == 'evening' and not (18 <= current_hour < 22):
                    period_changed = True
                elif self.frequency_unit == 'night' and not (current_hour >= 22 or current_hour < 6):
                    period_changed = True
                should_reset = period_changed
            
            if should_reset:
                self.current_passage_count = 0
                self.last_passage_reset = now
        else:
            self.last_passage_reset = now
        
        return self.current_passage_count < self.passage_limit
    
    def increment_passage(self):
        self.current_passage_count += 1
        if not self.last_passage_reset:
            self.last_passage_reset = datetime.utcnow()
