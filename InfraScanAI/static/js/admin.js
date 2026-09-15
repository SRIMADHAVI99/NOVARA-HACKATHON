let map;
let heatmap;
let damageChartInstance;
let reportsData = [];

document.addEventListener('DOMContentLoaded', () => {
    fetchReports();
    // Refresh data every 30 seconds
    setInterval(fetchReports, 30000);
});

async function fetchReports() {
    try {
        const response = await fetch('/api/reports');
        if (response.ok) {
            reportsData = await response.json();
            updateDashboard();
        }
    } catch (e) {
        console.error("Error fetching reports", e);
    }
}

function updateDashboard() {
    updateStats();
    updateTable();
    updateChart();
    
    // Check if Google Maps API loaded successfully
    if (typeof google === 'object' && typeof google.maps === 'object' && typeof google.maps.Map === 'function') {
        try {
            initMap();
        } catch (err) {
            console.warn("Google Maps init failed, falling back to Leaflet:", err);
            initFallbackMap();
        }
    } else {
        initFallbackMap();
    }
}

function updateStats() {
    document.getElementById('statTotal').textContent = reportsData.length;
    document.getElementById('statPending').textContent = reportsData.filter(r => r.status === 'Pending').length;
    document.getElementById('statRepaired').textContent = reportsData.filter(r => r.status === 'Repaired').length;
    document.getElementById('statHighSeverity').textContent = reportsData.filter(r => r.severity === 'High').length;
}

function updateTable() {
    const tbody = document.getElementById('reportsTableBody');
    tbody.innerHTML = '';
    
    reportsData.forEach(r => {
        const tr = document.createElement('tr');
        tr.style.borderBottom = '1px solid var(--border-color)';
        tr.style.transition = 'background-color 0.2s';
        tr.onmouseover = () => tr.style.backgroundColor = '#f8fafc';
        tr.onmouseout = () => tr.style.backgroundColor = 'transparent';
        
        let badgeClass = 'badge-success';
        if (r.status === 'Pending') badgeClass = 'badge-warning';
        else if (r.status === 'Under Review') badgeClass = 'badge-primary';
        
        let sevColor = '#64748b';
        if(r.severity === 'High') sevColor = '#ef4444';
        else if(r.severity === 'Medium') sevColor = '#f59e0b';
        
        const dateStr = new Date(r.report_time).toLocaleDateString(undefined, {year: 'numeric', month: 'short', day: 'numeric'});

        tr.innerHTML = `
            <td style="padding: 1rem; width: 120px;">
                <div style="font-weight: 600; font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.5rem;">#${r.report_id.split('-')[1]}</div>
                <img src="/static/uploads/${r.image_path}" style="width: 80px; height: 60px; object-fit: cover; border-radius: 0.5rem; border: 1px solid var(--border-color);">
            </td>
            <td style="padding: 1rem;">
                <div style="font-weight: 500; margin-bottom: 0.25rem;">${r.name}</div>
                <div style="font-size: 0.85rem; color: var(--text-muted);"><i class="fa-solid fa-envelope" style="margin-right: 4px;"></i>${r.email}</div>
                ${r.phone ? `<div style="font-size: 0.85rem; color: var(--text-muted);"><i class="fa-solid fa-phone" style="margin-right: 4px;"></i>${r.phone}</div>` : ''}
                <div style="font-size: 0.85rem; color: var(--primary-color); margin-top: 0.5rem;"><i class="fa-solid fa-calendar-day" style="margin-right: 4px;"></i>${dateStr}</div>
            </td>
            <td style="padding: 1rem;">
                <div style="font-weight: 600; margin-bottom: 0.25rem;">${r.damage_type}</div>
                <div><span style="color: ${sevColor}; font-weight: 600; font-size: 0.9rem;"><i class="fa-solid fa-triangle-exclamation" style="margin-right: 4px;"></i>${r.severity}</span></div>
            </td>
            <td style="padding: 1rem; max-width: 200px;">
                <div style="font-size: 0.85rem; margin-bottom: 0.25rem;"><strong style="color: var(--primary-color);">Conf:</strong> ${r.confidence ? (r.confidence * 100).toFixed(0) + '%' : 'N/A'}</div>
                <div class="text-muted" style="font-size: 0.85rem; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; text-overflow: ellipsis;">
                    ${r.notes || 'No description provided.'}
                </div>
            </td>
            <td style="padding: 1rem;">
                <span class="badge ${badgeClass}" id="status-${r.id}">${r.status}</span>
            </td>
            <td style="padding: 1rem;">
                <div style="display: flex; flex-direction: column; gap: 0.5rem;">
                ${r.status === 'Pending' ? 
                    `<button class="btn btn-primary" style="padding: 0.4rem 0.75rem; font-size: 0.85rem;" onclick="updateStatus(${r.id}, 'Under Review')">Review</button>` 
                    : ''
                }
                ${(r.status === 'Pending' || r.status === 'Under Review') ? 
                    `<button class="btn btn-outline" style="padding: 0.4rem 0.75rem; font-size: 0.85rem;" onclick="assignTeam(${r.id})">Assign Team</button>
                     <button class="btn btn-success" style="padding: 0.4rem 0.75rem; font-size: 0.85rem; background-color: var(--success-color); color: white; border: none;" onclick="updateStatus(${r.id}, 'Repaired')"><i class="fa-solid fa-check"></i> Resolve</button>
                    ` 
                    : 
                    `<span style="color: var(--success-color); font-weight: 600;"><i class="fa-solid fa-check-double" style="margin-right: 4px;"></i> Resolved</span>`
                }
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function updateChart() {
    const ctx = document.getElementById('damageChart').getContext('2d');
    
    const types = {'Pothole': 0, 'Crack': 0, 'No Damage': 0};
    reportsData.forEach(r => {
        if(types[r.damage_type] !== undefined) types[r.damage_type]++;
    });
    
    if (damageChartInstance) {
        damageChartInstance.destroy();
    }
    
    damageChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(types),
            datasets: [{
                data: Object.values(types),
                backgroundColor: [
                    '#6366f1', // Indigo for Pothole
                    '#ec4899', // Pink for Crack
                    '#10b981'  // Green for No damage
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}

async function updateStatus(id, newStatus) {
    if(!confirm(`Are you sure you want to mark this report as ${newStatus}?`)) return;
    
    try {
        const response = await fetch(`/api/reports/${id}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
        });
        
        if (response.ok) {
            // Update local data and re-render
            const report = reportsData.find(r => r.id === id);
            if(report) report.status = newStatus;
            updateDashboard();
        }
    } catch (e) {
        alert("Error updating status");
    }
}

