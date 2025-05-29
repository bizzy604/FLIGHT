/**
 * results.js - Handles the flight search results page functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Set current year in footer
    const currentYearSpan = document.getElementById('currentYear');
    if (currentYearSpan) {
        currentYearSpan.textContent = new Date().getFullYear();
    }
    
    // Get search parameters from URL
    const urlParams = new URLSearchParams(window.location.search);
    const searchParams = {
        origin: urlParams.get('origin') || '',
        destination: urlParams.get('destination') || '',
        departureDate: urlParams.get('departureDate') || '',
        returnDate: urlParams.get('returnDate') || '',
        adults: parseInt(urlParams.get('adults')) || 1,
        children: parseInt(urlParams.get('children')) || 0,
        infants: parseInt(urlParams.get('infants')) || 0,
        cabin: urlParams.get('cabin') || 'Y',
        tripType: urlParams.get('tripType') || 'ONE_WAY'
    };
    
    // Get results from session storage
    const results = JSON.parse(sessionStorage.getItem('flightSearchResults') || '[]');
    const searchCriteria = JSON.parse(sessionStorage.getItem('searchCriteria') || '{}');
    
    // Update search summary
    updateSearchSummary(searchParams, searchCriteria);
    
    // Display results
    displayResults(results, searchParams);
    
    // Set up sorting functionality
    setupSorting();
    
    // Set up filter toggles
    setupFilters();
});

/**
 * Updates the search summary section with the search parameters
 */
function updateSearchSummary(params, criteria) {
    const searchSummary = document.getElementById('search-summary');
    const searchParamsEl = document.getElementById('search-params');
    
    if (!searchSummary || !searchParamsEl) return;
    
    const tripTypeText = {
        'ONE_WAY': 'One Way',
        'ROUND_TRIP': 'Round Trip',
        'MULTI_CITY': 'Multi-City'
    }[params.tripType] || 'One Way';
    
    const cabinClassText = {
        'Y': 'Economy',
        'W': 'Premium Economy',
        'C': 'Business',
        'F': 'First Class'
    }[params.cabin] || 'Economy';
    
    let passengersText = '';
    if (params.adults > 0) passengersText += `${params.adults} Adult${params.adults > 1 ? 's' : ''}`;
    if (params.children > 0) passengersText += `${passengersText ? ', ' : ''}${params.children} Child${params.children > 1 ? 'ren' : ''}`;
    if (params.infants > 0) passengersText += `${passengersText ? ', ' : ''}${params.infants} Infant${params.infants > 1 ? 's' : ''}`;
    
    // Check if we have multi-city segments
    let segmentsHtml = '';
    if (criteria.odSegments && criteria.odSegments.length > 0) {
        segmentsHtml = criteria.odSegments.map((segment, index) => {
            return `
                <div style="margin-bottom: 10px; padding: 10px; background: #f8f9fa; border-radius: 4px;">
                    <div><strong>${index === 0 ? 'Departure' : 'Return'}:</strong> ${formatDate(segment.DepartureDate)}</div>
                    <div>${segment.Origin} → ${segment.Destination}</div>
                </div>
            `;
        }).join('');
    } else {
        segmentsHtml = `
            <div><strong>Departure:</strong> ${formatDate(params.departureDate)}</div>
            ${params.returnDate ? `<div><strong>Return:</strong> ${formatDate(params.returnDate)}</div>` : ''}
        `;
    }
    
    searchSummary.innerHTML = `
        <h2>${params.origin || ''} to ${params.destination || ''}</h2>
        <div style="display: flex; flex-wrap: wrap; gap: 20px; margin-top: 10px;">
            <div><strong>Trip Type:</strong> ${tripTypeText}</div>
            ${segmentsHtml}
            <div><strong>Class:</strong> ${cabinClassText}</div>
            <div><strong>Passengers:</strong> ${passengersText}</div>
        </div>
    `;
}

/**
 * Displays the flight results in the results container
 */
