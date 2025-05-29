document.addEventListener('DOMContentLoaded', function() {
    // Set current year in footer
    const currentYearSpan = document.getElementById('currentYear');
    if (currentYearSpan) {
        currentYearSpan.textContent = new Date().getFullYear();
    }

    // Mobile navigation toggle
    const mobileNavToggle = document.querySelector('.mobile-nav-toggle');
    const mainNav = document.querySelector('.main-nav');
    if (mobileNavToggle && mainNav) {
        mobileNavToggle.addEventListener('click', () => {
            mainNav.classList.toggle('active');
            mobileNavToggle.classList.toggle('active');
            const isExpanded = mainNav.classList.contains('active');
            mobileNavToggle.setAttribute('aria-expanded', isExpanded);
        });
    }
    
    // Get search parameters from URL and flight results from session storage
    const urlParams = new URLSearchParams(window.location.search);
    const searchCriteria = JSON.parse(sessionStorage.getItem('searchCriteria') || '{}');
    let flightOffers = JSON.parse(sessionStorage.getItem('flightSearchResults') || '[]');

    updateSearchSummary(searchCriteria);
    displayFlightResults(flightOffers, searchCriteria);
    setupSortingControls(flightOffers, searchCriteria);
    setupFilteringControls(flightOffers, searchCriteria);

    const modifySearchBtn = document.getElementById('modify-search-btn');
    if (modifySearchBtn) {
        modifySearchBtn.addEventListener('click', () => {
            // Construct query params from searchCriteria to repopulate the form
            const queryParams = new URLSearchParams();
            if (searchCriteria.tripType) queryParams.set('tripType', searchCriteria.tripType);
            
            if (searchCriteria.odSegments && searchCriteria.odSegments.length > 0) {
                searchCriteria.odSegments.forEach((segment, index) => {
                    queryParams.set(`origin-${index}`, segment.Origin);
                    queryParams.set(`destination-${index}`, segment.Destination);
                    queryParams.set(`departureDate-${index}`, segment.DepartureDate);
                    if (segment.ReturnDate) {
                         queryParams.set(`returnDate-${index}`, segment.ReturnDate);
                    }
                });
            }
            queryParams.set('adults', searchCriteria.passengers?.adults || 1);
            queryParams.set('children', searchCriteria.passengers?.children || 0);
            queryParams.set('infants', searchCriteria.passengers?.infants || 0);
            queryParams.set('cabinClass', searchCriteria.cabinClass || 'ECONOMY');

            window.location.href = `index.html?${queryParams.toString()}`;
        });
    }
});

