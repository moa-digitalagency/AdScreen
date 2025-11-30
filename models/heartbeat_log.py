from datetime import datetime
from app import db


class HeartbeatLog(db.Model):
    __tablename__ = 'heartbeat_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    screen_id = db.Column(db.Integer, db.ForeignKey('screens.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