function assignTeam(id) {
    alert(`Maintenance team assigned to report #${id}. Tracking number dispatched.`);
    updateStatus(id, 'Under Review');
}

function logoutOfficer() {
    localStorage.removeItem('officerData');
    window.location.href = '/officer_login';
}

// Map initialization (If mock API key fails, it won't render, but we set it up anyway)
function initMap() {
    if (!document.getElementById('map')) return;
    
    // Default center (average of points or an arbitrary city center)
    let center = { lat: 37.7749, lng: -122.4194 }; 
    if(reportsData.length > 0) {
        center = { lat: reportsData[0].latitude, lng: reportsData[0].longitude };
    }

    map = new google.maps.Map(document.getElementById('map'), {
        zoom: 12,
        center: center,
        styles: [
            { elementType: "geometry", stylers: [{ color: "#f5f5f5" }] },
            { elementType: "labels.icon", stylers: [{ visibility: "off" }] },
            { elementType: "labels.text.fill", stylers: [{ color: "#616161" }] },
            { elementType: "labels.text.stroke", stylers: [{ color: "#f5f5f5" }] },
            { featureType: "administrative.land_parcel", elementType: "labels.text.fill", stylers: [{ color: "#bdbdbd" }] },
            { featureType: "poi", elementType: "geometry", stylers: [{ color: "#eeeeee" }] },
            { featureType: "poi", elementType: "labels.text.fill", stylers: [{ color: "#757575" }] },
            { featureType: "poi.park", elementType: "geometry", stylers: [{ color: "#e5e5e5" }] },
            { featureType: "poi.park", elementType: "labels.text.fill", stylers: [{ color: "#9e9e9e" }] },
            { featureType: "road", elementType: "geometry", stylers: [{ color: "#ffffff" }] },
            { featureType: "road.arterial", elementType: "labels.text.fill", stylers: [{ color: "#757575" }] },
            { featureType: "road.highway", elementType: "geometry", stylers: [{ color: "#dadada" }] },
            { featureType: "road.highway", elementType: "labels.text.fill", stylers: [{ color: "#616161" }] },
            { featureType: "road.local", elementType: "labels.text.fill", stylers: [{ color: "#9e9e9e" }] },
            { featureType: "transit.line", elementType: "geometry", stylers: [{ color: "#e5e5e5" }] },
            { featureType: "transit.station", elementType: "geometry", stylers: [{ color: "#eeeeee" }] },
            { featureType: "water", elementType: "geometry", stylers: [{ color: "#c9c9c9" }] },
            { featureType: "water", elementType: "labels.text.fill", stylers: [{ color: "#9e9e9e" }] }
        ]
    });

    const heatmapData = reportsData.map(r => new google.maps.LatLng(r.latitude, r.longitude));
    
    heatmap = new google.maps.visualization.HeatmapLayer({
        data: heatmapData,
        map: map,
        radius: 20,
        gradient: [
            'rgba(0, 255, 255, 0)',
            'rgba(0, 255, 255, 1)',
            'rgba(0, 191, 255, 1)',
            'rgba(0, 127, 255, 1)',
            'rgba(0, 63, 255, 1)',
            'rgba(0, 0, 255, 1)',
            'rgba(0, 0, 223, 1)',
            'rgba(0, 0, 191, 1)',
            'rgba(0, 0, 159, 1)',
            'rgba(0, 0, 127, 1)',
            'rgba(63, 0, 91, 1)',
            'rgba(127, 0, 63, 1)',
            'rgba(191, 0, 31, 1)',
            'rgba(255, 0, 0, 1)'
        ]
    });
    
    // Also add markers
    reportsData.forEach(r => {
        if(r.status === 'Pending') {
            new google.maps.Marker({
                position: {lat: r.latitude, lng: r.longitude},
                map: map,
                title: r.damage_type
            });
        }
    });
}

