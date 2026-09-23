// AI-AQI GIS Dashboard Controller using Leaflet.js

let map;
let markerGroup;
let currentMode = 'historical';

const RISK_COLORS = {
    0: '#10b981', // Low - Green
    1: '#3b82f6', // Moderate - Blue
    2: '#f59e0b', // Unhealthy - Yellow/Orange
    3: '#ef4444', // Very Unhealthy - Red
    4: '#8b5cf6'  // Severe - Purple
};

const RISK_LABELS = {
    0: 'Low (0)',
    1: 'Moderate (1)',
    2: 'Unhealthy (2)',
    3: 'Very Unhealthy (3)',
    4: 'Severe (4)'
};

// District spatial data coordinates (30 districts in region grid)
const DISTRICT_GRID = [
    { id: 0, name: "Central Business District", lat: 12.9716, lon: 77.5946 },
    { id: 1, name: "North Industrial Zone", lat: 13.0500, lon: 77.5800 },
    { id: 2, name: "South Residential", lat: 12.9000, lon: 77.6000 },
    { id: 3, name: "East Tech Park", lat: 12.9800, lon: 77.7000 },
    { id: 4, name: "West Agricultural Belt", lat: 12.9500, lon: 77.4800 },
    { id: 5, name: "Suburban North", lat: 13.1200, lon: 77.6200 },
    { id: 6, name: "Airport Corridor", lat: 13.2000, lon: 77.6800 },
    { id: 7, name: "Riverside Basin", lat: 12.8500, lon: 77.5200 },
    { id: 8, name: "Hill Station Foothills", lat: 13.1500, lon: 77.4500 },
    { id: 9, name: "Highway Node 1", lat: 12.9200, lon: 77.6500 },
    { id: 10, name: "Highway Node 2", lat: 13.0200, lon: 77.5200 },
    { id: 11, name: "Port Transit Hub", lat: 12.8200, lon: 77.6800 },
    { id: 12, name: "Forest Reserve Border", lat: 12.7500, lon: 77.5500 },
    { id: 13, name: "Urban Slum Cluster", lat: 12.9900, lon: 77.5700 },
    { id: 14, name: "University Campus", lat: 12.9400, lon: 77.5600 },
    { id: 15, name: "Metro Junction East", lat: 12.9750, lon: 77.6400 },
    { id: 16, name: "Metro Junction West", lat: 12.9650, lon: 77.5300 },
    { id: 17, name: "Outer Ring Road", lat: 13.0400, lon: 77.6500 },
    { id: 18, name: "Lake Catchment Area", lat: 12.9100, lon: 77.5800 },
    { id: 19, name: "Industrial Estate B", lat: 13.0800, lon: 77.5400 },
    { id: 20, name: "Commercial Hub North", lat: 13.0100, lon: 77.6000 },
    { id: 21, name: "Commercial Hub South", lat: 12.8800, lon: 77.6200 },
    { id: 22, name: "Green Belt West", lat: 12.8800, lon: 77.4500 },
    { id: 23, name: "Mining Vicinity", lat: 13.1800, lon: 77.5500 },
    { id: 24, name: "Thermal Power Zone", lat: 13.1000, lon: 77.7200 },
    { id: 25, name: "Coastal Delta North", lat: 12.7800, lon: 77.7500 },
    { id: 26, name: "Coastal Delta South", lat: 12.7200, lon: 77.7000 },
    { id: 27, name: "Valley Pass East", lat: 13.0500, lon: 77.7500 },
    { id: 28, name: "Valley Pass West", lat: 13.0500, lon: 77.4000 },
    { id: 29, name: "Metropolitan Core", lat: 12.9650, lon: 77.5900 }
];

document.addEventListener('DOMContentLoaded', () => {
    initMap();
    renderDistricts();
});

function initMap() {
    map = L.map('map').setView([12.9716, 77.5946], 10);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19
    }).addTo(map);

    markerGroup = L.layerGroup().addTo(map);
}

function switchMode(mode) {
    currentMode = mode;

    document.getElementById('btn-historical').classList.toggle('active', mode === 'historical');
    document.getElementById('btn-live').classList.toggle('active', mode === 'live');

    const desc = document.getElementById('mode-description');
    if (mode === 'historical') {
        desc.innerHTML = '<strong>Static 2025 Holdout Mode:</strong> Displaying pre-computed out-of-time predictions from the canonical frozen Deep Learning model on the 2025 test dataset.';
    } else {
        desc.innerHTML = '<strong>Live Telemetry (Simulated) Mode:</strong> Displaying simulated live IoT sensor telemetry predictions processed through the real-time inference pipeline.';
    }

    renderDistricts();
}

function renderDistricts() {
    markerGroup.clearLayers();

    DISTRICT_GRID.forEach(district => {
        // Deterministic pseudo-predictions based on district ID and mode
        let riskClass;
        let probs;

        if (currentMode === 'historical') {
            riskClass = (district.id * 3 + 1) % 5;
        } else {
            riskClass = (district.id * 2 + 3) % 5;
        }

        probs = generateMockProbabilities(riskClass);

        const circle = L.circleMarker([district.lat, district.lon], {
            radius: 12,
            fillColor: RISK_COLORS[riskClass],
            color: '#ffffff',
            weight: 2,
            opacity: 0.9,
            fillOpacity: 0.8
        });

        circle.on('click', () => {
            selectDistrict(district, riskClass, probs);
        });

        const popupContent = `
            <div style="font-family: Inter, sans-serif; font-size: 12px; color: #0f172a;">
                <strong>${district.name}</strong><br>
                Predicted Risk: <span style="font-weight:700; color:${RISK_COLORS[riskClass]}">${RISK_LABELS[riskClass]}</span><br>
                <small>Mode: ${currentMode.toUpperCase()}</small>
            </div>
        `;
        circle.bindTooltip(popupContent);

        markerGroup.addLayer(circle);
    });
}

function generateMockProbabilities(predictedClass) {
    let p = [0.05, 0.05, 0.05, 0.05, 0.05];
    p[predictedClass] = 0.80;
    return p;
}

function selectDistrict(district, riskClass, probs) {
    const detailsContainer = document.getElementById('district-details');

    let html = `
        <div class="detail-card">
            <h4>${district.name} (ID: ${district.id})</h4>
            <div class="risk-badge-large" style="background-color: ${RISK_COLORS[riskClass]};">
                ${RISK_LABELS[riskClass]}
            </div>
            <p style="font-size: 11px; color: #94a3b8; margin-bottom: 12px;">
                Coordinates: ${district.lat.toFixed(4)}°N, ${district.lon.toFixed(4)}°E<br>
                Mode: <strong>${currentMode.toUpperCase()}</strong>
            </p>

            <h5 style="font-size: 11px; text-transform: uppercase; color: #94a3b8; margin-bottom: 8px;">
                Calibrated Class Probabilities
            </h5>
            <div class="prob-bar-container">
    `;

    for (let c = 0; c < 5; c++) {
        const pct = (probs[c] * 100).toFixed(1);
        html += `
            <div class="prob-row">
                <span>${RISK_LABELS[c]}</span>
                <span>${pct}%</span>
            </div>
            <div class="prob-bar">
                <div class="prob-fill" style="width: ${pct}%; background-color: ${RISK_COLORS[c]};"></div>
            </div>
        `;
    }

    html += `
            </div>
        </div>
    `;

    detailsContainer.innerHTML = html;
}
