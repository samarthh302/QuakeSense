from app import db
from datetime import datetime
from sqlalchemy import Index

class Earthquake(db.Model):
    __tablename__ = 'earthquakes'
    
    id = db.Column(db.Integer, primary_key=True)
    usgs_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    magnitude = db.Column(db.Float, nullable=False)
    depth = db.Column(db.Float, nullable=False)
    region = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Add indexes for common queries
    __table_args__ = (
        Index('idx_magnitude', 'magnitude'),
        Index('idx_timestamp', 'timestamp'),
        Index('idx_location', 'latitude', 'longitude'),
        Index('idx_region', 'region'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'usgs_id': self.usgs_id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'magnitude': self.magnitude,
            'depth': self.depth,
            'region': self.region,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def get_magnitude_color(self):
        """Return color code based on magnitude"""
        if self.magnitude < 4.0:
            return 'green'
        elif self.magnitude < 6.0:
            return 'yellow'
        else:
            return 'red'
    
    def __repr__(self):
        return f'<Earthquake {self.usgs_id}: M{self.magnitude} at {self.region}>'

class RiskZone(db.Model):
    __tablename__ = 'risk_zones'
    
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.Float, nullable=False)  # 0.0 to 1.0
    region_name = db.Column(db.String(200))
    earthquake_count = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'risk_level': self.risk_level,
            'region_name': self.region_name,
            'earthquake_count': self.earthquake_count,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
    
    def __repr__(self):
        return f'<RiskZone {self.region_name}: Risk {self.risk_level}>'