function updateSearchSummary(criteria) {
    const summaryDetails = document.getElementById('search-summary-details');
    if (!summaryDetails) return;

    const titleEl = summaryDetails.querySelector('.summary-title');
    const routeEl = summaryDetails.querySelector('.summary-route');
    const datesEl = summaryDetails.querySelector('.summary-dates');
    const passengersEl = summaryDetails.querySelector('.summary-passengers');
    const cabinEl = summaryDetails.querySelector('.summary-cabin');

    if (!criteria || Object.keys(criteria).length === 0) {
        if(routeEl) routeEl.textContent = 'Search details not available.';
        return;
    }
    
    let routeText = '';
    let datesText = '';

    if (criteria.odSegments && criteria.odSegments.length > 0) {
        const firstSegment = criteria.odSegments[0];
        routeText = `${firstSegment.Origin} → ${firstSegment.Destination}`;
        datesText = `Depart: ${formatDisplayDate(firstSegment.DepartureDate)}`;
        if (criteria.tripType === 'round-trip' && firstSegment.ReturnDate) {
            routeText += ` (Round Trip)`;
            datesText += ` | Return: ${formatDisplayDate(firstSegment.ReturnDate)}`;
        } else if (criteria.tripType === 'multi-city') {
            routeText = `Multi-City Trip (${criteria.odSegments.length} legs)`;
            // Could list all legs if desired
            datesText = `Starting: ${formatDisplayDate(firstSegment.DepartureDate)}`;
        }
    }

    const passengers = criteria.passengers || { adults: 1, children: 0, infants: 0 };
    let passengerText = `${passengers.adults} Adult${passengers.adults !== 1 ? 's' : ''}`;
    if (passengers.children > 0) passengerText += `, ${passengers.children} Child${passengers.children !== 1 ? 'ren' : ''}`;
    if (passengers.infants > 0) passengerText += `, ${passengers.infants} Infant${passengers.infants !== 1 ? 's' : ''}`;

    const cabinClassText = {
        ECONOMY: 'Economy',
        PREMIUM_ECONOMY: 'Premium Economy',
        BUSINESS: 'Business',
        FIRST: 'First Class'
    }[criteria.cabinClass?.toUpperCase()] || 'Economy';

    if(titleEl) titleEl.textContent = criteria.tripType ? `${criteria.tripType.replace('_', ' ')} Flight Search` : 'Your Search';
    if(routeEl) routeEl.textContent = routeText;
    if(datesEl) datesEl.innerHTML = `<svg class="icon" viewBox="0 0 24 24"><path fill="currentColor" d="M17 13h-5v5h5v-5zM16 2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2h-1V2h-2zm3 18H5V9h14v11z"></path></svg> ${datesText}`;
    if(passengersEl) passengersEl.innerHTML = `<svg class="icon" viewBox="0 0 24 24"><path fill="currentColor" d="M16.5 12c1.38 0 2.5-1.12 2.5-2.5S17.88 7 16.5 7C15.12 7 14 8.12 14 9.5s1.12 2.5 2.5 2.5zM9 11c1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3 1.34 3 3 3zm7.5 3c-1.83 0-5.5.92-5.5 2.75V19h11v-2.25c0-1.83-3.67-2.75-5.5-2.75zM9 13c-2.33 0-7 1.17-7 3.5V19h7v-2.25c0-.85.33-2.34 2.37-3.47C10.5 13.1 9.66 13 9 13z"/></svg> ${passengerText}`;
    if(cabinEl) cabinEl.innerHTML = `<svg class="icon" viewBox="0 0 24 24"><path fill="currentColor" d="M4 18v3h3v-3h10v3h3v-6H4zm15-8h3v3h-3zM2 10h3v3H2zm15 3H7V5c0-1.1.9-2 2-2h6c1.1 0 2 .9 2 2v8z"></path></svg> ${cabinClassText}`;
}


function displayFlightResults(offers, searchCriteria) {
    const container = document.getElementById('results-container');
    const loadingPlaceholder = document.querySelector('.loading-results-placeholder');
    const resultsCountEl = document.getElementById('results-count');

    if (loadingPlaceholder) loadingPlaceholder.style.display = 'none';
    if (!container) return;

    container.innerHTML = ''; // Clear previous results or loading

    if (!Array.isArray(offers) || offers.length === 0) {
        container.innerHTML = `
            <div class="no-flights-found">
                <img src="assets/images/no-results-icon.svg" alt="No flights found" class="no-results-icon">
                <h3>No Flights Found</h3>
                <p>We couldn't find any flights matching your criteria. Try adjusting your search or filters.</p>
                <button class="primary-button" id="no-results-modify-search">Modify Search</button>
            </div>`;
        if(resultsCountEl) resultsCountEl.textContent = "0 flights found.";
        document.getElementById('no-results-modify-search').addEventListener('click', () => {
            window.location.href = 'index.html'; // Or pass params like in updateSearchSummary
        });
        return;
    }

    // Dynamically populate airline filters
    populateAirlineFilters(offers);
    
    // Default sort or apply current sort
    const sortSelect = document.getElementById('sort-results');
    const sortBy = sortSelect ? sortSelect.value : 'duration-asc';
    sortAndRenderResults(offers, sortBy, searchCriteria);

    if(resultsCountEl) resultsCountEl.textContent = `${offers.length} flight${offers.length !== 1 ? 's' : ''} found.`;
}

