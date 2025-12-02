from app import db
from datetime import datetime


class Broadcast(db.Model):
    __tablename__ = 'broadcasts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    
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
    
    BROADCAST_TYPE_OVERLAY = 'overlay'
    BROADCAST_TYPE_CONTENT = 'content'
    
    broadcast_type = db.Column(db.String(20), default=BROADCAST_TYPE_OVERLAY)
    
    OVERLAY_TYPE_TICKER = 'ticker'
    OVERLAY_TYPE_IMAGE = 'image'
    OVERLAY_TYPE_CORNER = 'corner'
    
    overlay_type = db.Column(db.String(20), default=OVERLAY_TYPE_TICKER)
    overlay_message = db.Column(db.Text)
    overlay_image_path = db.Column(db.String(500))
    overlay_position = db.Column(db.String(20), default='footer')
    overlay_corner_position = db.Column(db.String(20), default='top_left')
    overlay_background_color = db.Column(db.String(20), default='#000000')
    overlay_text_color = db.Column(db.String(20), default='#FFFFFF')
    overlay_font_size = db.Column(db.Integer, default=24)
    overlay_scroll_speed = db.Column(db.Integer, default=50)
    overlay_corner_size = db.Column(db.Integer, default=15)
    overlay_position_mode = db.Column(db.String(20), default='linear')
    overlay_image_width_percent = db.Column(db.Float, default=20.0)
    overlay_image_pos_x = db.Column(db.Integer, default=0)
    overlay_image_pos_y = db.Column(db.Integer, default=0)
    overlay_image_opacity = db.Column(db.Float, default=1.0)
    
    content_file_path = db.Column(db.String(500))
    content_type = db.Column(db.String(20), default='image')
    content_duration = db.Column(db.Integer, default=10)
    content_priority = db.Column(db.Integer, default=200)
    
    is_active = db.Column(db.Boolean, default=True)
    start_datetime = db.Column(db.DateTime)
    end_datetime = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    target_organization = db.relationship('Organization', foreign_keys=[target_organization_id], backref='broadcasts')
    target_screen = db.relationship('Screen', foreign_keys=[target_screen_id], backref='broadcasts')
    creator = db.relationship('User', foreign_keys=[created_by], backref='broadcasts_created')
    
    def is_currently_active(self):
        if not self.is_active:
            return False
        
        now = datetime.utcnow()
        if self.start_datetime and now < self.start_datetime:
            return False
        if self.end_datetime and now > self.end_datetime:
            return False
        
        return True
    
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
    
    def _apply_org_type_filter(self, query, Organization):
        if self.target_org_type == self.ORG_TYPE_PAID:
            return query.filter(Organization.is_paid == True)
        elif self.target_org_type == self.ORG_TYPE_FREE:
            return query.filter(Organization.is_paid == False)
        return query
    
    def get_target_screens(self):
        from models import Screen, Organization
        
        if not self.is_currently_active():
            return []
        
        if self.target_type == self.TARGET_SCREEN:
            screen = Screen.query.get(self.target_screen_id)
            if screen and screen.is_active and self._matches_org_type(screen.organization):
                return [screen]
            return []
        
        if self.target_type == self.TARGET_ORGANIZATION:
            org = Organization.query.get(self.target_organization_id)
            if org and self._matches_org_type(org):
                return Screen.query.filter_by(
                    organization_id=self.target_organization_id,
                    is_active=True
                ).all()
            return []
        
        if self.target_type == self.TARGET_CITY:
            query = Screen.query.join(Organization).filter(
                Organization.country == self.target_country,
                Organization.city == self.target_city,
                Screen.is_active == True
            )
            return self._apply_org_type_filter(query, Organization).all()
        
        if self.target_type == self.TARGET_COUNTRY:
            query = Screen.query.join(Organization).filter(
                Organization.country == self.target_country,
                Screen.is_active == True
            )
            return self._apply_org_type_filter(query, Organization).all()
        
        return []
    
    def get_org_type_display(self):
        if self.target_org_type == self.ORG_TYPE_PAID:
            return "Payants uniquement"
        elif self.target_org_type == self.ORG_TYPE_FREE:
            return "Gratuits uniquement"
        return "Tous"
    
    def get_target_display(self):
        from models import Organization, Screen
        
        org_type_suffix = ""
        if self.target_org_type != self.ORG_TYPE_ALL:
            org_type_suffix = f" ({self.get_org_type_display()})"
        
        if self.target_type == self.TARGET_SCREEN:
            screen = Screen.query.get(self.target_screen_id) if self.target_screen_id else None
            return f"Écran: {screen.name}" if screen else "Écran inconnu"
        
        if self.target_type == self.TARGET_ORGANIZATION:
            org = Organization.query.get(self.target_organization_id) if self.target_organization_id else None
            return f"Établissement: {org.name}" if org else "Établissement inconnu"
        
        if self.target_type == self.TARGET_CITY:
            return f"Ville: {self.target_city or 'Non spécifiée'} ({self.target_country or 'Non spécifié'}){org_type_suffix}"
        
        if self.target_type == self.TARGET_COUNTRY:
            from utils.countries import get_country_name
            country_name = get_country_name(self.target_country) if self.target_country else 'Non spécifié'
            return f"Pays: {country_name}{org_type_suffix}"
        
        return "Cible inconnue"
    
    def to_overlay_dict(self):
        result = {
            'id': f'broadcast_{self.id}',
            'type': self.overlay_type,
            'message': self.overlay_message,
            'image_path': self.overlay_image_path,
            'position': self.overlay_position,
            'position_mode': self.overlay_position_mode,
            'corner_position': self.overlay_corner_position,
            'corner_size': self.overlay_corner_size,
            'background_color': self.overlay_background_color,
            'text_color': self.overlay_text_color,
            'font_size': self.overlay_font_size,
            'scroll_speed': self.overlay_scroll_speed,
            'image_width_percent': self.overlay_image_width_percent,
            'image_pos_x': self.overlay_image_pos_x,
            'image_pos_y': self.overlay_image_pos_y,
            'image_opacity': self.overlay_image_opacity,
            'frequency_type': 'duration',
            'display_duration': 0,
            'passage_limit': 0,
            'frequency_unit': 'day',
            'image_width': 0,
            'image_height': 0,
            'start_time': self.start_datetime.isoformat() if self.start_datetime else None,
            'end_time': self.end_datetime.isoformat() if self.end_datetime else None,
            'is_active': True,
            'is_broadcast': True
        }
        return result
    
    def to_content_dict(self):
        return {
            'id': f'broadcast_{self.id}',
            'type': self.content_type,
            'url': f'/{self.content_file_path}' if self.content_file_path else None,
            'duration': self.content_duration,
            'priority': self.content_priority,
            'category': 'broadcast',
            'name': self.name,
            'is_broadcast': True
        }
