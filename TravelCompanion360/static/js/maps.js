// Travel Companion - Google Maps Integration

let map;
let markers = [];
let infoWindow;

// Initialize the map
function initMap() {
    // Default center (will be overridden if destinations are available)
    const defaultCenter = { lat: 20, lng: 0 };
    
    // Create the map
    map = new google.maps.Map(document.getElementById("map"), {
        center: defaultCenter,
        zoom: 2,
        styles: getMapStyles(),
        mapTypeControl: false,
        fullscreenControl: true,
        streetViewControl: false,
    });
    
    // Create a single info window instance
    infoWindow = new google.maps.InfoWindow();
    
    // Get destinations from data attribute
    const mapContainer = document.getElementById("map");
    if (mapContainer) {
        const destinationsData = mapContainer.getAttribute("data-destinations");
        
        if (destinationsData) {
            try {
                const destinations = JSON.parse(destinationsData);
                if (destinations && destinations.length > 0) {
                    // Add markers for each destination
                    destinations.forEach(destination => {
                        addMarker(destination);
                    });
                    
                    // If we have destinations, center on the first one
                    if (destinations.length > 0) {
                        map.setCenter({ lat: destinations[0].lat, lng: destinations[0].lng });
                        map.setZoom(5);
                    }
                    
                    // Create bounds to fit all markers
                    if (destinations.length > 1) {
                        const bounds = new google.maps.LatLngBounds();
                        markers.forEach(marker => {
                            bounds.extend(marker.getPosition());
                        });
                        map.fitBounds(bounds);
                    }
                }
            } catch (error) {
                console.error("Error parsing destinations data:", error);
            }
        }
    }
    
    // Add search box if it exists
    const searchInput = document.getElementById("map-search");
    if (searchInput) {
        // Create the search box and link it to the UI element
        const searchBox = new google.maps.places.SearchBox(searchInput);
        
        // Bias the SearchBox results towards current map's viewport
        map.addListener("bounds_changed", () => {
            searchBox.setBounds(map.getBounds());
        });
        
        // Listen for the event fired when the user selects a prediction and retrieve
        // more details for that place
        searchBox.addListener("places_changed", () => {
            const places = searchBox.getPlaces();
            
            if (places.length === 0) {
                return;
            }
            
            // Clear existing markers
            clearMarkers();
            
            // For each place, get the icon, name and location
            const bounds = new google.maps.LatLngBounds();
            
            places.forEach(place => {
                if (!place.geometry || !place.geometry.location) {
                    console.log("Returned place contains no geometry");
                    return;
                }
                
                // Add a marker for this place
                const marker = new google.maps.Marker({
                    map,
                    title: place.name,
                    position: place.geometry.location,
                    animation: google.maps.Animation.DROP,
                    icon: {
                        url: 'https://maps.google.com/mapfiles/ms/icons/blue-dot.png'
                    }
                });
                
                markers.push(marker);
                
                // Add click event to marker
                marker.addListener("click", () => {
                    // Create content for info window
                    let content = `<div class="info-window">
                        <h3>${place.name}</h3>`;
                    
                    if (place.formatted_address) {
                        content += `<p>${place.formatted_address}</p>`;
                    }
                    
                    if (place.photos && place.photos.length > 0) {
                        content += `<img src="${place.photos[0].getUrl({maxWidth: 200, maxHeight: 200})}" 
                                      alt="${place.name}" class="info-window-img">`;
                    }
                    
                    content += `<a href="https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(place.name)}" 
                                 target="_blank" class="btn btn-primary btn-sm mt-2">View on Google Maps</a>
                               </div>`;
                    
                    infoWindow.setContent(content);
                    infoWindow.open(map, marker);
                });
                
                if (place.geometry.viewport) {
                    // Only geocodes have viewport
                    bounds.union(place.geometry.viewport);
                } else {
                    bounds.extend(place.geometry.location);
                }
            });
            
            map.fitBounds(bounds);
        });
    }
    
    // Add nearby search functionality for hotels if button exists
    const findHotelsBtn = document.getElementById("find-nearby-hotels");
    if (findHotelsBtn) {
        findHotelsBtn.addEventListener("click", () => {
            // Get the current center of the map
            const center = map.getCenter();
            findNearbyPlaces(center, "lodging");
        });
    }
    
    // Add nearby search functionality for car rentals if button exists
    const findCarRentalsBtn = document.getElementById("find-nearby-car-rentals");
    if (findCarRentalsBtn) {
        findCarRentalsBtn.addEventListener("click", () => {
            // Get the current center of the map
            const center = map.getCenter();
            findNearbyPlaces(center, "car_rental");
        });
    }
}

// Add a marker to the map
function addMarker(destination) {
    const marker = new google.maps.Marker({
        position: { lat: destination.lat, lng: destination.lng },
        map: map,
        title: destination.name,
        animation: google.maps.Animation.DROP
    });
    
    markers.push(marker);
    
    // Add click event to marker
    marker.addListener("click", () => {
        // Create content for info window
        const content = `
            <div class="info-window">
                <h3>${destination.name}</h3>
                <p>${destination.country}</p>
                <a href="/hotels?destination=${encodeURIComponent(destination.name)}" class="btn btn-primary btn-sm">Find Hotels</a>
            </div>
        `;
        
        infoWindow.setContent(content);
        infoWindow.open(map, marker);
    });
}

// Clear all markers from the map
function clearMarkers() {
    markers.forEach(marker => {
        marker.setMap(null);
    });
    markers = [];
}

