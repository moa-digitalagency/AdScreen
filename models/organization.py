from datetime import datetime
from app import db


class Organization(db.Model):
    __tablename__ = 'organizations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(256))
    country = db.Column(db.String(5), default='FR')
    city = db.Column(db.String(128), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_paid = db.Column(db.Boolean, default=True)
    commission_rate = db.Column(db.Float, default=10.0)
    subscription_plan = db.Column(db.String(50), default='basic')
    currency = db.Column(db.String(10), default='EUR')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    commission_set_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    commission_updated_at = db.Column(db.DateTime, nullable=True)
    
    business_name = db.Column(db.String(256), nullable=True)
    registration_number_label = db.Column(db.String(100), nullable=True)  # Custom label for registration number (e.g., SIRET, NIF, Tax ID)
    business_registration_number = db.Column(db.String(100), nullable=True)
    vat_rate = db.Column(db.Float, default=0.0)
    vat_number = db.Column(db.String(50), nullable=True)
    timezone = db.Column(db.String(50), default='UTC')
    
    has_iptv = db.Column(db.Boolean, default=False)
    iptv_m3u_url = db.Column(db.Text, nullable=True)
    
    allow_ad_content = db.Column(db.Boolean, default=True)
    
    users = db.relationship('User', back_populates='organization', foreign_keys='User.organization_id')
    screens = db.relationship('Screen', back_populates='organization', cascade='all, delete-orphan')
    
    def get_currency_symbol(self):
        from utils.currencies import get_currency_symbol
        return get_currency_symbol(self.currency or 'EUR')
    
    def get_currency_info(self):
        from utils.currencies import get_currency_by_code
        return get_currency_by_code(self.currency or 'EUR')
    
    def calculate_platform_commission(self, amount):
        return round(amount * (self.commission_rate / 100), 2)
    
    def calculate_net_revenue(self, gross_amount):
        commission = self.calculate_platform_commission(gross_amount)
        return round(gross_amount - commission, 2)
    
    def calculate_vat(self, amount):
        if not self.vat_rate or self.vat_rate <= 0:
            return 0
        return round(amount * (self.vat_rate / 100), 2)
    
    def calculate_price_with_vat(self, amount):
        vat = self.calculate_vat(amount)
        return round(amount + vat, 2)
    
    def get_business_info(self):
        return {
            'business_name': self.business_name or self.name,
            'registration_number': self.business_registration_number or '',
            'vat_number': self.vat_number or '',
            'vat_rate': self.vat_rate or 0,
            'address': self.address or '',
            'phone': self.phone or '',
            'email': self.email or ''
        }
    
    def has_business_info(self):
        return bool(self.business_name or self.business_registration_number)
    
    def can_use_booking(self):
        return self.is_paid
    
    def can_use_billing(self):
        return self.is_paid
    
    def can_use_paid_features(self):
        return self.is_paid
    
    def get_available_features(self):
        features = ['internal', 'overlay', 'broadcast']
        if self.is_paid:
            features.extend(['booking', 'billing', 'slots', 'periods'])
        return features
