from datetime import datetime
import secrets
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), nullable=False, default='org')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True)
    organization = db.relationship('Organization', back_populates='users')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_superadmin(self):
        return self.role == 'superadmin'
    
    def is_org_admin(self):
        return self.role == 'org'


class Organization(db.Model):
    __tablename__ = 'organizations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(256))
    is_active = db.Column(db.Boolean, default=True)
    commission_rate = db.Column(db.Float, default=10.0)
    subscription_plan = db.Column(db.String(50), default='basic')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    users = db.relationship('User', back_populates='organization')
    screens = db.relationship('Screen', back_populates='organization', cascade='all, delete-orphan')


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


class TimeSlot(db.Model):
    __tablename__ = 'time_slots'
    
    id = db.Column(db.Integer, primary_key=True)
    content_type = db.Column(db.String(20), nullable=False)
    duration_seconds = db.Column(db.Integer, nullable=False)
    price_per_play = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    screen_id = db.Column(db.Integer, db.ForeignKey('screens.id'), nullable=False)
    screen = db.relationship('Screen', back_populates='time_slots')


class TimePeriod(db.Model):
    __tablename__ = 'time_periods'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    start_hour = db.Column(db.Integer, nullable=False)
    end_hour = db.Column(db.Integer, nullable=False)
    price_multiplier = db.Column(db.Float, default=1.0)
    
    screen_id = db.Column(db.Integer, db.ForeignKey('screens.id'), nullable=False)
    screen = db.relationship('Screen', back_populates='time_periods')


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


class Booking(db.Model):
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    slot_duration = db.Column(db.Integer, nullable=False)
    time_period_id = db.Column(db.Integer, db.ForeignKey('time_periods.id'))
    num_plays = db.Column(db.Integer, nullable=False)
    plays_completed = db.Column(db.Integer, default=0)
    price_per_play = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    payment_status = db.Column(db.String(20), default='pending')
    payment_reference = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    screen_id = db.Column(db.Integer, db.ForeignKey('screens.id'), nullable=False)
    screen = db.relationship('Screen', back_populates='bookings')
    
    content_id = db.Column(db.Integer, db.ForeignKey('contents.id'), nullable=False)
    content = db.relationship('Content', back_populates='booking')
    
    time_period = db.relationship('TimePeriod')


class Filler(db.Model):
    __tablename__ = 'fillers'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), nullable=False)
    content_type = db.Column(db.String(20), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    duration_seconds = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    screen_id = db.Column(db.Integer, db.ForeignKey('screens.id'), nullable=False)
    screen = db.relationship('Screen', back_populates='fillers')


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


class StatLog(db.Model):
    __tablename__ = 'stat_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    content_type = db.Column(db.String(20), nullable=False)
    content_id = db.Column(db.Integer)
    content_category = db.Column(db.String(20))
    played_at = db.Column(db.DateTime, default=datetime.utcnow)
    duration_seconds = db.Column(db.Float)
    
    screen_id = db.Column(db.Integer, db.ForeignKey('screens.id'), nullable=False)
    screen = db.relationship('Screen', back_populates='stat_logs')


class HeartbeatLog(db.Model):
    __tablename__ = 'heartbeat_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    screen_id = db.Column(db.Integer, db.ForeignKey('screens.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