// Find nearby places of a specific type
function findNearbyPlaces(location, type) {
    // Create a PlacesService
    const service = new google.maps.places.PlacesService(map);
    
    // Define the request
    const request = {
        location: location,
        radius: 5000, // 5km
        type: type
    };
    
    // Clear existing markers
    clearMarkers();
    
    // Perform the nearby search
    service.nearbySearch(request, (results, status) => {
        if (status === google.maps.places.PlacesServiceStatus.OK && results) {
            // Create bounds to fit all results
            const bounds = new google.maps.LatLngBounds();
            
            // Create markers for each result
            results.forEach((place, i) => {
                if (place.geometry && place.geometry.location) {
                    // Use timeout to animate the markers appearing one by one
                    setTimeout(() => {
                        const marker = new google.maps.Marker({
                            position: place.geometry.location,
                            map: map,
                            title: place.name,
                            animation: google.maps.Animation.DROP,
                            icon: {
                                url: type === 'lodging' 
                                    ? 'https://maps.google.com/mapfiles/ms/icons/blue-dot.png'
                                    : 'https://maps.google.com/mapfiles/ms/icons/green-dot.png'
                            }
                        });
                        
                        markers.push(marker);
                        
                        // Add click event to marker
                        marker.addListener("click", () => {
                            // Get more details about the place
                            service.getDetails({ placeId: place.place_id }, (placeDetails, detailsStatus) => {
                                if (detailsStatus === google.maps.places.PlacesServiceStatus.OK) {
                                    // Create content for info window
                                    let content = `<div class="info-window">
                                        <h3>${placeDetails.name}</h3>`;
                                    
                                    if (placeDetails.vicinity) {
                                        content += `<p>${placeDetails.vicinity}</p>`;
                                    }
                                    
                                    if (placeDetails.rating) {
                                        content += `<div class="place-rating">
                                            <span class="stars">★</span> ${placeDetails.rating.toFixed(1)}
                                        </div>`;
                                    }
                                    
                                    if (placeDetails.photos && placeDetails.photos.length > 0) {
                                        content += `<img src="${placeDetails.photos[0].getUrl({maxWidth: 200, maxHeight: 150})}" 
                                                      alt="${placeDetails.name}" class="info-window-img">`;
                                    }
                                    
                                    if (placeDetails.website) {
                                        content += `<a href="${placeDetails.website}" target="_blank" class="btn btn-primary btn-sm mt-2">Visit Website</a>`;
                                    }
                                    
                                    content += `<a href="https://www.google.com/maps/place/?q=place_id:${placeDetails.place_id}" 
                                                 target="_blank" class="btn btn-secondary btn-sm mt-2 ${placeDetails.website ? 'ml-2' : ''}">View on Google Maps</a>
                                               </div>`;
                                    
                                    infoWindow.setContent(content);
                                    infoWindow.open(map, marker);
                                }
                            });
                        });
                        
                        bounds.extend(place.geometry.location);
                        
                        // Fit the map to the bounds after all markers are added
                        if (i === results.length - 1) {
                            map.fitBounds(bounds);
                        }
                    }, i * 50); // Stagger the appearance of markers
                }
            });
        }
    });
}

// Get coordinates for a location using the backend API
function getCoordinates(location, callback) {
    fetch(`/api/coordinates?location=${encodeURIComponent(location)}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Location not found');
            }
            return response.json();
        })
        .then(data => {
            callback(data);
        })
        .catch(error => {
            console.error('Error getting coordinates:', error);
            alert('Could not find the location. Please try a different search term.');
        });
}

// Custom map styles for a travel-themed look
function getMapStyles() {
    return [
        {
            "featureType": "administrative",
            "elementType": "labels.text.fill",
            "stylers": [
                {
                    "color": "#444444"
                }
            ]
        },
        {
            "featureType": "landscape",
            "elementType": "all",
            "stylers": [
                {
                    "color": "#f2f2f2"
                }
            ]
        },
        {
            "featureType": "poi",
            "elementType": "all",
            "stylers": [
                {
                    "visibility": "off"
                }
            ]
        },
        {
            "featureType": "road",
            "elementType": "all",
            "stylers": [
                {
                    "saturation": -100
                },
                {
                    "lightness": 45
                }
            ]
        },
        {
            "featureType": "road.highway",
            "elementType": "all",
            "stylers": [
                {
                    "visibility": "simplified"
                }
            ]
        },
        {
            "featureType": "road.arterial",
            "elementType": "labels.icon",
            "stylers": [
                {
                    "visibility": "off"
                }
            ]
        },
        {
            "featureType": "transit",
            "elementType": "all",
            "stylers": [
                {
                    "visibility": "off"
                }
            ]
        },
        {
            "featureType": "water",
            "elementType": "all",
            "stylers": [
                {
                    "color": "#1a73e8"
                },
                {
                    "visibility": "on"
                }
            ]
        }
    ];
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
                getCoordinates(location, function(coords) {
                    // Center map on the location
                    map.setCenter(coords);
                    map.setZoom(13);
                    
                    // Add a marker at the location
                    const marker = new google.maps.Marker({
                        position: coords,
                        map: map,
                        title: location,
                        animation: google.maps.Animation.DROP
                    });
                    
                    // Clear any previous markers and add this one
                    clearMarkers();
                    markers.push(marker);
                    
                    // Add click event to marker
                    marker.addListener("click", () => {
                        const content = `
                            <div class="info-window">
                                <h3>${location}</h3>
                                <a href="/hotels?destination=${encodeURIComponent(location)}" class="btn btn-primary btn-sm">Find Hotels</a>
                            </div>
                        `;
                        
                        infoWindow.setContent(content);
                        infoWindow.open(map, marker);
                    });
                });
            }
        });
    }
});
