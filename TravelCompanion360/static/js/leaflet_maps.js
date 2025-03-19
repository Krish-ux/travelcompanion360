// Travel Companion - Leaflet Maps Integration

let map;
let markers = [];
let popup = null;

// Initialize the Leaflet map
function initLeafletMap() {
    // Default center (will be overridden if destinations are available)
    const defaultCenter = [20, 0]; // [lat, lng]
    
    // Create the map
    map = L.map('map').setView(defaultCenter, 2);
    
    // Add the OpenStreetMap tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(map);
    
    // Get destinations from data attribute or from the global variable
    const mapContainer = document.getElementById("map");
    let destinations = [];
    
    // First check if sample destinations are in window (from app.py)
    if (window.sampleDestinations) {
        destinations = window.sampleDestinations;
    }
    // If not, try to get from data attribute
    else if (mapContainer) {
        const destinationsData = mapContainer.getAttribute("data-destinations");
        
        if (destinationsData) {
            try {
                destinations = JSON.parse(destinationsData);
            } catch (error) {
                console.error("Error parsing destinations data:", error);
            }
        }
    }
    
    // Add predefined destinations if none were found
    if (!destinations || destinations.length === 0) {
        // Fallback to hard-coded sample destinations if needed
        destinations = [
            {"name": "Paris", "country": "France", "lat": 48.8566, "lng": 2.3522},
            {"name": "Tokyo", "country": "Japan", "lat": 35.6762, "lng": 139.6503},
            {"name": "New York", "country": "USA", "lat": 40.7128, "lng": -74.0060},
            {"name": "Sydney", "country": "Australia", "lat": -33.8688, "lng": 151.2093},
            {"name": "London", "country": "UK", "lat": 51.5074, "lng": -0.1278}
        ];
    }
    
    // Add markers for each destination
    if (destinations && destinations.length > 0) {
        destinations.forEach(destination => {
            addMarker(destination);
        });
        
        // If we have destinations, center on the first one
        if (destinations.length > 0) {
            map.setView([destinations[0].lat, destinations[0].lng], 5);
        }
        
        // Fit the map to all markers
        if (destinations.length > 1) {
            const bounds = L.latLngBounds(destinations.map(d => [d.lat, d.lng]));
            map.fitBounds(bounds);
        }
    }
    
    // Initialize hotel data if available (for hotels page)
    if (window.hotelData && window.hotelData.length > 0 && window.destination) {
        // Try to geocode the destination for map center
        geocodeLocation(window.destination, function(coords) {
            if (coords) {
                map.setView([coords.lat, coords.lng], 12);
                
                // Add markers for each hotel
                window.hotelData.forEach(hotel => {
                    // Create a point near the center for the hotels
                    // This is simplified since we don't have real coordinates for the hotels
                    const lat = coords.lat + (Math.random() - 0.5) * 0.05;
                    const lng = coords.lng + (Math.random() - 0.5) * 0.05;
                    
                    addHotelMarker({
                        name: hotel.name,
                        location: hotel.location,
                        lat: lat,
                        lng: lng,
                        price: hotel.price,
                        rating: hotel.rating
                    });
                });
            }
        });
    }
    
    // Add nearby search functionality for hotels if button exists
    const findHotelsBtn = document.getElementById("find-nearby-hotels");
    if (findHotelsBtn) {
        findHotelsBtn.addEventListener("click", () => {
            // Get the current center of the map
            const center = map.getCenter();
            highlightNearbyFeatures("hotel");
        });
    }
}

// Add a marker to the map
function addMarker(destination) {
    const marker = L.marker([destination.lat, destination.lng], {
        title: destination.name
    }).addTo(map);
    
    markers.push(marker);
    
    // Add click event to marker
    marker.bindPopup(`
        <div class="info-window">
            <h3>${destination.name}</h3>
            <p>${destination.country}</p>
            <a href="/hotels?destination=${encodeURIComponent(destination.name)}" class="btn btn-primary btn-sm">Find Hotels</a>
        </div>
    `);
}

// Add a hotel marker to the map
function addHotelMarker(hotel) {
    // Create a custom hotel icon
    const hotelIcon = L.divIcon({
        className: 'hotel-marker',
        html: `<i class="fas fa-hotel"></i>`,
        iconSize: [30, 30]
    });
    
    const marker = L.marker([hotel.lat, hotel.lng], {
        title: hotel.name,
        icon: hotelIcon
    }).addTo(map);
    
    markers.push(marker);
    
    // Add click event to marker
    marker.bindPopup(`
        <div class="info-window">
            <h3>${hotel.name}</h3>
            <p>${hotel.location}</p>
            <div class="hotel-price">$${hotel.price}</div>
            <div class="hotel-rating">
                ${'★'.repeat(Math.floor(hotel.rating))}${'☆'.repeat(5 - Math.floor(hotel.rating))}
                ${hotel.rating}/5
            </div>
            <a href="https://www.openstreetmap.org/search?query=${encodeURIComponent(hotel.name + ' ' + hotel.location)}" target="_blank" class="btn btn-secondary btn-sm mt-2">View on OpenStreetMap</a>
        </div>
    `);
}

// Clear all markers from the map
function clearMarkers() {
    markers.forEach(marker => {
        map.removeLayer(marker);
    });
    markers = [];
}

// Geocode a location using Nominatim (OpenStreetMap's geocoder)
function geocodeLocation(location, callback) {
    fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(location)}`)
        .then(response => response.json())
        .then(data => {
            if (data && data.length > 0) {
                callback({
                    lat: parseFloat(data[0].lat),
                    lng: parseFloat(data[0].lon)
                });
            } else {
                console.error('Location not found');
                callback(null);
            }
        })
        .catch(error => {
            console.error('Error geocoding:', error);
            callback(null);
        });
}

// Handle map search form submission
document.addEventListener('DOMContentLoaded', function() {
    const mapSearchForm = document.getElementById('map-search-form');
    
    if (mapSearchForm) {
        mapSearchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const searchInput = document.getElementById('map-search');
            const location = searchInput.value.trim();
            
            if (location) {
                geocodeLocation(location, function(coords) {
                    if (coords) {
                        // Center map on the location
                        map.setView([coords.lat, coords.lng], 13);
                        
                        // Add a marker at the location
                        const marker = L.marker([coords.lat, coords.lng]).addTo(map);
                        
                        // Clear any previous markers and add this one
                        clearMarkers();
                        markers.push(marker);
                        
                        // Add popup to marker
                        marker.bindPopup(`
                            <div class="info-window">
                                <h3>${location}</h3>
                                <a href="/hotels?destination=${encodeURIComponent(location)}" class="btn btn-primary btn-sm">Find Hotels</a>
                            </div>
                        `).openPopup();
                    } else {
                        alert('Could not find the location. Please try a different search term.');
                    }
                });
            }
        });
    }
});

// Highlight features of a specific type near the map center
function highlightNearbyFeatures(type) {
    // This is a simplified version since we don't have access to the Overpass API directly
    // In a real implementation, we would query Overpass API for nearby POIs
    
    alert('This feature uses OpenStreetMap data which requires additional API setup. For now, try searching for specific locations instead.');
}