from datetime import datetime
import secrets
from app import db


class Invoice(db.Model):
    __tablename__ = 'invoices'
    
    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_VALIDATED = 'validated'
    STATUS_OVERDUE = 'overdue'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(32), unique=True, nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    
    week_start_date = db.Column(db.Date, nullable=False)
    week_end_date = db.Column(db.Date, nullable=False)
    
    gross_revenue = db.Column(db.Float, default=0.0)
    commission_rate = db.Column(db.Float, nullable=False)
    commission_amount = db.Column(db.Float, default=0.0)
    net_revenue = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(10), default='EUR')
    
    bookings_count = db.Column(db.Integer, default=0)
    
    status = db.Column(db.String(20), default=STATUS_PENDING)
    
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime, nullable=True)
    validated_at = db.Column(db.DateTime, nullable=True)
    validated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    organization = db.relationship('Organization', backref=db.backref('invoices', lazy='dynamic'))
    validator = db.relationship('User', foreign_keys=[validated_by])
    payment_proofs = db.relationship('PaymentProof', back_populates='invoice', cascade='all, delete-orphan')
    
    def generate_invoice_number(self):
        year = datetime.utcnow().year
        random_part = secrets.token_hex(4).upper()
        self.invoice_number = f"FAC-{year}-{random_part}"
        return self.invoice_number
    
    def get_currency_symbol(self):
        from utils.currencies import get_currency_symbol
        return get_currency_symbol(self.currency or 'EUR')
    
    def get_status_label(self):
        labels = {
            self.STATUS_PENDING: 'En attente',
            self.STATUS_PAID: 'Payée',
            self.STATUS_VALIDATED: 'Validée',
            self.STATUS_OVERDUE: 'En retard'
        }
        return labels.get(self.status, self.status)
    
    def get_status_color(self):
        colors = {
            self.STATUS_PENDING: 'yellow',
            self.STATUS_PAID: 'blue',
            self.STATUS_VALIDATED: 'green',
            self.STATUS_OVERDUE: 'red'
        }
        return colors.get(self.status, 'gray')
    
    def has_pending_proof(self):
        return any(p.status == PaymentProof.STATUS_PENDING for p in self.payment_proofs)
    
    def get_latest_proof(self):
        if self.payment_proofs:
            return max(self.payment_proofs, key=lambda p: p.uploaded_at)
        return None


class PaymentProof(db.Model):
    __tablename__ = 'payment_proofs'
    
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    
    file_path = db.Column(db.String(512), nullable=False)
    file_name = db.Column(db.String(256), nullable=False)
    file_size = db.Column(db.Integer, default=0)
    
    notes = db.Column(db.Text, nullable=True)
    
    status = db.Column(db.String(20), default=STATUS_PENDING)
    
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    review_notes = db.Column(db.Text, nullable=True)
    
    invoice = db.relationship('Invoice', back_populates='payment_proofs')
    uploader = db.relationship('User', foreign_keys=[uploaded_by])
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])
    
    def get_status_label(self):
        labels = {
            self.STATUS_PENDING: 'En attente de validation',
            self.STATUS_APPROVED: 'Approuvée',
            self.STATUS_REJECTED: 'Refusée'
        }
        return labels.get(self.status, self.status)
    
    def get_status_color(self):
        colors = {
            self.STATUS_PENDING: 'yellow',
            self.STATUS_APPROVED: 'green',
            self.STATUS_REJECTED: 'red'
        }
        return colors.get(self.status, 'gray')
