from datetime import datetime
import secrets
from app import db


class AdContent(db.Model):
    """Contenu publicitaire vendu par le superadmin aux annonceurs"""
    __tablename__ = 'ad_contents'
    
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(32), unique=True, nullable=False)
    name = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text)
    
    TARGET_COUNTRY = 'country'
    TARGET_CITY = 'city'
    TARGET_ORGANIZATION = 'organization'
    TARGET_SCREEN = 'screen'
    
    target_type = db.Column(db.String(20), default=TARGET_COUNTRY)
    target_country = db.Column(db.String(5), nullable=True)
    target_city = db.Column(db.String(128), nullable=True)
    target_organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True)
    target_screen_id = db.Column(db.Integer, db.ForeignKey('screens.id'), nullable=True)
    
    ORG_TYPE_ALL = 'all'
    ORG_TYPE_PAID = 'paid'
    ORG_TYPE_FREE = 'free'
    
    target_org_type = db.Column(db.String(10), default=ORG_TYPE_ALL)
    
    file_path = db.Column(db.String(500), nullable=False)
    content_type = db.Column(db.String(20), default='image')
    duration = db.Column(db.Integer, default=10)
    file_size = db.Column(db.Integer, default=0)
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    
    SCHEDULE_IMMEDIATE = 'immediate'
    SCHEDULE_PERIOD = 'period'
    
    schedule_type = db.Column(db.String(20), default=SCHEDULE_IMMEDIATE)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    
    advertiser_name = db.Column(db.String(256))
    advertiser_email = db.Column(db.String(256))
    advertiser_phone = db.Column(db.String(50))
    advertiser_company = db.Column(db.String(256))
    
    total_price = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(10), default='EUR')
    commission_rate = db.Column(db.Float, default=0.0)
    
    STATUS_ACTIVE = 'active'
    STATUS_SCHEDULED = 'scheduled'
    STATUS_EXPIRED = 'expired'
    STATUS_PAUSED = 'paused'
    STATUS_CANCELLED = 'cancelled'
    
    status = db.Column(db.String(20), default=STATUS_SCHEDULED)
    
    total_impressions = db.Column(db.Integer, default=0)
    total_duration_played = db.Column(db.Float, default=0.0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    target_organization = db.relationship('Organization', foreign_keys=[target_organization_id], backref='ad_contents')
    target_screen = db.relationship('Screen', foreign_keys=[target_screen_id], backref='ad_contents')
    creator = db.relationship('User', foreign_keys=[created_by], backref='ad_contents_created')
    
    def generate_reference(self):
        year = datetime.utcnow().year
        month = datetime.utcnow().month
        random_part = secrets.token_hex(3).upper()
        self.reference = f"PUB-{year}{month:02d}-{random_part}"
        return self.reference
    
    def is_currently_active(self):
        if self.status not in [self.STATUS_ACTIVE, self.STATUS_SCHEDULED]:
            return False
        
        now = datetime.utcnow()
        
        if self.schedule_type == self.SCHEDULE_IMMEDIATE:
            return self.status == self.STATUS_ACTIVE
        
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        
        return True
    
    def update_status(self):
        """Met à jour le statut en fonction des dates"""
        now = datetime.utcnow()
        
        if self.status in [self.STATUS_PAUSED, self.STATUS_CANCELLED]:
            return
        
        if self.schedule_type == self.SCHEDULE_PERIOD:
            if self.end_date and now > self.end_date:
                self.status = self.STATUS_EXPIRED
            elif self.start_date and now >= self.start_date:
                self.status = self.STATUS_ACTIVE
            elif self.start_date and now < self.start_date:
                self.status = self.STATUS_SCHEDULED
    
    def _matches_org_type(self, org):
        if not org:
            return False
        if self.target_org_type == self.ORG_TYPE_ALL:
            return True
        if self.target_org_type == self.ORG_TYPE_PAID:
            return org.is_paid
        if self.target_org_type == self.ORG_TYPE_FREE:
            return not org.is_paid
        return True
    
    def applies_to_screen(self, screen):
        if not self.is_currently_active():
            return False
        
        if not screen.is_active:
            return False
        
        org = screen.organization
        if not org or getattr(org, 'allow_ad_content', True) is False:
            return False
        
        if not self._matches_org_type(org):
            return False
        
        if self.target_type == self.TARGET_SCREEN:
            return self.target_screen_id == screen.id
        
        if self.target_type == self.TARGET_ORGANIZATION:
            return self.target_organization_id == screen.organization_id
        
        if self.target_type == self.TARGET_CITY:
            if org:
                return (org.country == self.target_country and 
                        org.city and 
                        org.city.lower() == self.target_city.lower() if self.target_city else False)
            return False
        
        if self.target_type == self.TARGET_COUNTRY:
            if org:
                return org.country == self.target_country
            return False
        
        return False
    
    def get_target_screens(self):
        from models import Screen, Organization
        
        if not self.is_currently_active():
            return []
        
        if self.target_type == self.TARGET_SCREEN:
            screen = Screen.query.get(self.target_screen_id)
            if screen and screen.is_active and self._matches_org_type(screen.organization):
                org = screen.organization
                if org and getattr(org, 'allow_ad_content', True) is not False:
                    return [screen]
            return []
        
        if self.target_type == self.TARGET_ORGANIZATION:
            org = Organization.query.get(self.target_organization_id)
            if org and self._matches_org_type(org) and getattr(org, 'allow_ad_content', True) is not False:
                return Screen.query.filter_by(
                    organization_id=self.target_organization_id,
                    is_active=True
                ).all()
            return []
        
        if self.target_type == self.TARGET_CITY:
            return Screen.query.join(Organization).filter(
                Organization.country == self.target_country,
                Organization.city == self.target_city,
                Organization.allow_ad_content != False,
                Screen.is_active == True
            ).all()
        
        if self.target_type == self.TARGET_COUNTRY:
            return Screen.query.join(Organization).filter(
                Organization.country == self.target_country,
                Organization.allow_ad_content != False,
                Screen.is_active == True
            ).all()
        
        return []
    
    def get_target_display(self):
        from models import Organization, Screen
        
        org_type_suffix = ""
        if self.target_org_type != self.ORG_TYPE_ALL:
            if self.target_org_type == self.ORG_TYPE_PAID:
                org_type_suffix = " (Payants)"
            else:
                org_type_suffix = " (Gratuits)"
        
        if self.target_type == self.TARGET_SCREEN:
            screen = Screen.query.get(self.target_screen_id) if self.target_screen_id else None
            return f"Écran: {screen.name}" if screen else "Écran inconnu"
        
        if self.target_type == self.TARGET_ORGANIZATION:
            org = Organization.query.get(self.target_organization_id) if self.target_organization_id else None
            return f"Établissement: {org.name}" if org else "Établissement inconnu"
        
        if self.target_type == self.TARGET_CITY:
            return f"Ville: {self.target_city or 'Non spécifiée'}{org_type_suffix}"
        
        if self.target_type == self.TARGET_COUNTRY:
            from utils.countries import get_country_name
            country_name = get_country_name(self.target_country) if self.target_country else 'Non spécifié'
            return f"Pays: {country_name}{org_type_suffix}"
        
        return "Cible inconnue"
    
    def get_status_display(self):
        labels = {
            self.STATUS_ACTIVE: 'Actif',
            self.STATUS_SCHEDULED: 'Programmé',
            self.STATUS_EXPIRED: 'Expiré',
            self.STATUS_PAUSED: 'En pause',
            self.STATUS_CANCELLED: 'Annulé'
        }
        return labels.get(self.status, self.status)
    
    def get_status_color(self):
        colors = {
            self.STATUS_ACTIVE: 'green',
            self.STATUS_SCHEDULED: 'blue',
            self.STATUS_EXPIRED: 'gray',
            self.STATUS_PAUSED: 'yellow',
            self.STATUS_CANCELLED: 'red'
        }
        return colors.get(self.status, 'gray')
    
    def get_currency_symbol(self):
        from utils.currencies import get_currency_symbol
        return get_currency_symbol(self.currency or 'EUR')
    
    def calculate_commission_for_org(self, org):
        """Calcule la commission à reverser à un établissement"""
        screens = [s for s in self.get_target_screens() if s.organization_id == org.id]
        if not screens:
            return 0.0
        
        total_screens = len(self.get_target_screens())
        if total_screens == 0:
            return 0.0
        
        org_share = len(screens) / total_screens
        org_revenue = self.total_price * org_share
        commission = org_revenue * (self.commission_rate / 100)
        
        return round(commission, 2)
    
    def to_content_dict(self):
        return {
            'id': f'ad_{self.id}',
            'type': self.content_type,
            'url': f'/{self.file_path}' if self.file_path else None,
            'duration': self.duration,
            'priority': 100,
            'category': 'ad_content',
            'name': self.name,
            'is_ad': True,
            'reference': self.reference
        }


class AdContentInvoice(db.Model):
    """Facture de commission pour contenu publicitaire"""
    __tablename__ = 'ad_content_invoices'
    
    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_VALIDATED = 'validated'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(32), unique=True, nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    ad_content_id = db.Column(db.Integer, db.ForeignKey('ad_contents.id'), nullable=False)
    
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    
    screens_count = db.Column(db.Integer, default=0)
    total_impressions = db.Column(db.Integer, default=0)
    total_duration = db.Column(db.Float, default=0.0)
    
    gross_amount = db.Column(db.Float, default=0.0)
    commission_rate = db.Column(db.Float, default=0.0)
    commission_amount = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(10), default='EUR')
    
    status = db.Column(db.String(20), default=STATUS_PENDING)
    
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime, nullable=True)
    validated_at = db.Column(db.DateTime, nullable=True)
    validated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    organization = db.relationship('Organization', backref=db.backref('ad_invoices', lazy='dynamic'))
    ad_content = db.relationship('AdContent', backref=db.backref('invoices', lazy='dynamic'))
    validator = db.relationship('User', foreign_keys=[validated_by])
    
    def generate_invoice_number(self):
        year = datetime.utcnow().year
        random_part = secrets.token_hex(4).upper()
        self.invoice_number = f"PUB-FAC-{year}-{random_part}"
        return self.invoice_number
    
    def get_currency_symbol(self):
        from utils.currencies import get_currency_symbol
        return get_currency_symbol(self.currency or 'EUR')
    
    def get_status_label(self):
        labels = {
            self.STATUS_PENDING: 'En attente',
            self.STATUS_PAID: 'Payée',
            self.STATUS_VALIDATED: 'Validée'
        }
        return labels.get(self.status, self.status)
    
    def get_status_color(self):
        colors = {
            self.STATUS_PENDING: 'yellow',
            self.STATUS_PAID: 'blue',
            self.STATUS_VALIDATED: 'green'
        }
        return colors.get(self.status, 'gray')


