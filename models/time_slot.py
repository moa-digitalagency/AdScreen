from app import db


class TimeSlot(db.Model):
    __tablename__ = 'time_slots'
    
    id = db.Column(db.Integer, primary_key=True)
    content_type = db.Column(db.String(20), nullable=False)
    duration_seconds = db.Column(db.Integer, nullable=False)
    price_per_play = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    screen_id = db.Column(db.Integer, db.ForeignKey('screens.id'), nullable=False)
    screen = db.relationship('Screen', back_populates='time_slots')
    
    def get_calculated_price(self):
        """Get price calculated from screen's price_per_minute.
        Formula: (duration_seconds / 60) * price_per_minute
        """
        if self.screen:
            return self.screen.calculate_slot_price(self.duration_seconds)
        return self.price_per_play
    
    def recalculate_price(self):
        """Update price_per_play based on screen's price_per_minute."""
        if self.screen:
            self.price_per_play = self.screen.calculate_slot_price(self.duration_seconds)
        return self.price_per_play
