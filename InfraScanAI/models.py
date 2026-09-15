from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

def utc_now():
    return datetime.now(timezone.utc)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    image_path = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    damage_type = db.Column(db.String(50), nullable=True) # Pothole, Crack, No Damage
    severity = db.Column(db.String(50), nullable=True) # Low, Medium, High
    confidence = db.Column(db.Float, nullable=True) # Detection Confidence
    notes = db.Column(db.Text, nullable=True) # Citizen notes
    report_time = db.Column(db.DateTime, default=utc_now)
    status = db.Column(db.String(50), default='Pending') # Pending, Repaired

    def to_dict(self):
        return {
            'id': self.id,
            'report_id': self.report_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'image_path': self.image_path,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'damage_type': self.damage_type,
            'severity': self.severity,
            'confidence': self.confidence,
            'notes': self.notes,
            'report_time': self.report_time.isoformat(),
            'status': self.status
        }
