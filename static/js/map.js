// Global earthquake map functionality
let earthquakeMap = null;
let earthquakeMarkers = [];
let riskZoneCircles = [];
let showRiskZones = false;

function initializeEarthquakeMap() {
    // Initialize the map
    earthquakeMap = {
        map: L.map('earthquake-map').setView([20, 0], 2),
        
        init: function() {
            // Add tile layer
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(this.map);
            
            // Load initial data
            this.loadEarthquakes();
            this.setupEventListeners();
        },
        
        loadEarthquakes: function(filters = {}) {
            const params = new URLSearchParams();
            
            // Add filters to params
            if (filters.days) params.append('days', filters.days);
            if (filters.minMagnitude) params.append('magnitude_min', filters.minMagnitude);
            if (filters.maxMagnitude) params.append('magnitude_max', filters.maxMagnitude);
            if (filters.region) params.append('region', filters.region);
            
            fetch(`/api/earthquakes?${params}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        this.displayEarthquakes(data.earthquakes);
                        this.updateRecentEarthquakesList(data.earthquakes);
                        this.updateLastUpdateTime();
                    } else {
                        console.error('Error loading earthquakes:', data.error);
                    }
                })
                .catch(error => {
                    console.error('Error fetching earthquake data:', error);
                });
        },
        
        displayEarthquakes: function(earthquakes) {
            // Clear existing markers
            earthquakeMarkers.forEach(marker => this.map.removeLayer(marker));
            earthquakeMarkers = [];
            
            earthquakes.forEach(eq => {
                const color = this.getMagnitudeColor(eq.magnitude);
                const radius = this.getMagnitudeRadius(eq.magnitude);
                
                const marker = L.circleMarker([eq.latitude, eq.longitude], {
                    radius: radius,
                    fillColor: color,
                    color: color,
                    weight: 2,
                    opacity: 0.8,
                    fillOpacity: 0.6
                });
                
                // Popup content
                const popupContent = `
                    <div class="earthquake-popup">
                        <h6 class="mb-2">
                            <span class="badge bg-${this.getMagnitudeBadgeColor(eq.magnitude)}">
                                M${eq.magnitude}
                            </span>
                        </h6>
                        <p class="mb-1"><strong>Region:</strong> ${eq.region}</p>
                        <p class="mb-1"><strong>Depth:</strong> ${eq.depth} km</p>
                        <p class="mb-1"><strong>Time:</strong> ${new Date(eq.timestamp).toLocaleString()}</p>
                        <p class="mb-0"><strong>Location:</strong> ${eq.latitude.toFixed(3)}, ${eq.longitude.toFixed(3)}</p>
                    </div>
                `;
                
                marker.bindPopup(popupContent);
                marker.addTo(this.map);
                earthquakeMarkers.push(marker);
            });
        },
        
        loadRiskZones: function() {
            fetch('/api/risk-zones')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        this.displayRiskZones(data.risk_zones);
                    }
                })
                .catch(error => console.error('Error loading risk zones:', error));
        },
        
        displayRiskZones: function(riskZones) {
            // Clear existing risk zone circles
            riskZoneCircles.forEach(circle => this.map.removeLayer(circle));
            riskZoneCircles = [];
            
            if (!showRiskZones) return;
            
            riskZones.forEach(zone => {
                const radius = Math.max(zone.risk_level * 100000, 20000); // Convert to meters
                const opacity = zone.risk_level * 0.7;
                
                const circle = L.circle([zone.latitude, zone.longitude], {
                    radius: radius,
                    color: '#007bff',
                    fillColor: '#007bff',
                    fillOpacity: opacity * 0.3,
                    weight: 2,
                    opacity: opacity
                });
                
                const popupContent = `
                    <div class="risk-zone-popup">
                        <h6 class="mb-2 text-primary">Risk Zone</h6>
                        <p class="mb-1"><strong>Region:</strong> ${zone.region_name || 'Unknown'}</p>
                        <p class="mb-1"><strong>Risk Level:</strong> ${(zone.risk_level * 100).toFixed(1)}%</p>
                        <p class="mb-1"><strong>Historical Events:</strong> ${zone.earthquake_count}</p>
                        <p class="mb-0"><small class="text-muted">Last updated: ${new Date(zone.last_updated).toLocaleString()}</small></p>
                    </div>
                `;
                
                circle.bindPopup(popupContent);
                circle.addTo(this.map);
                riskZoneCircles.push(circle);
            });
        },
        
        getMagnitudeColor: function(magnitude) {
            if (magnitude < 4.0) return '#28a745'; // green
            else if (magnitude < 6.0) return '#ffc107'; // yellow
            else return '#dc3545'; // red
        },
        
        getMagnitudeBadgeColor: function(magnitude) {
            if (magnitude < 4.0) return 'success';
            else if (magnitude < 6.0) return 'warning';
            else return 'danger';
        },
        
        getMagnitudeRadius: function(magnitude) {
            return Math.max(magnitude * 2, 3);
        },
        
        toggleRiskZones: function() {
            showRiskZones = !showRiskZones;
            if (showRiskZones) {
                this.loadRiskZones();
                document.getElementById('toggle-risk-zones').classList.add('active');
            } else {
                riskZoneCircles.forEach(circle => this.map.removeLayer(circle));
                riskZoneCircles = [];
                document.getElementById('toggle-risk-zones').classList.remove('active');
            }
        },
        
        refreshData: function() {
            const filters = this.getCurrentFilters();
            this.loadEarthquakes(filters);
            if (showRiskZones) {
                this.loadRiskZones();
            }
        },
        
        getCurrentFilters: function() {
            return {
                days: document.getElementById('time-filter').value,
                minMagnitude: document.getElementById('min-magnitude').value,
                maxMagnitude: document.getElementById('max-magnitude').value,
                region: document.getElementById('region-filter').value
            };
        },
        
        updateRecentEarthquakesList: function(earthquakes) {
            const majorEarthquakes = earthquakes
                .filter(eq => eq.magnitude >= 5.0)
                .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
                .slice(0, 5);
            
            const listContainer = document.getElementById('recent-earthquakes-list');
            
            if (majorEarthquakes.length === 0) {
                listContainer.innerHTML = `
                    <div class="text-center text-muted">
                        <i data-feather="info"></i>
                        <p class="mt-2">No major earthquakes in the selected time period</p>
                    </div>
                `;
                feather.replace();
                return;
            }
            
            const listHTML = majorEarthquakes.map(eq => `
                <div class="d-flex justify-content-between align-items-start mb-2 p-2 border-bottom">
                    <div>
                        <div class="d-flex align-items-center mb-1">
                            <span class="badge bg-${this.getMagnitudeBadgeColor(eq.magnitude)} me-2">
                                M${eq.magnitude}
                            </span>
                            <small class="text-muted">${new Date(eq.timestamp).toLocaleDateString()}</small>
                        </div>
                        <div class="small text-truncate" style="max-width: 250px;" title="${eq.region}">
                            ${eq.region}
                        </div>
                    </div>
                </div>
            `).join('');
            
            listContainer.innerHTML = listHTML;
        },
        
        updateLastUpdateTime: function() {
            const now = new Date();
            document.getElementById('last-update-time').textContent = now.toLocaleTimeString();
        },
        
        setupEventListeners: function() {
            // Filter form submission
            document.getElementById('filter-form').addEventListener('submit', (e) => {
                e.preventDefault();
                const filters = this.getCurrentFilters();
                this.loadEarthquakes(filters);
            });
            
            // Refresh button
            document.getElementById('refresh-data').addEventListener('click', () => {
                this.refreshData();
            });
            
            // Toggle risk zones button
            document.getElementById('toggle-risk-zones').addEventListener('click', () => {
                this.toggleRiskZones();
            });
        }
    };
    
    // Initialize the map
    earthquakeMap.init();
}

// Utility function to show loading state
function showLoadingState(elementId, message = 'Loading...') {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="text-center text-muted">
                <i data-feather="loader" class="spin"></i>
                <p class="mt-2">${message}</p>
            </div>
        `;
        feather.replace();
    }
}
