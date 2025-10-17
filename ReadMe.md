QuakeSense – Global Earthquake Viewer

QuakeSense is a lightweight Flask web application for visualizing earthquake data from an existing database. It provides a clean, user-friendly dashboard for exploring recent seismic events without requiring live data fetching.

Features

Display recent earthquakes in a sortable table.

Fully local and lightweight — runs with Python and Flask.

Uses an existing SQLite database (earthquakes.db) — no new data is fetched.

Easy setup and deployment on any system with Python installed.

Technology Stack

Backend: Python, Flask, Flask-SQLAlchemy

Database: SQLite (earthquakes.db)

Frontend: Jinja2 templates (HTML + CSS)

Dependencies:

Flask

Flask-SQLAlchemy

Project Structure
QuakeSense/
│
├── app.py          # Main Flask application
├── main.py         # Entry point to run the app
├── routes.py       # Application routes
├── instance/
│   └── earthquakes.db  # Existing earthquake database (do not overwrite)
├── templates/      # HTML templates
│   └── index.html
├── static/         # Optional static assets (CSS, JS)
└── README.md

Getting Started
Prerequisites

Python 3.10 or higher installed

pip installed

Install Dependencies
pip install Flask Flask-SQLAlchemy

Run the Application

Open a terminal and navigate to the project folder:

cd path/to/QuakeSense


Run the app:

python main.py


Open a browser and visit:

http://127.0.0.1:5000


You will see the recent earthquake dashboard.

Notes

Do not delete or overwrite instance/earthquakes.db — this file contains all earthquake data.

The app does not fetch live data; it only reads from the existing database.

Optional enhancements include adding interactive maps (Leaflet.js) or charts (Chart.js).