function createFlightCardElement(offer, offerIndex, searchCriteria) {
    const card = document.createElement('div');
    card.className = 'flight-card';

    // Data attributes for sorting/filtering
    const totalDurationMinutes = calculateTotalOfferDuration(offer.segments);
    card.dataset.price = offer.price.amount;
    card.dataset.duration = totalDurationMinutes;
    card.dataset.airline = offer.airline?.toUpperCase() || 'UNKNOWN';
    card.dataset.stops = (offer.segments?.length || 1) - 1; // Simplistic stop count
    card.dataset.departureTime = getEarliestDeparture(offer.segments);
    // card.dataset.arrivalTime = getLatestArrival(offer.segments); // If needed for sorting

    const passengerCount = (searchCriteria.passengers?.adults || 1) + 
                           (searchCriteria.passengers?.children || 0) +
                           (searchCriteria.passengers?.infants || 0);
    const pricePerPaxText = passengerCount > 0 ? `Total for ${passengerCount} passenger${passengerCount > 1 ? 's' : ''}` : 'Total Price';


    let segmentsHtml = '<div class="flight-itinerary-details">';
    
    // Group segments by direction (e.g., Outbound, Return) if applicable
    // For now, assuming all segments in offer.segments are part of one journey or a simple round trip
    // A more complex grouping might be needed for true multi-city or complex round trips.
    
    let currentLegTitle = searchCriteria.tripType === 'round-trip' && offer.segments.length > 1 ? "Outbound" : "";
    let hasRenderedFirstLegTitle = false;

    offer.segments.forEach((segment, index) => {
        if (searchCriteria.tripType === 'round-trip' && offer.segments.length > 1) {
            // Heuristic: if there's a significant time gap or airport change that implies a return
            // This is a simplification. Real round trip detection is complex from flat segment lists.
            // For now, let's assume first half is outbound, second is return if segments > 1
            if (index === 0 && !hasRenderedFirstLegTitle) {
                 segmentsHtml += `<h4 class="segment-group-title">Outbound</h4>`;
                 hasRenderedFirstLegTitle = true;
            } else if (index >= Math.ceil(offer.segments.length / 2) && currentLegTitle === "Outbound") {
                segmentsHtml += `<h4 class="segment-group-title">Return</h4>`;
                currentLegTitle = "Return";
            }
        }

        const departureDate = formatDisplayDate(segment.departure_time);
        const departureTime = formatDisplayTime(segment.departure_time);
        const arrivalDate = formatDisplayDate(segment.arrival_time);
        const arrivalTime = formatDisplayTime(segment.arrival_time);
        const duration = calculateSegmentDuration(segment.departure_time, segment.arrival_time);

        segmentsHtml += `
            <div class="flight-segment-card">
                <div class="segment-departure">
                    <div class="segment-time">${departureTime}</div>
                    <div class="segment-airport">${segment.origin}</div>
                    <div class="segment-date">${departureDate}</div>
                </div>
                <div class="segment-journey-visual">
                    <div class="journey-duration">${duration}</div>
                    <div class="journey-line"></div>
                    <div class="journey-airline-fn">${segment.airline} ${segment.flight_number}</div>
                    ${offer.segments.length > 1 && index < offer.segments.length -1 ? `<div class="journey-stops">${(offer.segments.length -1) === 1 ? "1 Stop" : (offer.segments.length -1) + " Stops"} </div>` : '<div class="journey-stops">Non-stop</div>'}
                </div>
                <div class="segment-arrival">
                    <div class="segment-time">${arrivalTime}</div>
                    <div class="segment-airport">${segment.destination}</div>
                    <div class="segment-date">${arrivalDate}</div>
                </div>
            </div>
        `;
    });
    segmentsHtml += '</div>'; // Close flight-itinerary-details

    card.innerHTML = `
        <div class="flight-card-header">
            <div class="airline-info">
                <img src="https://logo.clearbit.com/${(offer.airline || 'default').toLowerCase()}.com" 
                     alt="${offer.airline || 'Airline'} logo" 
                     class="airline-logo"
                     onerror="this.onerror=null; this.src='assets/images/default-airline-logo.png';">
                <div class="airline-details">
                    <span class="name">${offer.airline_name || offer.airline || 'Airline Name'}</span>
                    <!-- Flight number can be more complex for multi-leg, display primary or first -->
                    <span class="flight-number">${offer.segments[0]?.flight_number ? `Flight ${offer.segments[0].airline} ${offer.segments[0].flight_number}` : ''}</span>
                </div>
            </div>
            <div class="price-action-section">
                <div class="flight-price">${formatCurrency(offer.price.amount, offer.price.currency)}</div>
                <div class="price-per-passenger">${pricePerPaxText}</div>
                <button class="select-flight-btn" data-offer-id="${offer.id}" data-offer-index="${offerIndex}">
                    Select Flight
                    <svg class="icon" viewBox="0 0 24 24"><path fill="currentColor" d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6z"></path></svg>
                </button>
            </div>
        </div>
        ${segmentsHtml}
        <!-- Optional: Footer for details toggle -->
        <!--
        <div class="flight-card-footer">
            <button class="toggle-details-btn">View Details</button>
        </div>
        <div class="flight-details-expanded" style="display: none;">
            <p>Additional flight details here...</p>
        </div>
        -->
    `;

    card.querySelector('.select-flight-btn').addEventListener('click', function() {
        selectFlight(this.dataset.offerId, offer);
    });
    
    // Optional: Add event listener for toggling details
    // const toggleBtn = card.querySelector('.toggle-details-btn');
    // if (toggleBtn) {
    //     toggleBtn.addEventListener('click', () => {
    //         const detailsPanel = card.querySelector('.flight-details-expanded');
    //         if (detailsPanel) {
    //             detailsPanel.style.display = detailsPanel.style.display === 'none' ? 'block' : 'none';
    //         }
    //     });
    // }

    return card;
}

