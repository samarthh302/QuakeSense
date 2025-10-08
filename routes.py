from flask import render_template, request, jsonify, redirect, url_for, flash
from app import app, db
from models import Earthquake, RiskZone
from earthquake_service import EarthquakeService
from prediction_service import PredictionService
from datetime import datetime, timedelta
from sqlalchemy import and_, or_
import logging

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/admin')
def admin():
    """Admin panel for data management"""
    earthquakes = Earthquake.query.order_by(Earthquake.timestamp.desc()).limit(50).all()
    total_earthquakes = Earthquake.query.count()
    recent_earthquakes = Earthquake.query.filter(
        Earthquake.timestamp >= datetime.utcnow() - timedelta(days=7)
    ).count()
    
    return render_template('admin.html', 
                         earthquakes=earthquakes,
                         total_earthquakes=total_earthquakes,
                         recent_earthquakes=recent_earthquakes)

@app.route('/api/earthquakes')
def api_earthquakes():
    """API endpoint to get earthquake data with filtering"""
    try:
        # Get query parameters
        magnitude_min = request.args.get('magnitude_min', type=float)
        magnitude_max = request.args.get('magnitude_max', type=float)
        region = request.args.get('region')
        days = request.args.get('days', default=30, type=int)
        limit = request.args.get('limit', default=1000, type=int)
        
        # Build query
        query = Earthquake.query
        
        # Filter by time period
        if days > 0:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(Earthquake.timestamp >= cutoff_date)
        
        # Filter by magnitude
        if magnitude_min is not None:
            query = query.filter(Earthquake.magnitude >= magnitude_min)
        if magnitude_max is not None:
            query = query.filter(Earthquake.magnitude <= magnitude_max)
        
        # Filter by region
        if region:
            query = query.filter(Earthquake.region.ilike(f'%{region}%'))
        
        # Execute query
        earthquakes = query.order_by(Earthquake.timestamp.desc()).limit(limit).all()
        
        return jsonify({
            'success': True,
            'earthquakes': [eq.to_dict() for eq in earthquakes],
            'count': len(earthquakes)
        })
        
    except Exception as e:
        app.logger.error(f"Error fetching earthquakes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/risk-zones')
def api_risk_zones():
    """API endpoint to get risk zone data"""
    try:
        risk_zones = RiskZone.query.filter(RiskZone.risk_level > 0.3).all()
        return jsonify({
            'success': True,
            'risk_zones': [zone.to_dict() for zone in risk_zones]
        })
    except Exception as e:
        app.logger.error(f"Error fetching risk zones: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/fetch-data', methods=['POST'])
def api_fetch_data():
    """Manually trigger earthquake data fetch"""
    try:
        service = EarthquakeService()
        count = service.fetch_and_store_earthquakes()
        return jsonify({
            'success': True,
            'message': f'Successfully fetched {count} new earthquakes',
            'count': count
        })
    except Exception as e:
        app.logger.error(f"Error fetching earthquake data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/update-predictions', methods=['POST'])
def api_update_predictions():
    """Update risk zone predictions"""
    try:
        prediction_service = PredictionService()
        zones_updated = prediction_service.update_risk_zones()
        return jsonify({
            'success': True,
            'message': f'Updated {zones_updated} risk zones',
            'zones_updated': zones_updated
        })
    except Exception as e:
        app.logger.error(f"Error updating predictions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/earthquake/<int:earthquake_id>')
def api_earthquake_detail(earthquake_id):
    """Get detailed information about a specific earthquake"""
    try:
        earthquake = Earthquake.query.get_or_404(earthquake_id)
        return jsonify({
            'success': True,
            'earthquake': earthquake.to_dict()
        })
    except Exception as e:
        app.logger.error(f"Error fetching earthquake detail: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/statistics')
def api_statistics():
    """Get earthquake statistics"""
    try:
        total = Earthquake.query.count()
        
        # Recent earthquakes (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent = Earthquake.query.filter(Earthquake.timestamp >= week_ago).count()
        
        # Magnitude distribution
        major = Earthquake.query.filter(Earthquake.magnitude >= 6.0).count()
        moderate = Earthquake.query.filter(and_(
            Earthquake.magnitude >= 4.0,
            Earthquake.magnitude < 6.0
        )).count()
        minor = Earthquake.query.filter(Earthquake.magnitude < 4.0).count()
        
        # Average magnitude
        from sqlalchemy import func
        avg_magnitude = db.session.query(func.avg(Earthquake.magnitude)).scalar()
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_earthquakes': total,
                'recent_earthquakes': recent,
                'major_earthquakes': major,
                'moderate_earthquakes': moderate,
                'minor_earthquakes': minor,
                'average_magnitude': round(float(avg_magnitude or 0), 2)
            }
        })
    except Exception as e:
        app.logger.error(f"Error fetching statistics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/earthquake/<int:earthquake_id>/delete', methods=['POST'])
def admin_delete_earthquake(earthquake_id):
    """Delete an earthquake record"""
    try:
        earthquake = Earthquake.query.get_or_404(earthquake_id)
        db.session.delete(earthquake)
        db.session.commit()
        flash(f'Earthquake {earthquake.usgs_id} deleted successfully', 'success')
    except Exception as e:
        app.logger.error(f"Error deleting earthquake: {e}")
        flash(f'Error deleting earthquake: {e}', 'error')
    
    return redirect(url_for('admin'))
