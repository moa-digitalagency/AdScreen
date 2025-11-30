from datetime import datetime
import secrets
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
    unique_code = db.Column(db.String(32), unique=True)
    password_hash = db.Column(db.String(256))
    last_heartbeat = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='offline')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    organization = db.relationship('Organization', back_populates='screens')
    
    time_slots = db.relationship('TimeSlot', back_populates='screen', cascade='all, delete-orphan')
    time_periods = db.relationship('TimePeriod', back_populates='screen', cascade='all, delete-orphan')
    contents = db.relationship('Content', back_populates='screen', cascade='all, delete-orphan')
    bookings = db.relationship('Booking', back_populates='screen', cascade='all, delete-orphan')
    fillers = db.relationship('Filler', back_populates='screen', cascade='all, delete-orphan')
    internal_contents = db.relationship('InternalContent', back_populates='screen', cascade='all, delete-orphan')
    stat_logs = db.relationship('StatLog', back_populates='screen', cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.unique_code:
            self.unique_code = secrets.token_urlsafe(16)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_aspect_ratio(self):
        from math import gcd
        g = gcd(self.resolution_width, self.resolution_height)
        return f"{self.resolution_width // g}:{self.resolution_height // g}"