class AdContentStat(db.Model):
    """Statistiques de diffusion du contenu publicitaire"""
    __tablename__ = 'ad_content_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    ad_content_id = db.Column(db.Integer, db.ForeignKey('ad_contents.id'), nullable=False)
    screen_id = db.Column(db.Integer, db.ForeignKey('screens.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    
    date = db.Column(db.Date, nullable=False)
    impressions = db.Column(db.Integer, default=0)
    total_duration = db.Column(db.Float, default=0.0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    ad_content = db.relationship('AdContent', backref=db.backref('stats', lazy='dynamic'))
    screen = db.relationship('Screen', backref=db.backref('ad_stats', lazy='dynamic'))
    organization = db.relationship('Organization', backref=db.backref('ad_stats', lazy='dynamic'))
    
    __table_args__ = (
        db.UniqueConstraint('ad_content_id', 'screen_id', 'date', name='unique_ad_stat_per_day'),
    )
    
    @classmethod
    def record_impression(cls, ad_content_id, screen_id, organization_id, duration):
        from datetime import date
        today = date.today()
        
        stat = cls.query.filter_by(
            ad_content_id=ad_content_id,
            screen_id=screen_id,
            date=today
        ).first()
        
        if not stat:
            stat = cls(
                ad_content_id=ad_content_id,
                screen_id=screen_id,
                organization_id=organization_id,
                date=today,
                impressions=0,
                total_duration=0.0
            )
            db.session.add(stat)
        
        stat.impressions += 1
        stat.total_duration += duration
        
        ad_content = AdContent.query.get(ad_content_id)
        if ad_content:
            ad_content.total_impressions += 1
            ad_content.total_duration_played += duration
        
        db.session.commit()
        return stat