function displayResults(offers, searchParams) {
    const container = document.getElementById('results-container');
    const loadingEl = document.querySelector('.loading');
    
    if (loadingEl) {
        loadingEl.style.display = 'none';
    }
    
    if (!container) return;
    
    if (!Array.isArray(offers) || offers.length === 0) {
        container.innerHTML = `
            <div class="no-flights">
                <h3>No flights found</h3>
                <p>We couldn't find any flights matching your criteria. Please try adjusting your search.</p>
                <a href="index.html" class="select-btn" style="display: inline-block; margin-top: 20px;">Modify Search</a>
            </div>
        `;
        return;
    }
    
    // Clear any existing content
    container.innerHTML = '';
    
    // Sort offers by price (cheapest first) by default
    offers.sort((a, b) => {
        const priceA = a.price?.amount || 0;
        const priceB = b.price?.amount || 0;
        return priceA - priceB;
    });
    
    // Create and append flight cards
    offers.forEach((offer, index) => {
        const flightCard = createFlightCard(offer, index, searchParams);
        if (flightCard) {
            container.appendChild(flightCard);
        }
    });
}

/**
 * Creates a flight card element
 */
function createFlightCard(offer, index, searchParams) {
    if (!offer) return null;
    
    // Format price
    const price = offer.price?.amount || 0;
    const currency = offer.price?.currency || 'USD';
    const formattedPrice = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2
    }).format(price);
    
    // Create segments HTML
    let segmentsHtml = '';
    if (Array.isArray(offer.segments)) {
        offer.segments.forEach((segment, segIndex) => {
            const departureTime = formatTime(segment.departure_time);
            const arrivalTime = formatTime(segment.arrival_time);
            const duration = calculateDuration(segment.departure_time, segment.arrival_time);
            
            segmentsHtml += `
                <div class="segment">
                    <div class="departure">
                        <div class="time">${departureTime}</div>
                        <div class="location">${segment.origin}</div>
                    </div>
                    <div class="duration">
                        <div>${duration}</div>
                        <div style="border-top: 1px solid #dee2e6; margin: 5px 0; width: 50px;"></div>
                        <div>${segment.flight_number || ''}</div>
                    </div>
                    <div class="arrival">
                        <div class="time">${arrivalTime}</div>
                        <div class="location">${segment.destination}</div>
                    </div>
                </div>
            `;
        });
    }
    
    // Create flight card element
    const flightCard = document.createElement('div');
    flightCard.className = 'flight-card';
    flightCard.dataset.price = price;
    flightCard.dataset.duration = calculateTotalDuration(offer.segments || []);
    flightCard.dataset.airline = (offer.airline || '').toLowerCase();
    flightCard.dataset.stops = countStops(offer.segments || []);
    
    flightCard.innerHTML = `
        <div class="flight-header">
            <div style="display: flex; align-items: center;">
                <img src="https://logo.clearbit.com/${offer.airline?.toLowerCase() || 'airline'}.com" 
                     alt="${offer.airline || 'Airline'}" 
                     class="airline-logo" 
                     onerror="this.src='https://via.placeholder.com/40?text='+encodeURIComponent('${offer.airline?.charAt(0) || 'A'}')">
                <div>
                    <h3 style="margin: 0;">${offer.airline || 'Flight'}</h3>
                    <div style="font-size: 0.9em; color: #6c757d;">${offer.flight_number || ''}</div>
                </div>
            </div>
            <div class="price-section">
                <div class="price">${formattedPrice}</div>
                <div class="price-details">${searchParams.adults} Adult${searchParams.adults > 1 ? 's' : ''}</div>
                <button class="select-btn" data-offer-index="${index}">Select</button>
            </div>
        </div>
        <div class="flight-segments">
            ${segmentsHtml}
        </div>
        <div class="flight-details" style="display: none; margin-top: 15px; padding-top: 15px; border-top: 1px solid #eaecef;">
            <h4>Flight Details</h4>
            <p>More details about this flight will be shown here.</p>
        </div>
    `;
    
    // Add click handler for the select button
    const selectBtn = flightCard.querySelector('.select-btn');
    if (selectBtn) {
        selectBtn.addEventListener('click', function() {
            selectFlight(index);
        });
    }
    
    // Add click handler to toggle flight details
    const flightHeader = flightCard.querySelector('.flight-header');
    if (flightHeader) {
        flightHeader.style.cursor = 'pointer';
        flightHeader.addEventListener('click', function() {
            const details = flightCard.querySelector('.flight-details');
            if (details) {
                details.style.display = details.style.display === 'none' ? 'block' : 'none';
            }
        });
    }
    
    return flightCard;
}

