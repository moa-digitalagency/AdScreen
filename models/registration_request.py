from datetime import datetime
from app import db


class RegistrationRequest(db.Model):
    __tablename__ = 'registration_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    org_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50))
    address = db.Column(db.String(500))
    country = db.Column(db.String(5), default='FR')
    currency = db.Column(db.String(10), default='EUR')
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    notes = db.Column(db.Text)
    
    processor = db.relationship('User', backref='processed_requests')
    
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    
    @classmethod
    def get_pending_count(cls):
        return cls.query.filter_by(status=cls.STATUS_PENDING).count()
    
    @classmethod
    def get_pending_requests(cls):
        return cls.query.filter_by(status=cls.STATUS_PENDING).order_by(cls.created_at.desc()).all()
