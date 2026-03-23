from datetime import datetime, timedelta
from app import db
import logging

logger = logging.getLogger(__name__)


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

    @classmethod
    def cleanup_old_logs(cls, days_to_keep=30):
        """Delete StatLog entries older than specified days (default: 30 days)"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            deleted_count = cls.query.filter(cls.played_at < cutoff_date).delete()
            db.session.commit()
            logger.info(f"Cleaned up {deleted_count} old StatLog entries (older than {days_to_keep} days)")
            return deleted_count
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error cleaning up StatLog: {e}")
            return 0
