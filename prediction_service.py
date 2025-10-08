import logging
from datetime import datetime, timedelta
from collections import defaultdict
import math
from app import db
from models import Earthquake, RiskZone
from sqlalchemy import func

class PredictionService:
    """Service for earthquake prediction and risk assessment"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def update_risk_zones(self, grid_size=2.0):
        """
        Update risk zones based on historical earthquake activity
        
        Args:
            grid_size: Size of grid cells in degrees
            
        Returns:
            Number of risk zones updated
        """
        try:
            # Clear existing risk zones
            RiskZone.query.delete()
            
            # Get historical earthquake data (last 365 days)
            cutoff_date = datetime.utcnow() - timedelta(days=365)
            earthquakes = Earthquake.query.filter(
                Earthquake.timestamp >= cutoff_date
            ).all()
            
            if not earthquakes:
                self.logger.warning("No earthquake data available for risk assessment")
                return 0
            
            # Group earthquakes into grid cells
            grid_cells = defaultdict(list)
            
            for eq in earthquakes:
                # Calculate grid cell coordinates
                lat_cell = math.floor(eq.latitude / grid_size) * grid_size
                lon_cell = math.floor(eq.longitude / grid_size) * grid_size
                
                grid_cells[(lat_cell, lon_cell)].append(eq)
            
            zones_created = 0
            
            for (lat, lon), cell_earthquakes in grid_cells.items():
                if len(cell_earthquakes) < 3:  # Minimum earthquakes for risk assessment
                    continue
                
                # Calculate risk metrics
                risk_level = self._calculate_risk_level(cell_earthquakes)
                
                # Only create zones with significant risk
                if risk_level > 0.3:
                    # Get representative region name
                    region_name = self._get_representative_region(cell_earthquakes)
                    
                    # Calculate center point of grid cell
                    center_lat = lat + grid_size / 2
                    center_lon = lon + grid_size / 2
                    
                    risk_zone = RiskZone(
                        latitude=center_lat,
                        longitude=center_lon,
                        risk_level=risk_level,
                        region_name=region_name,
                        earthquake_count=len(cell_earthquakes),
                        last_updated=datetime.utcnow()
                    )
                    
                    db.session.add(risk_zone)
                    zones_created += 1
            
            db.session.commit()
            self.logger.info(f"Created {zones_created} risk zones")
            return zones_created
            
        except Exception as e:
            self.logger.error(f"Error updating risk zones: {e}")
            db.session.rollback()
            raise
    
    def _calculate_risk_level(self, earthquakes):
        """
        Calculate risk level for a group of earthquakes
        
        Risk factors considered:
        - Frequency of earthquakes
        - Average magnitude
        - Recent activity
        - Depth patterns
        """
        if not earthquakes:
            return 0.0
        
        # Frequency factor (earthquakes per month)
        frequency = len(earthquakes) / 12.0  # Assuming 1 year of data
        frequency_score = min(frequency / 10.0, 1.0)  # Normalize to 0-1
        
        # Magnitude factor
        magnitudes = [eq.magnitude for eq in earthquakes if eq.magnitude]
        if magnitudes:
            avg_magnitude = sum(magnitudes) / len(magnitudes)
            max_magnitude = max(magnitudes)
            magnitude_score = min((avg_magnitude - 2.0) / 6.0, 1.0)  # Scale 2-8 to 0-1
            magnitude_score = max(magnitude_score, 0.0)
            
            # Boost for high maximum magnitude
            if max_magnitude >= 6.0:
                magnitude_score *= 1.5
        else:
            magnitude_score = 0.0
        
        # Recent activity factor (more recent = higher risk)
        now = datetime.utcnow()
        recent_earthquakes = [
            eq for eq in earthquakes 
            if (now - eq.timestamp).days <= 90
        ]
        recency_score = len(recent_earthquakes) / len(earthquakes)
        
        # Depth factor (shallower earthquakes are more dangerous)
        depths = [eq.depth for eq in earthquakes if eq.depth is not None]
        if depths:
            avg_depth = sum(depths) / len(depths)
            # Shallow earthquakes (< 70km) are more dangerous
            depth_score = max(0, (70 - avg_depth) / 70) if avg_depth > 0 else 0.5
        else:
            depth_score = 0.5
        
        # Combine factors with weights
        risk_level = (
            frequency_score * 0.3 +
            magnitude_score * 0.4 +
            recency_score * 0.2 +
            depth_score * 0.1
        )
        
        return min(risk_level, 1.0)
    
    def _get_representative_region(self, earthquakes):
        """Get the most common region name from a group of earthquakes"""
        region_counts = defaultdict(int)
        
        for eq in earthquakes:
            if eq.region:
                region_counts[eq.region] += 1
        
        if region_counts:
            return max(region_counts.items(), key=lambda x: x[1])[0]
        
        return "Unknown Region"
    
    def get_high_risk_regions(self, min_risk=0.7):
        """Get regions with high earthquake risk"""
        return RiskZone.query.filter(
            RiskZone.risk_level >= min_risk
        ).order_by(RiskZone.risk_level.desc()).all()
    
    def predict_next_earthquake_probability(self, latitude, longitude, radius_km=100):
        """
        Predict probability of earthquake in a region
        Based on historical patterns and current seismic activity
        """
        try:
            # Convert radius to approximate degrees
            radius_deg = radius_km / 111.0  # Rough conversion
            
            # Get historical earthquakes in the region
            earthquakes = Earthquake.query.filter(
                func.abs(Earthquake.latitude - latitude) <= radius_deg,
                func.abs(Earthquake.longitude - longitude) <= radius_deg
            ).all()
            
            if len(earthquakes) < 5:
                return {
                    'probability': 0.1,
                    'confidence': 'low',
                    'based_on_events': len(earthquakes)
                }
            
            # Analyze patterns
            recent_earthquakes = [
                eq for eq in earthquakes
                if (datetime.utcnow() - eq.timestamp).days <= 30
            ]
            
            # Simple probability calculation based on historical frequency
            historical_frequency = len(earthquakes) / 365.0  # earthquakes per day
            recent_activity_boost = len(recent_earthquakes) * 0.1
            
            probability = min(historical_frequency + recent_activity_boost, 1.0)
            
            # Determine confidence level
            if len(earthquakes) > 50:
                confidence = 'high'
            elif len(earthquakes) > 20:
                confidence = 'medium'
            else:
                confidence = 'low'
            
            return {
                'probability': round(probability, 3),
                'confidence': confidence,
                'based_on_events': len(earthquakes),
                'recent_activity': len(recent_earthquakes)
            }
            
        except Exception as e:
            self.logger.error(f"Error predicting earthquake probability: {e}")
            return {
                'probability': 0.0,
                'confidence': 'unknown',
                'error': str(e)
            }
