import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# initialize the app with the extension
db.init_app(app)

# Import routes after app initialization
from routes import *  # noqa: F401, F403

with app.app_context():
    # Create tables
    db.create_all()

# Initialize background scheduler for data fetching
scheduler = BackgroundScheduler()

def fetch_earthquake_data():
    """Background task to fetch earthquake data from USGS API"""
    with app.app_context():
        try:
            from earthquake_service import EarthquakeService
            service = EarthquakeService()
            count = service.fetch_and_store_earthquakes()
            app.logger.info(f"Fetched {count} new earthquakes")
        except Exception as e:
            app.logger.error(f"Error fetching earthquake data: {e}")

# Schedule earthquake data fetching every 30 minutes
scheduler.add_job(
    func=fetch_earthquake_data,
    trigger=IntervalTrigger(minutes=30),
    id='fetch_earthquakes',
    name='Fetch earthquake data from USGS',
    replace_existing=True
)

# Start the scheduler
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