function populateAirlineFilters(offers) {
    const airlineFiltersContainer = document.getElementById('airline-filters-container');
    if (!airlineFiltersContainer) return;

    const airlines = [...new Set(offers.map(offer => offer.airline).filter(Boolean))];
    airlines.sort();

    if (airlines.length > 0) {
        airlineFiltersContainer.innerHTML = ''; // Clear loading/previous
        airlines.forEach(airlineCode => {
            const label = document.createElement('label');
            label.className = 'filter-checkbox';
            label.innerHTML = `
                <input type="checkbox" name="airline" value="${airlineCode.toUpperCase()}" class="filter-toggle"> 
                ${airlineCode} {/* Ideally, map code to name if available */}
            `;
            airlineFiltersContainer.appendChild(label);
        });
    } else {
        airlineFiltersContainer.innerHTML = '<p class="no-filters-available">No airline filters available.</p>';
    }
    // Re-attach event listeners if filters are dynamically added
    setupFilterEventListeners();
}

function setupFilterEventListeners() {
    document.querySelectorAll('.filter-toggle').forEach(toggle => {
        // Remove existing to prevent duplicates if called multiple times
        toggle.removeEventListener('change', handleFilterChange); 
        toggle.addEventListener('change', handleFilterChange);
    });
    const priceRangeSlider = document.getElementById('price-range');
    if (priceRangeSlider) {
        priceRangeSlider.removeEventListener('input', handleFilterChange);
        priceRangeSlider.addEventListener('input', () => {
            // Update price display
            const minPriceDisplay = document.getElementById('min-price-display');
            const maxPriceDisplay = document.getElementById('max-price-display'); // Assuming you want to filter by max selected
            if(minPriceDisplay) minPriceDisplay.textContent = `$${priceRangeSlider.value}`; // Or format currency
            // For a range, you'd have two sliders or inputs. This is a single max price slider.
            if(maxPriceDisplay && priceRangeSlider.id === 'price-range') maxPriceDisplay.textContent = `$${priceRangeSlider.value}`;
             handleFilterChange();
        });
    }
     const applyFiltersBtn = document.querySelector('.apply-filters-btn');
    if (applyFiltersBtn) {
        applyFiltersBtn.removeEventListener('click', handleFilterChange); // Prevent multiple listeners
        applyFiltersBtn.addEventListener('click', handleFilterChange);
    }
}

function handleFilterChange() {
    const flightOffers = JSON.parse(sessionStorage.getItem('flightSearchResults') || '[]');
    const searchCriteria = JSON.parse(sessionStorage.getItem('searchCriteria') || '{}');
    applyFiltersAndSort(flightOffers, searchCriteria);
}

function setupSortingControls(initialOffers, searchCriteria) {
    const sortSelect = document.getElementById('sort-results');
    if (!sortSelect) return;

    sortSelect.addEventListener('change', function() {
        // Get current filtered offers if filtering is applied, else use initialOffers
        // For simplicity now, always re-filter and sort from original full list
        const allOffers = JSON.parse(sessionStorage.getItem('flightSearchResults') || '[]');
        applyFiltersAndSort(allOffers, searchCriteria);
    });
}