/**
 * Sets up sorting functionality for the results
 */
function setupSorting() {
    const sortSelect = document.getElementById('sort-results');
    if (!sortSelect) return;
    
    sortSelect.addEventListener('change', function() {
        const container = document.getElementById('results-container');
        if (!container) return;
        
        const cards = Array.from(container.getElementsByClassName('flight-card'));
        if (cards.length === 0) return;
        
        // Sort cards based on selected option
        cards.sort((a, b) => {
            const sortBy = this.value;
            
            switch(sortBy) {
                case 'price-asc':
                    return parseFloat(a.dataset.price) - parseFloat(b.dataset.price);
                case 'price-desc':
                    return parseFloat(b.dataset.price) - parseFloat(a.dataset.price);
                case 'duration-asc':
                    return parseFloat(a.dataset.duration) - parseFloat(b.dataset.duration);
                case 'departure-asc':
                    // This would require storing departure time in the dataset
                    return 0; // Implement based on your data structure
                default:
                    return 0;
            }
        });
        
        // Re-append cards in sorted order
        cards.forEach(card => container.appendChild(card));
    });
}

/**
 * Sets up filter toggles for the results
 */
function setupFilters() {
    // Implement filter toggles for airlines, stops, etc.
    const filterToggles = document.querySelectorAll('.filter-toggle');
    filterToggles.forEach(toggle => {
        toggle.addEventListener('change', applyFilters);
    });
}

/**
 * Applies all active filters to the results
 */
function applyFilters() {
    // Get all filter values
    const airlineFilters = Array.from(document.querySelectorAll('input[name="airline"]:checked')).map(el => el.value);
    const stopFilters = Array.from(document.querySelectorAll('input[name="stops"]:checked')).map(el => el.value);
    
    // Get all flight cards
    const cards = document.querySelectorAll('.flight-card');
    
    cards.forEach(card => {
        const airline = card.dataset.airline;
        const stops = card.dataset.stops;
        
        // Check if card matches all active filters
        const matchesAirline = airlineFilters.length === 0 || airlineFilters.includes(airline);
        const matchesStops = stopFilters.length === 0 || stopFilters.includes(stops);
        
        // Show/hide card based on filters
        if (matchesAirline && matchesStops) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });
}

/**
 * Handles flight selection
 */
function selectFlight(offerIndex) {
    // Get the selected offer from session storage
    const offers = JSON.parse(sessionStorage.getItem('flightSearchResults') || '[]');
    const selectedOffer = offers[parseInt(offerIndex)];
    
    if (selectedOffer) {
        // Store selected offer for the booking page
        sessionStorage.setItem('selectedFlight', JSON.stringify(selectedOffer));
        
        // Redirect to booking page
        window.location.href = 'booking.html';
    }
}

/**
 * Helper function to format date
 */
function formatDate(dateString) {
    if (!dateString) return '';
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('en-US', options);
}

/**
 * Helper function to format time
 */
function formatTime(dateTimeString) {
    if (!dateTimeString) return '';
    const date = new Date(dateTimeString);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
}

/**
 * Helper function to calculate duration between two times
 */
function calculateDuration(departure, arrival) {
    if (!departure || !arrival) return '';
    
    const dep = new Date(departure);
    const arr = new Date(arrival);
    const diffMs = arr - dep;
    
    if (isNaN(diffMs)) return '';
    
    const hours = Math.floor(diffMs / (1000 * 60 * 60));
    const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    
    return `${hours}h ${minutes}m`;
}

/**
 * Calculates total duration of all segments in minutes
 */
function calculateTotalDuration(segments) {
    if (!Array.isArray(segments) || segments.length === 0) return 0;
    
    let totalMs = 0;
    segments.forEach(segment => {
        if (segment.departure_time && segment.arrival_time) {
            const dep = new Date(segment.departure_time);
            const arr = new Date(segment.arrival_time);
            totalMs += (arr - dep);
        }
    });
    
    return Math.floor(totalMs / (1000 * 60)); // Convert to minutes
}

/**
 * Counts the number of stops in a flight
 */
function countStops(segments) {
    if (!Array.isArray(segments)) return '0';
    return Math.max(0, segments.length - 1).toString();
}
