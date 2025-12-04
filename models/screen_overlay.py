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
    corner_size = db.Column(db.Integer, default=15)
    position_mode = db.Column(db.String(20), default='linear')
    
    image_width = db.Column(db.Integer, default=0)
    image_height = db.Column(db.Integer, default=0)
    image_width_percent = db.Column(db.Float, default=20.0)
    image_pos_x = db.Column(db.Integer, default=0)
    image_pos_y = db.Column(db.Integer, default=0)
    image_opacity = db.Column(db.Float, default=1.0)
    
    frequency_type = db.Column(db.String(20), default='duration')
    display_duration = db.Column(db.Integer, default=10)
    passage_limit = db.Column(db.Integer, default=0)
    frequency_unit = db.Column(db.String(20), default='day')
    current_passage_count = db.Column(db.Integer, default=0)
    last_passage_reset = db.Column(db.DateTime)
    
    priority = db.Column(db.Integer, default=50)
    
    SOURCE_LOCAL = 'local'
    SOURCE_BROADCAST = 'broadcast'
    source = db.Column(db.String(20), default=SOURCE_LOCAL)
    source_broadcast_id = db.Column(db.Integer, db.ForeignKey('broadcasts.id'), nullable=True)
    
    is_paused = db.Column(db.Boolean, default=False)
    paused_by_broadcast_id = db.Column(db.Integer, nullable=True)
    paused_at = db.Column(db.DateTime, nullable=True)
    
    is_active = db.Column(db.Boolean, default=True)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    screen = db.relationship('Screen', back_populates='overlays')
    source_broadcast = db.relationship('Broadcast', foreign_keys=[source_broadcast_id], backref='created_overlays')
    
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
    
    FREQUENCY_TYPE_DURATION = 'duration'
    FREQUENCY_TYPE_PASSAGE = 'passage'
    
    FREQUENCY_MORNING = 'morning'
    FREQUENCY_NOON = 'noon'
    FREQUENCY_AFTERNOON = 'afternoon'
    FREQUENCY_EVENING = 'evening'
    FREQUENCY_NIGHT = 'night'
    FREQUENCY_DAY = 'day'
    FREQUENCY_WEEK = 'week'
    
    def is_currently_active(self):
        if not self.is_active:
            return False
        
        if self.is_paused:
            return False
        
        now = datetime.utcnow()
        if self.start_time and now < self.start_time:
            return False
        if self.end_time and now > self.end_time:
            return False
        
        return True
    
    def pause(self, by_broadcast_id=None):
        self.is_paused = True
        self.paused_by_broadcast_id = by_broadcast_id
        self.paused_at = datetime.utcnow()
    
    def resume(self):
        self.is_paused = False
        self.paused_by_broadcast_id = None
        self.paused_at = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.overlay_type,
            'message': self.message,
            'image_path': self.image_path,
            'position': self.position,
            'position_mode': self.position_mode,
            'corner_position': self.corner_position,
            'corner_size': self.corner_size,
            'background_color': self.background_color,
            'text_color': self.text_color,
            'font_size': self.font_size,
            'scroll_speed': self.scroll_speed,
            'frequency_type': self.frequency_type,
            'display_duration': self.display_duration,
            'passage_limit': self.passage_limit,
            'frequency_unit': self.frequency_unit,
            'image_width': self.image_width,
            'image_height': self.image_height,
            'image_width_percent': self.image_width_percent,
            'image_pos_x': self.image_pos_x,
            'image_pos_y': self.image_pos_y,
            'image_opacity': self.image_opacity,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'is_active': self.is_currently_active(),
            'priority': self.priority,
            'source': self.source,
            'is_paused': self.is_paused,
            'is_broadcast': self.source == self.SOURCE_BROADCAST
        }
    
    def _get_current_period(self, hour):
        if 6 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 14:
            return 'noon'
        elif 14 <= hour < 18:
            return 'afternoon'
        elif 18 <= hour < 22:
            return 'evening'
        else:
            return 'night'
    
    def _should_reset_counter(self, now):
        if not self.last_passage_reset:
            return True
        
        if self.frequency_unit == 'day':
            return now.date() > self.last_passage_reset.date()
        elif self.frequency_unit == 'week':
            days_diff = (now - self.last_passage_reset).days
            return days_diff >= 7 or now.isocalendar()[1] != self.last_passage_reset.isocalendar()[1]
        elif self.frequency_unit in ['morning', 'noon', 'afternoon', 'evening', 'night']:
            current_period = self._get_current_period(now.hour)
            last_period = self._get_current_period(self.last_passage_reset.hour)
            if now.date() > self.last_passage_reset.date():
                return True
            return current_period == self.frequency_unit and last_period != self.frequency_unit
        
        return False
    
    def should_display(self):
        if not self.is_currently_active():
            return False
        
        if self.frequency_type == 'duration':
            return True
        
        if self.frequency_type == 'passage' and self.passage_limit <= 0:
            return True
        
        now = datetime.utcnow()
        
        if self._should_reset_counter(now):
            self.current_passage_count = 0
            self.last_passage_reset = now
        
        return self.current_passage_count < self.passage_limit
    
    def increment_passage(self):
        self.current_passage_count += 1
        if not self.last_passage_reset:
            self.last_passage_reset = datetime.utcnow()
