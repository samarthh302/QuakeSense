// Admin panel functionality
function initializeAdminPanel() {
    setupEventListeners();
}

function setupEventListeners() {
    // Manual fetch data button
    document.getElementById('fetch-data-btn').addEventListener('click', fetchEarthquakeData);
    document.getElementById('manual-fetch-btn').addEventListener('click', fetchEarthquakeData);
    document.getElementById('initial-fetch-btn')?.addEventListener('click', fetchEarthquakeData);
    
    // Update predictions button
    document.getElementById('update-predictions-btn').addEventListener('click', updatePredictions);
    document.getElementById('recalculate-risk-btn').addEventListener('click', updatePredictions);
}

function fetchEarthquakeData() {
    showOperationStatus('Fetching earthquake data...', 'info');
    
    // Disable buttons during operation
    const buttons = ['fetch-data-btn', 'manual-fetch-btn', 'initial-fetch-btn'];
    buttons.forEach(id => {
        const btn = document.getElementById(id);
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i data-feather="loader" class="spin me-1"></i>Fetching...';
        }
    });
    
    fetch('/api/fetch-data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showOperationStatus(
                `Success! ${data.message}`, 
                'success',
                () => {
                    // Refresh the page to show new data
                    setTimeout(() => window.location.reload(), 1500);
                }
            );
        } else {
            showOperationStatus(`Error: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        console.error('Error fetching data:', error);
        showOperationStatus('Error: Network request failed', 'error');
    })
    .finally(() => {
        // Re-enable buttons
        buttons.forEach(id => {
            const btn = document.getElementById(id);
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i data-feather="download"></i> Fetch New Data';
            }
        });
        feather.replace();
    });
}

function updatePredictions() {
    showOperationStatus('Updating risk zone predictions...', 'info');
    
    // Disable buttons during operation
    const buttons = ['update-predictions-btn', 'recalculate-risk-btn'];
    buttons.forEach(id => {
        const btn = document.getElementById(id);
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i data-feather="loader" class="spin me-1"></i>Processing...';
        }
    });
    
    fetch('/api/update-predictions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showOperationStatus(
                `Success! ${data.message}`, 
                'success',
                () => {
                    // Refresh risk zones count
                    loadRiskZonesCount();
                }
            );
        } else {
            showOperationStatus(`Error: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        console.error('Error updating predictions:', error);
        showOperationStatus('Error: Network request failed', 'error');
    })
    .finally(() => {
        // Re-enable buttons
        buttons.forEach(id => {
            const btn = document.getElementById(id);
            if (btn) {
                btn.disabled = false;
                if (id.includes('update')) {
                    btn.innerHTML = '<i data-feather="cpu"></i> Update Predictions';
                } else {
                    btn.innerHTML = '<i data-feather="cpu"></i> Recalculate Risk Zones';
                }
            }
        });
        feather.replace();
    });
}

function showOperationStatus(message, type = 'info', callback = null) {
    const statusElement = document.getElementById('status-message');
    
    let icon, className;
    switch (type) {
        case 'success':
            icon = 'check-circle';
            className = 'text-success';
            break;
        case 'error':
            icon = 'alert-circle';
            className = 'text-danger';
            break;
        default:
            icon = 'info';
            className = 'text-info';
    }
    
    statusElement.innerHTML = `
        <div class="${className} text-center">
            <i data-feather="${icon}" width="48" height="48"></i>
            <p class="mt-2">${message}</p>
        </div>
    `;
    
    feather.replace();
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('statusModal'));
    modal.show();
    
    // Execute callback if provided
    if (callback) {
        callback();
    }
    
    // Auto-hide success messages
    if (type === 'success') {
        setTimeout(() => {
            modal.hide();
        }, 3000);
    }
}

function confirmDelete(earthquakeId, earthquakeInfo) {
    if (confirm(`Are you sure you want to delete earthquake ${earthquakeInfo}?`)) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/admin/earthquake/${earthquakeId}/delete`;
        document.body.appendChild(form);
        form.submit();
    }
}

// Utility function to format numbers
function formatNumber(num) {
    return num.toLocaleString();
}

// Utility function to format dates
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

// Auto-refresh functionality for admin panel
function startAutoRefresh() {
    // Refresh statistics every 2 minutes
    setInterval(() => {
        loadRiskZonesCount();
        // Could add other auto-refresh functionality here
    }, 120000);
}

// Initialize auto-refresh when page loads
document.addEventListener('DOMContentLoaded', function() {
    startAutoRefresh();
});
