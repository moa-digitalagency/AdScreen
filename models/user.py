from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


ADMIN_PERMISSIONS = [
    ('dashboard', 'Tableau de bord'),
    ('organizations', 'Établissements'),
    ('screens', 'Écrans'),
    ('broadcasts', 'Diffusion'),
    ('stats', 'Statistiques'),
    ('billing', 'Facturation'),
    ('registration_requests', 'Demandes'),
    ('settings', 'Paramètres'),
    ('users', 'Utilisateurs Admin'),
]


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), nullable=False, default='org')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    admin_permissions = db.Column(db.Text, nullable=True)
    
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True)
    organization = db.relationship('Organization', back_populates='users', foreign_keys=[organization_id])
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_superadmin(self):
        return self.role == 'superadmin'
    
    def is_admin(self):
        return self.role in ['superadmin', 'admin']
    
    def is_org_admin(self):
        return self.role == 'org'
    
    def get_permissions(self):
        if self.role == 'superadmin':
            return [p[0] for p in ADMIN_PERMISSIONS]
        if not self.admin_permissions:
            return []
        return [p.strip() for p in self.admin_permissions.split(',') if p.strip()]
    
    def set_permissions(self, permissions_list):
        self.admin_permissions = ','.join(permissions_list) if permissions_list else ''
    
    def has_permission(self, permission):
        if self.role == 'superadmin':
            return True
        return permission in self.get_permissions()
    
    @staticmethod
    def get_available_permissions():
        return ADMIN_PERMISSIONS
