from datetime import datetime
from app import db


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