function setupFilteringControls(initialOffers, searchCriteria) {
    setupFilterEventListeners(); // Initial setup for existing toggles

    // Price range slider display update
    const priceRangeSlider = document.getElementById('price-range');
    const minPriceDisplay = document.getElementById('min-price-display');
    const maxPriceDisplay = document.getElementById('max-price-display');

    if (priceRangeSlider && minPriceDisplay && maxPriceDisplay) {
        // Find min/max prices from offers to set slider limits dynamically
        if (initialOffers.length > 0) {
            const prices = initialOffers.map(o => o.price.amount);
            const minPrice = Math.min(...prices);
            const maxPrice = Math.max(...prices);
            priceRangeSlider.min = Math.floor(minPrice);
            priceRangeSlider.max = Math.ceil(maxPrice);
            priceRangeSlider.value = Math.ceil(maxPrice); // Default to max
            minPriceDisplay.textContent = formatCurrency(parseFloat(priceRangeSlider.min), initialOffers[0].price.currency, 0);
            maxPriceDisplay.textContent = formatCurrency(parseFloat(priceRangeSlider.value), initialOffers[0].price.currency, 0);
        }

        priceRangeSlider.addEventListener('input', () => {
            maxPriceDisplay.textContent = formatCurrency(parseFloat(priceRangeSlider.value), initialOffers.length > 0 ? initialOffers[0].price.currency : 'USD', 0);
            // Filtering is handled by applyFiltersAndSort via common event handler
        });
    }
}

function applyFiltersAndSort(offersToProcess, searchCriteria) {
    // --- Filtering ---
    const activeStopFilters = Array.from(document.querySelectorAll('input[name="stops"]:checked')).map(el => el.value);
    const activeAirlineFilters = Array.from(document.querySelectorAll('input[name="airline"]:checked')).map(el => el.value.toUpperCase());
    const priceRangeSlider = document.getElementById('price-range');
    const maxPrice = priceRangeSlider ? parseFloat(priceRangeSlider.value) : Infinity;
    
    const activeDepartureTimeFilters = Array.from(document.querySelectorAll('input[name="departureTime"]:checked')).map(el => el.value);

    let filteredOffers = offersToProcess.filter(offer => {
        const offerStops = (offer.segments?.length || 1) - 1;
        const offerAirline = offer.airline?.toUpperCase() || 'UNKNOWN';
        const offerPrice = offer.price.amount;
        const offerDepartureTime = new Date(getEarliestDeparture(offer.segments));

        const stopMatch = activeStopFilters.length === 0 || 
                          (activeStopFilters.includes("2+") && offerStops >= 2) ||
                          activeStopFilters.includes(offerStops.toString());
        const airlineMatch = activeAirlineFilters.length === 0 || activeAirlineFilters.includes(offerAirline);
        const priceMatch = offerPrice <= maxPrice;
        
        const departureTimeMatch = activeDepartureTimeFilters.length === 0 || 
            activeDepartureTimeFilters.some(slot => {
                const hour = offerDepartureTime.getHours();
                if (slot === "morning" && hour >= 5 && hour < 12) return true;
                if (slot === "afternoon" && hour >= 12 && hour < 17) return true;
                if (slot === "evening" && hour >= 17 && hour < 21) return true;
                if (slot === "night" && (hour >= 21 || hour < 5)) return true;
                return false;
            });

        return stopMatch && airlineMatch && priceMatch && departureTimeMatch;
    });

    // --- Sorting ---
    const sortSelect = document.getElementById('sort-results');
    const sortBy = sortSelect ? sortSelect.value : 'duration-asc';
    sortAndRenderResults(filteredOffers, sortBy, searchCriteria);
}


function sortAndRenderResults(offersToSort, sortBy, searchCriteria) {
    const container = document.getElementById('results-container');
    if (!container) return;
    container.innerHTML = ''; // Clear for new sorted/filtered results

     const resultsCountEl = document.getElementById('results-count');
    if(resultsCountEl) resultsCountEl.textContent = `${offersToSort.length} flight${offersToSort.length !== 1 ? 's' : ''} found.`;


    if (offersToSort.length === 0) {
         container.innerHTML = `
            <div class="no-flights-found">
                <img src="assets/images/no-results-icon.svg" alt="No flights found" class="no-results-icon">
                <h3>No Flights Found</h3>
                <p>No flights match your current filters. Try adjusting them or modifying your search.</p>
                 <button class="primary-button" id="no-filtered-results-modify-search">Modify Search</button>
            </div>`;
        document.getElementById('no-filtered-results-modify-search').addEventListener('click', () => {
            window.location.href = 'index.html'; 
        });
        return;
    }


    offersToSort.sort((a, b) => {
        switch (sortBy) {
            case 'price-asc':
                return a.price.amount - b.price.amount;
            case 'price-desc':
                return b.price.amount - a.price.amount;
            case 'duration-asc':
                return calculateTotalOfferDuration(a.segments) - calculateTotalOfferDuration(b.segments);
            case 'departure-asc':
                return new Date(getEarliestDeparture(a.segments)) - new Date(getEarliestDeparture(b.segments));
            case 'arrival-asc': // Assuming this means latest arrival of the journey
                 return new Date(getLatestArrival(a.segments)) - new Date(getLatestArrival(b.segments));
            default:
                return 0;
        }
    });

    offersToSort.forEach((offer, index) => {
        const flightCard = createFlightCardElement(offer, index, searchCriteria);
        if (flightCard) {
            container.appendChild(flightCard);
        }
    });
}


