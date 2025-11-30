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
    commission_set_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    commission_updated_at = db.Column(db.DateTime, nullable=True)
    
    users = db.relationship('User', back_populates='organization', foreign_keys='User.organization_id')
    screens = db.relationship('Screen', back_populates='organization', cascade='all, delete-orphan')
    
    def calculate_platform_commission(self, amount):
        return round(amount * (self.commission_rate / 100), 2)
    
    def calculate_net_revenue(self, gross_amount):
        commission = self.calculate_platform_commission(gross_amount)
        return round(gross_amount - commission, 2)
