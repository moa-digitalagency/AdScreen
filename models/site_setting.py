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
            'site_title': cls.get('site_title', 'Shabaka AdScreen'),
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
            'platform_name': cls.get('platform_name', 'Shabaka AdScreen'),
            'support_email': cls.get('support_email', ''),
            'maintenance_mode': cls.get('maintenance_mode', False),
        }
    
    @classmethod
    def get_ad_content_settings(cls):
        """Paramètres pour le contenu publicitaire vendu par le superadmin"""
        return {
            'ad_commission_rate': cls.get('ad_commission_rate', 30.0),
            'ad_min_price_per_day': cls.get('ad_min_price_per_day', 10.0),
            'ad_auto_invoice': cls.get('ad_auto_invoice', True),
            'ad_invoice_frequency': cls.get('ad_invoice_frequency', 'monthly'),
        }
    
    @classmethod
    def set_ad_content_settings(cls, settings):
        """Sauvegarde les paramètres du contenu publicitaire"""
        if 'ad_commission_rate' in settings:
            cls.set('ad_commission_rate', settings['ad_commission_rate'], 'float', 'ad_content', 'Taux de commission pub (%)')
        if 'ad_min_price_per_day' in settings:
            cls.set('ad_min_price_per_day', settings['ad_min_price_per_day'], 'float', 'ad_content', 'Prix minimum par jour')
        if 'ad_auto_invoice' in settings:
            cls.set('ad_auto_invoice', settings['ad_auto_invoice'], 'boolean', 'ad_content', 'Facturation automatique')
        if 'ad_invoice_frequency' in settings:
            cls.set('ad_invoice_frequency', settings['ad_invoice_frequency'], 'string', 'ad_content', 'Fréquence de facturation')
