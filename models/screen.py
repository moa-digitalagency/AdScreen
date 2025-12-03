from datetime import datetime
import secrets
import string
from app import db
from werkzeug.security import generate_password_hash, check_password_hash


class Screen(db.Model):
    __tablename__ = 'screens'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    location = db.Column(db.String(256))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    resolution_width = db.Column(db.Integer, default=1920)
    resolution_height = db.Column(db.Integer, default=1080)
    orientation = db.Column(db.String(20), default='landscape')
    accepts_images = db.Column(db.Boolean, default=True)
    accepts_videos = db.Column(db.Boolean, default=True)
    max_file_size_mb = db.Column(db.Integer, default=50)
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    price_per_minute = db.Column(db.Float, default=2.0)  # Base price per minute for auto-calculating slot prices
    unique_code = db.Column(db.String(6), unique=True)
    password_hash = db.Column(db.String(256))
    last_heartbeat = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='offline')
    screen_image = db.Column(db.String(512), nullable=True)  # Optional image of the physical screen
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    iptv_enabled = db.Column(db.Boolean, default=False)
    current_mode = db.Column(db.String(20), default='playlist')  # 'playlist' or 'iptv'
    current_iptv_channel = db.Column(db.String(512), nullable=True)
    current_iptv_channel_name = db.Column(db.String(256), nullable=True)
    
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    organization = db.relationship('Organization', back_populates='screens')
    
    time_slots = db.relationship('TimeSlot', back_populates='screen', cascade='all, delete-orphan')
    time_periods = db.relationship('TimePeriod', back_populates='screen', cascade='all, delete-orphan')
    contents = db.relationship('Content', back_populates='screen', cascade='all, delete-orphan')
    bookings = db.relationship('Booking', back_populates='screen', cascade='all, delete-orphan')
    fillers = db.relationship('Filler', back_populates='screen', cascade='all, delete-orphan')
    internal_contents = db.relationship('InternalContent', back_populates='screen', cascade='all, delete-orphan')
    stat_logs = db.relationship('StatLog', back_populates='screen', cascade='all, delete-orphan')
    overlays = db.relationship('ScreenOverlay', back_populates='screen', cascade='all, delete-orphan')
    
    @staticmethod
    def generate_unique_code():
        chars = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(secrets.choice(chars) for _ in range(6))
            existing = Screen.query.filter_by(unique_code=code).first()
            if not existing:
                return code
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.unique_code:
            self.unique_code = Screen.generate_unique_code()
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_aspect_ratio(self):
        from math import gcd
        g = gcd(self.resolution_width, self.resolution_height)
        return f"{self.resolution_width // g}:{self.resolution_height // g}"
    
    def calculate_slot_price(self, duration_seconds):
        """Calculate slot price based on duration and price_per_minute.
        Formula: (duration_seconds / 60) * price_per_minute
        Example: 15s at 2€/min = (15/60) * 2 = 0.50€
        """
        return round((duration_seconds / 60) * (self.price_per_minute or 2.0), 2)
    
    def get_currency_symbol(self):
        """Get currency symbol from organization."""
        if self.organization:
            return self.organization.get_currency_symbol()
        return '€'
    
    def get_currency(self):
        """Get currency code from organization."""
        if self.organization:
            return self.organization.currency or 'EUR'
        return 'EUR'
    
    def get_iptv_url_hls(self):
        """Transform MPEG-TS URL to HLS format for better browser compatibility.
        Changes output=mpegts to output=m3u8 for IPTV providers that support both formats.
        """
        import re
        if not self.current_iptv_channel:
            return None
        
        url = self.current_iptv_channel
        url = re.sub(r'output=mpegts', 'output=m3u8', url, flags=re.IGNORECASE)
        url = re.sub(r'output=ts', 'output=m3u8', url, flags=re.IGNORECASE)
        return url