let leafletMapInstance = null;

function initFallbackMap() {
    const mapElement = document.getElementById('map');
    if (!mapElement) return;

    // Hide overlay
    const overlay = document.getElementById('mapOverlay');
    if (overlay) overlay.style.display = 'none';

    if (typeof L === 'undefined') {
        mapElement.innerHTML = '<div style="padding: 2rem; text-align: center; color: #64748b;">Map view offline.</div>';
        return;
    }

    if (leafletMapInstance) {
        leafletMapInstance.remove();
        leafletMapInstance = null;
    }

    let defaultCenter = [37.7749, -122.4194];
    if (reportsData.length > 0 && reportsData[0].latitude && reportsData[0].longitude) {
        defaultCenter = [reportsData[0].latitude, reportsData[0].longitude];
    }

    leafletMapInstance = L.map('map').setView(defaultCenter, 11);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(leafletMapInstance);

    const markersGroup = L.featureGroup();

    reportsData.forEach(r => {
        if (r.latitude && r.longitude) {
            const statusClass = r.status === 'Pending' ? 'badge-warning' : (r.status === 'Under Review' ? 'badge-primary' : 'badge-success');
            const sevColor = r.severity === 'High' ? '#ef4444' : (r.severity === 'Medium' ? '#f59e0b' : '#059669');

            const popupContent = `
                <div style="font-family: system-ui, sans-serif; min-width: 180px; padding: 4px;">
                    <div style="font-weight: 700; font-size: 1rem; color: #1e293b;">${r.damage_type}</div>
                    <div style="font-size: 0.85rem; color: ${sevColor}; font-weight: 600; margin-bottom: 4px;">Severity: ${r.severity}</div>
                    <div style="font-size: 0.8rem; color: #64748b; margin-bottom: 6px;">Reported by: ${r.name}</div>
                    <span class="badge ${statusClass}" style="font-size: 0.75rem; padding: 2px 8px;">${r.status}</span>
                    ${r.image_path ? `<div style="margin-top: 6px;"><img src="/static/uploads/${r.image_path}" style="width: 100%; height: 70px; object-fit: cover; border-radius: 4px;"></div>` : ''}
                </div>
            `;

            const marker = L.marker([r.latitude, r.longitude]).bindPopup(popupContent);
            marker.addTo(markersGroup);
        }
    });

    markersGroup.addTo(leafletMapInstance);

    if (reportsData.length > 0) {
        try {
            leafletMapInstance.fitBounds(markersGroup.getBounds().pad(0.2));
        } catch (e) {
            // Ignore if single point
        }
    }
}
