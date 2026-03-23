from datetime import datetime
from app import db


class StatLog(db.Model):
    __tablename__ = 'stat_logs'
    __table_args__ = (
        db.Index('idx_stat_logs_played_at', 'played_at'),
        db.Index('idx_stat_logs_screen_played', 'screen_id', 'played_at'),
    )

    id = db.Column(db.Integer, primary_key=True)
    content_type = db.Column(db.String(20), nullable=False)
    content_id = db.Column(db.Integer)
    content_category = db.Column(db.String(20))
    played_at = db.Column(db.DateTime, default=datetime.utcnow)
    duration_seconds = db.Column(db.Float)
    
    screen_id = db.Column(db.Integer, db.ForeignKey('screens.id'), nullable=False)
    screen = db.relationship('Screen', back_populates='stat_logs')