function selectFlight(offerId, offerData) {
    // Store the full offer data for the selected flight
    sessionStorage.setItem('selectedFlightOffer', JSON.stringify(offerData));
    // Redirect to a booking page (assuming booking.html)
    window.location.href = `booking.html?offerId=${encodeURIComponent(offerId)}`;
}

// --- Date and Time Helper Functions ---
function formatDisplayDate(isoString) {
    if (!isoString || isoString === "Invalid Date") return "N/A";
    try {
        const date = new Date(isoString);
        if (isNaN(date.getTime())) return "Invalid Date";
        return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
    } catch (e) {
        return "Date Error";
    }
}

function formatDisplayTime(isoString) {
    if (!isoString || isoString === "Invalid Date") return "N/A";
    try {
        const date = new Date(isoString);
        if (isNaN(date.getTime())) return "Invalid Time";
        return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
    } catch (e) {
        return "Time Error";
    }
}

function calculateSegmentDuration(departureIso, arrivalIso) {
    if (!departureIso || !arrivalIso || departureIso === "Invalid Date" || arrivalIso === "Invalid Date") return "N/A";
    try {
        const dep = new Date(departureIso);
        const arr = new Date(arrivalIso);
        if (isNaN(dep.getTime()) || isNaN(arr.getTime())) return "Calc Error";

        let diffMs = arr - dep;
        if (diffMs < 0) diffMs = 0; // Should not happen with valid data

        const hours = Math.floor(diffMs / (1000 * 60 * 60));
        const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
        return `${hours}h ${minutes}m`;
    } catch (e) {
        return "Duration Error";
    }
}

function calculateTotalOfferDuration(segments) {
    if (!Array.isArray(segments) || segments.length === 0) return 0;
    let totalDurationMs = 0;
    try {
        // For simple sum of flight times:
        segments.forEach(seg => {
            const dep = new Date(seg.departure_time);
            const arr = new Date(seg.arrival_time);
            if (!isNaN(dep.getTime()) && !isNaN(arr.getTime()) && arr > dep) {
                totalDurationMs += (arr - dep);
            }
        });
        // If segments represent a journey with layovers, this would be:
        // const firstDep = new Date(segments[0].departure_time);
        // const lastArr = new Date(segments[segments.length - 1].arrival_time);
        // if (!isNaN(firstDep.getTime()) && !isNaN(lastArr.getTime()) && lastArr > firstDep) {
        //     totalDurationMs = lastArr - firstDep;
        // }

    } catch (e) { /* ignore segment parse error for total calculation */ }
    return Math.floor(totalDurationMs / (1000 * 60)); // in minutes
}

function getEarliestDeparture(segments) {
    if (!Array.isArray(segments) || segments.length === 0) return new Date(0).toISOString(); // Epoch for invalid
    try {
        return new Date(segments[0].departure_time).toISOString();
    } catch (e) { return new Date(0).toISOString(); }
}

function getLatestArrival(segments) {
     if (!Array.isArray(segments) || segments.length === 0) return new Date(0).toISOString();
    try {
        return new Date(segments[segments.length - 1].arrival_time).toISOString();
    } catch (e) { return new Date(0).toISOString(); }
}

function formatCurrency(amount, currencyCode = 'USD', fractionDigits = 2) {
    if (typeof amount !== 'number') amount = parseFloat(amount) || 0;
    try {
        return new Intl.NumberFormat('en-IN', { // Using en-IN for Rupee symbol, adjust if needed
            style: 'currency',
            currency: currencyCode,
            minimumFractionDigits: fractionDigits,
            maximumFractionDigits: fractionDigits
        }).format(amount);
    } catch (e) { // Fallback for unknown currency codes
        return `${currencyCode} ${amount.toFixed(fractionDigits)}`;
    }
}
