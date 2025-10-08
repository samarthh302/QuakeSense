import requests
import logging
from datetime import datetime, timedelta
from app import db
from models import Earthquake

class EarthquakeService:
    """Service for fetching and managing earthquake data from USGS API"""
    
    USGS_API_BASE = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def fetch_and_store_earthquakes(self, days=7, min_magnitude=2.0):
        """
        Fetch earthquake data from USGS API and store in database
        
        Args:
            days: Number of days to look back
            min_magnitude: Minimum magnitude to fetch
            
        Returns:
            Number of new earthquakes stored
        """
        try:
            # Calculate date range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
            
            # USGS API parameters
            params = {
                'format': 'geojson',
                'starttime': start_time.strftime('%Y-%m-%d'),
                'endtime': end_time.strftime('%Y-%m-%d'),
                'minmagnitude': min_magnitude,
                'limit': 20000  # Maximum allowed by USGS
            }
            
            self.logger.info(f"Fetching earthquakes from {start_time} to {end_time}")
            
            # Make API request
            response = requests.get(self.USGS_API_BASE, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            features = data.get('features', [])
            
            new_count = 0
            
            for feature in features:
                try:
                    # Extract earthquake data
                    properties = feature['properties']
                    geometry = feature['geometry']
                    
                    usgs_id = feature['id']
                    magnitude = properties.get('mag')
                    region = properties.get('place', 'Unknown')
                    timestamp = datetime.fromtimestamp(properties['time'] / 1000)
                    
                    coordinates = geometry['coordinates']
                    longitude = coordinates[0]
                    latitude = coordinates[1]
                    depth = coordinates[2] if len(coordinates) > 2 else 0
                    
                    # Check if earthquake already exists
                    existing = Earthquake.query.filter_by(usgs_id=usgs_id).first()
                    if existing:
                        continue
                    
                    # Create new earthquake record
                    earthquake = Earthquake(
                        usgs_id=usgs_id,
                        latitude=latitude,
                        longitude=longitude,
                        magnitude=magnitude,
                        depth=depth,
                        region=region,
                        timestamp=timestamp
                    )
                    
                    db.session.add(earthquake)
                    new_count += 1
                    
                except Exception as e:
                    self.logger.error(f"Error processing earthquake feature: {e}")
                    db.session.rollback()
                    continue
            
            # Commit all new records
            if new_count > 0:
                try:
                    db.session.commit()
                except Exception as e:
                    self.logger.error(f"Error committing earthquakes: {e}")
                    db.session.rollback()
                    raise
            
            self.logger.info(f"Successfully stored {new_count} new earthquakes")
            return new_count
            
        except requests.RequestException as e:
            self.logger.error(f"Error fetching data from USGS API: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error in fetch_and_store_earthquakes: {e}")
            db.session.rollback()
            raise
    
    def get_earthquake_by_region(self, region_name, days=30):
        """Get earthquakes for a specific region"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return Earthquake.query.filter(
            Earthquake.region.ilike(f'%{region_name}%'),
            Earthquake.timestamp >= cutoff_date
        ).all()
    
    def get_recent_major_earthquakes(self, min_magnitude=5.0, days=7):
        """Get recent major earthquakes"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return Earthquake.query.filter(
            Earthquake.magnitude >= min_magnitude,
            Earthquake.timestamp >= cutoff_date
        ).order_by(Earthquake.magnitude.desc()).all()
    
    def get_earthquake_statistics(self):
        """Get basic earthquake statistics"""
        total = Earthquake.query.count()
        
        # Recent earthquakes (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent = Earthquake.query.filter(Earthquake.timestamp >= week_ago).count()
        
        # Magnitude distribution
        major = Earthquake.query.filter(Earthquake.magnitude >= 6.0).count()
        moderate = Earthquake.query.filter(
            Earthquake.magnitude >= 4.0,
            Earthquake.magnitude < 6.0
        ).count()
        minor = Earthquake.query.filter(Earthquake.magnitude < 4.0).count()
        
        return {
            'total': total,
            'recent': recent,
            'major': major,
            'moderate': moderate,
            'minor': minor
        }
