from datetime import datetime
from app import db


class SiteSetting(db.Model):
    __tablename__ = 'site_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    value_type = db.Column(db.String(20), default='string')
    category = db.Column(db.String(50), default='general')
    description = db.Column(db.String(255))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get(cls, key, default=None):
        setting = cls.query.filter_by(key=key).first()
        if setting is None:
            return default
        
        if setting.value_type == 'boolean':
            return setting.value.lower() in ('true', '1', 'yes')
        elif setting.value_type == 'integer':
            try:
                return int(setting.value)
            except (ValueError, TypeError):
                return default
        elif setting.value_type == 'float':
            try:
                return float(setting.value)
            except (ValueError, TypeError):
                return default
        return setting.value
    
    @classmethod
    def set(cls, key, value, value_type='string', category='general', description=None):
        setting = cls.query.filter_by(key=key).first()
        if setting is None:
            setting = cls(key=key, category=category)
            db.session.add(setting)
        
        setting.value = str(value) if value is not None else ''
        setting.value_type = value_type
        if description:
            setting.description = description
        
        db.session.commit()
        return setting
    
    @classmethod
    def get_all_by_category(cls, category):
        return cls.query.filter_by(category=category).all()
    
    @classmethod
    def get_seo_settings(cls):
        return {
            'site_title': cls.get('site_title', 'AdScreen'),
            'site_description': cls.get('site_description', 'Plateforme de location d\'écrans publicitaires'),
            'meta_keywords': cls.get('meta_keywords', ''),
            'og_image': cls.get('og_image', ''),
            'google_analytics_id': cls.get('google_analytics_id', ''),
        }
    
    @classmethod
    def get_platform_settings(cls):
        return {
            'default_commission_rate': cls.get('default_commission_rate', 10.0),
            'min_commission_rate': cls.get('min_commission_rate', 5.0),
            'max_commission_rate': cls.get('max_commission_rate', 30.0),
            'platform_name': cls.get('platform_name', 'AdScreen'),
            'support_email': cls.get('support_email', ''),
            'maintenance_mode': cls.get('maintenance_mode', False),
        }
