# QuakeSense - Global Earthquake Tracking and Prediction System

## Overview

QuakeSense is a Flask-based web application that provides real-time earthquake monitoring and risk assessment capabilities. The system fetches earthquake data from the USGS (United States Geological Survey) API, stores it in a relational database, and visualizes it on an interactive world map. It includes predictive analytics to identify high-risk seismic zones based on historical earthquake patterns.

The application serves two main user groups:
1. **General users** - View earthquake data on an interactive dashboard with filtering capabilities
2. **Administrators** - Manage data fetching, update risk predictions, and monitor system statistics

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Technology Stack**: The frontend uses a traditional server-rendered approach with Jinja2 templates, enhanced with modern JavaScript libraries:
- Bootstrap 5 (dark theme) for responsive UI components
- Leaflet.js for interactive map visualization
- Chart.js for data visualization
- Feather Icons for consistent iconography

**Design Pattern**: The application follows a template inheritance pattern with `base.html` as the parent template, providing consistent navigation and styling across pages (`index.html` for dashboard, `admin.html` for admin panel).

**Client-Side Logic**: JavaScript modules (`map.js`, `admin.js`) handle:
- Asynchronous data fetching from REST APIs
- Dynamic map marker rendering based on earthquake magnitude
- Real-time UI updates without page reloads
- Filter controls for earthquake data

**Rationale**: This architecture was chosen for simplicity and rapid development. Server-side rendering reduces complexity while JavaScript enhancements provide interactivity. The alternative of a full SPA framework (React/Vue) would add unnecessary overhead for this use case.

### Backend Architecture

**Framework**: Flask (Python web framework) with SQLAlchemy ORM for database operations.

**Application Structure**:
- `app.py` - Application factory, database initialization, and scheduler setup
- `routes.py` - HTTP route handlers for web pages and REST API endpoints
- `models.py` - SQLAlchemy data models (Earthquake, RiskZone)
- `earthquake_service.py` - Business logic for fetching and storing USGS earthquake data
- `prediction_service.py` - Risk assessment and prediction algorithms
- `main.py` - Application entry point

**Key Architectural Decisions**:

1. **Service Layer Pattern**: Business logic is separated into dedicated service classes (`EarthquakeService`, `PredictionService`) rather than embedding it in routes. This promotes reusability and testability.

2. **Background Task Processing**: APScheduler runs periodic tasks (earthquake data fetching) in the background without blocking HTTP requests. This ensures fresh data without manual intervention.

3. **Database Connection Pooling**: SQLAlchemy is configured with `pool_recycle=300` and `pool_pre_ping=True` to handle connection lifecycle management and prevent stale connections.

4. **Proxy Fix Middleware**: `ProxyFix` middleware ensures correct protocol and host information when deployed behind reverse proxies (common in cloud environments).

**Pros**:
- Simple, maintainable codebase
- Clear separation of concerns
- Easy to extend with new features

**Cons**:
- Background scheduler runs in-process (not suitable for multi-worker deployments)
- Synchronous request handling (may struggle under heavy load)

### Data Storage

**Database**: Relational database accessed via SQLAlchemy ORM (configured through `DATABASE_URL` environment variable).

**Schema Design**:

1. **Earthquake Model**:
   - Stores seismic event data from USGS
   - Indexed fields: `usgs_id` (unique), `magnitude`, `timestamp`, `latitude/longitude`, `region`
   - Composite index on location coordinates for spatial queries
   - Includes `created_at` for tracking when data was ingested

2. **RiskZone Model** (referenced but not fully shown):
   - Stores computed risk assessments for geographic grid cells
   - Derived from historical earthquake patterns

**Indexing Strategy**: Multiple indexes support common query patterns:
- Time-based filtering (recent earthquakes)
- Magnitude-based filtering (major events)
- Geographic filtering (region-specific queries)
- Location-based queries for spatial analysis

**Rationale**: SQLAlchemy ORM provides database portability while maintaining type safety. The indexing strategy optimizes for read-heavy workloads typical of monitoring applications. The alternative of NoSQL storage was rejected due to the need for complex relational queries and ACID guarantees.

### Authentication & Authorization

**Current State**: No authentication system is implemented. The application relies on environment-based security (`SESSION_SECRET`).

**Security Considerations**: Admin endpoints (`/admin`, `/api/fetch-data`) are currently unprotected, suitable only for trusted environments or future enhancement with authentication middleware.

### Prediction & Analytics

**Algorithm**: Grid-based risk assessment that:
1. Divides the globe into grid cells (configurable size, default 2° x 2°)
2. Aggregates historical earthquake data (365-day window) per cell
3. Calculates risk metrics based on frequency and magnitude
4. Stores results in RiskZone table for visualization

**Design Choice**: Rule-based approach over machine learning for initial version. This provides:
- Interpretable results
- No training data requirements
- Deterministic behavior
- Lower computational overhead

The architecture supports future ML integration through the service layer abstraction.

## External Dependencies

### Third-Party APIs

**USGS Earthquake API**:
- **Endpoint**: `https://earthquake.usgs.gov/fdsnws/event/1/query`
- **Purpose**: Fetch global earthquake data in GeoJSON format
- **Rate Limits**: Maximum 20,000 records per request
- **Data Fields**: Magnitude, location (lat/lon), depth, region, timestamp
- **Integration**: `EarthquakeService` handles API requests with timeout protection (30s)

### External Libraries & Services

**Python Dependencies**:
- `Flask` - Web framework
- `Flask-SQLAlchemy` - ORM and database toolkit
- `requests` - HTTP client for USGS API
- `APScheduler` - Background task scheduling
- `werkzeug` - WSGI utilities (ProxyFix middleware)

**Frontend Libraries** (CDN-hosted):
- `Leaflet.js` (v1.9.4) - Interactive map rendering
- `Bootstrap 5` - UI framework with dark theme
- `Chart.js` - Data visualization
- `Feather Icons` - Icon library

**Database**: Supports any SQLAlchemy-compatible database (PostgreSQL, MySQL, SQLite) via connection string configuration.

### Environment Configuration

**Required Environment Variables**:
- `DATABASE_URL` - Database connection string
- `SESSION_SECRET` - Flask session encryption key

**Deployment Considerations**: The application uses `ProxyFix` middleware, indicating deployment behind a reverse proxy (nginx, Replit's infrastructure, etc.). Background scheduler requires single-worker deployment or external job queue for production scale.