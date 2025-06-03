
// results.js - Handles the flight search results page functionality

document.addEventListener('DOMContentLoaded', function() {
    // Global elements
    const resultsContainer = document.getElementById('results-container');
    const resultsCountText = document.getElementById('results-count');
    const loadingPlaceholder = document.querySelector('.loading-results-placeholder');
    const noFlightsFoundPlaceholder = createNoFlightsFoundElement(); 
    
    const searchSummaryDetailsEl = document.getElementById('search-summary-details');
    const modifySearchBtn = document.getElementById('modify-search-btn');
    const modifySearchFromNoResultsBtn = noFlightsFoundPlaceholder.querySelector('#modify-search-from-no-results');

    // Filters
    const stopFiltersCheckboxes = document.querySelectorAll('input[name="stops"]');
    const priceRangeSlider = document.getElementById('price-range');
    const minPriceDisplay = document.getElementById('min-price-display');
    const maxPriceDisplay = document.getElementById('max-price-display');
    const airlineFiltersContainer = document.getElementById('airline-filters-container');
    const departureTimeFiltersCheckboxes = document.querySelectorAll('input[name="departureTime"]');
    const applyFiltersBtn = document.querySelector('.apply-filters-btn');

    // Sorting
    const sortResultsSelect = document.getElementById('sort-results');

    let allFlightOffers = []; // Store all fetched offers for filtering/sorting
    let currentSearchParams = {}; // Store current search parameters

    // Initialize Page
    initializeResultsPage();
    setupMobileNav(); // Ensure mobile nav works

    function initializeResultsPage() {
        console.log("Initializing results page...");
        // Set current year in footer
        const currentYearSpan = document.getElementById('currentYear');
        if (currentYearSpan) {
            currentYearSpan.textContent = new Date().getFullYear();
        }

        // Append the no-flights-found placeholder to the container
        if (resultsContainer && !resultsContainer.querySelector('.no-flights-found')) {
            resultsContainer.appendChild(noFlightsFoundPlaceholder);
        }
        
        currentSearchParams = getSearchParamsFromStorage();
        console.log("Retrieved searchParams:", currentSearchParams);

        if (!currentSearchParams || Object.keys(currentSearchParams).length === 0 || !currentSearchParams.segments || currentSearchParams.segments.length === 0) {
            console.error('Search parameters not found or invalid in localStorage.');
            displaySearchSummaryError('Search parameters are missing. Please try a new search.');
            if (loadingPlaceholder) loadingPlaceholder.classList.add('hidden');
            renderFlightResults([]); 
            return;
        }

        displaySearchSummary(currentSearchParams);
        fetchFlightResults(currentSearchParams);
        setupEventListeners();
    }
    
    function getSearchParamsFromStorage() {
        // First try to get from URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.toString()) {
            const params = {
                origin: urlParams.get('origin'),
                destination: urlParams.get('destination'),
                departureDate: urlParams.get('departureDate'),
                returnDate: urlParams.get('returnDate'),
                tripType: urlParams.get('tripType') || 'ONE_WAY',
                adults: parseInt(urlParams.get('adults') || '1'),
                children: parseInt(urlParams.get('children') || '0'),
                infants: parseInt(urlParams.get('infants') || '0'),
                cabinClass: urlParams.get('cabin') || 'ECONOMY'
            };
            
            // For round-trip, add the return segment
            if (params.tripType === 'ROUND_TRIP' && params.returnDate) {
                params.segments = [
                    {
                        Origin: params.origin,
                        Destination: params.destination,
                        DepartureDate: params.departureDate
                    },
                    {
                        Origin: params.destination,
                        Destination: params.origin,
                        DepartureDate: params.returnDate
                    }
                ];
            } else {
                // For one-way
                params.segments = [{
                    Origin: params.origin,
                    Destination: params.destination,
                    DepartureDate: params.departureDate
                }];
            }
            
            // Save to localStorage for future use
            localStorage.setItem('flightSearchParams', JSON.stringify(params));
            return params;
        }

        // Fall back to localStorage
        const savedParams = localStorage.getItem('flightSearchParams');
        if (savedParams) {
            try {
                const params = JSON.parse(savedParams);
                // Ensure segments are properly formatted
                if (params.tripType === 'ROUND_TRIP' && (!params.segments || params.segments.length < 2)) {
                    if (params.returnDate) {
                        params.segments = [
                            {
                                Origin: params.origin,
                                Destination: params.destination,
                                DepartureDate: params.departureDate
                            },
                            {
                                Origin: params.destination,
                                Destination: params.origin,
                                DepartureDate: params.returnDate
                            }
                        ];
                    }
                } else if (!params.segments) {
                    params.segments = [{
                        Origin: params.origin,
                        Destination: params.destination,
                        DepartureDate: params.departureDate
                    }];
                }
                return params;
            } catch (e) {
                console.error("Error parsing flightSearchParams from localStorage:", e);
            }
        }
        
        return null;
    }

    function setupEventListeners() {
        if (modifySearchBtn) {
            modifySearchBtn.addEventListener('click', () => window.location.href = 'index.html');
        }
        if (modifySearchFromNoResultsBtn) {
            modifySearchFromNoResultsBtn.addEventListener('click', () => window.location.href = 'index.html');
        }

        if (applyFiltersBtn) {
            applyFiltersBtn.addEventListener('click', applyFiltersAndSort);
        } else { // Fallback: if no apply button, filter on individual changes
            stopFiltersCheckboxes.forEach(filter => filter.addEventListener('change', applyFiltersAndSort));
            departureTimeFiltersCheckboxes.forEach(filter => filter.addEventListener('change', applyFiltersAndSort));
            // Airline filters listeners are added in populateAirlineFilters
        }

        if (priceRangeSlider) {
            priceRangeSlider.addEventListener('input', () => {
                if (maxPriceDisplay) {
                    maxPriceDisplay.textContent = formatCurrency(parseInt(priceRangeSlider.value), 'INR');
                }
            });
            // Apply filter on 'change' (release) or via Apply button
            if (!applyFiltersBtn) {
                priceRangeSlider.addEventListener('change', applyFiltersAndSort);
            }
             // Initial display for price range
            if (minPriceDisplay && maxPriceDisplay) {
                minPriceDisplay.textContent = formatCurrency(0, 'INR'); 
                maxPriceDisplay.textContent = formatCurrency(parseInt(priceRangeSlider.max), 'INR'); 
            }
        }

        if (sortResultsSelect) {
            sortResultsSelect.addEventListener('change', applyFiltersAndSort);
        }
    }

    function createNoFlightsFoundElement() {
        const div = document.createElement('div');
        div.className = 'no-flights-found hidden'; // Initially hidden
        div.innerHTML = `
            <div class="no-results-icon" style="width:80px; height:80px; margin-bottom:1rem; display:flex; align-items:center; justify-content:center; font-size:40px; color:#718096;">
                ✈️
            </div>
            <h3>No Flights Found</h3>
            <p>We couldn't find any flights matching your criteria. Try adjusting your search or filters.</p>
            <button class="primary-button" id="modify-search-from-no-results">Modify Search</button>
        `;
        return div;
    }
    
    function displaySearchSummaryError(message) {
        if (!searchSummaryDetailsEl) return;
        searchSummaryDetailsEl.innerHTML = `<p class="error-message">${message}</p>`;
    }

    function displaySearchSummary(params) {
        if (!searchSummaryDetailsEl || !params || !params.segments) {
            console.warn("Search summary cannot be displayed. Params or segments missing:", params);
            displaySearchSummaryError("Could not load search summary.");
            return;
        }

        const tripType = params.tripType || 'ONE_WAY';
        const cabinClass = params.cabinClass || 'ECONOMY';
        const firstSegment = params.segments[0];
        
        if (!firstSegment) {
            console.warn("No segments found in params:", params);
            return;
        }

        // Format route information
        let routeName = '';
        if (tripType === 'ROUND_TRIP' && params.segments.length >= 2) {
            routeName = firstSegment.Origin + ' ↔ ' + firstSegment.Destination;
        } else {
            routeName = firstSegment.Origin + ' → ' + firstSegment.Destination;
        }

        // Format dates
        const departureDate = firstSegment.DepartureDate ? new Date(firstSegment.DepartureDate) : null;
        let returnDate = null;
        
        if (tripType === 'ROUND_TRIP' && params.segments.length >= 2) {
            returnDate = new Date(params.segments[1].DepartureDate);
        }

        const formattedDepartureDate = departureDate 
            ? departureDate.toLocaleDateString('en-US', { 
                weekday: 'short', 
                month: 'short', 
                day: 'numeric' 
            })
            : 'N/A';

        let formattedReturnDate = '';
        if (returnDate) {
            formattedReturnDate = returnDate.toLocaleDateString('en-US', { 
                weekday: 'short', 
                month: 'short', 
                day: 'numeric' 
            });
        }

        // Format passengers
        const adults = params.adults || 0;
        const children = params.children || 0;
        const infants = params.infants || 0;
        
        let passengersText = '';
        if (adults > 0) passengersText += adults + ' ' + (adults > 1 ? 'Adults' : 'Adult');
        if (children > 0) passengersText += ', ' + children + ' ' + (children > 1 ? 'Children' : 'Child');
        if (infants > 0) passengersText += ', ' + infants + ' ' + (infants > 1 ? 'Infants' : 'Infant');

        // Format cabin class
        const cabinText = cabinClass
            .toLowerCase()
            .split(' ')
            .map(function(word) { 
                return word.charAt(0).toUpperCase() + word.slice(1); 
            })
            .join(' ');

        // Format trip type for display
        let tripTypeText = '';
        switch(tripType) {
            case 'ROUND_TRIP':
                tripTypeText = 'Round Trip';
                break;
            case 'MULTI_CITY':
                tripTypeText = 'Multi-City';
                break;
            default:
                tripTypeText = 'One Way';
        }

        // Create elements using DOM methods
        const contentDiv = document.createElement('div');
        contentDiv.className = 'search-summary-content';

        const routeDiv = document.createElement('div');
        routeDiv.className = 'search-summary-route';
        
        const h2 = document.createElement('h2');
        h2.textContent = routeName;
        
        const tripTypeSpan = document.createElement('span');
        tripTypeSpan.className = 'trip-type';
        tripTypeSpan.textContent = tripTypeText;
        
        routeDiv.appendChild(h2);
        routeDiv.appendChild(tripTypeSpan);
        
        const datesDiv = document.createElement('div');
        datesDiv.className = 'search-summary-dates';
        
        // Departure date group
        const depDateGroup = document.createElement('div');
        depDateGroup.className = 'date-group';
        
        const depLabel = document.createElement('span');
        depLabel.className = 'date-label';
        depLabel.textContent = 'Departure';
        
        const depValue = document.createElement('span');
        depValue.className = 'date-value';
        depValue.textContent = formattedDepartureDate;
        
        depDateGroup.appendChild(depLabel);
        depDateGroup.appendChild(depValue);
        
        datesDiv.appendChild(depDateGroup);
        
        // Return date group if return date exists
        if (returnDate) {
            const retDateGroup = document.createElement('div');
            retDateGroup.className = 'date-group';
            
            const retLabel = document.createElement('span');
            retLabel.className = 'date-label';
            retLabel.textContent = 'Return';
            
            const retValue = document.createElement('span');
            retValue.className = 'date-value';
            retValue.textContent = formattedReturnDate;
            
            retDateGroup.appendChild(retLabel);
            retDateGroup.appendChild(retValue);
            
            datesDiv.appendChild(retDateGroup);
        }
        
        // Details section
        const detailsDiv = document.createElement('div');
        detailsDiv.className = 'search-summary-details';
        
        // Passengers detail
        const passGroup = document.createElement('div');
        passGroup.className = 'detail-group';
        
        const passLabel = document.createElement('span');
        passLabel.className = 'detail-label';
        passLabel.textContent = 'Passengers:';
        
        const passValue = document.createElement('span');
        passValue.className = 'detail-value';
        passValue.textContent = passengersText;
        
        passGroup.appendChild(passLabel);
        passGroup.appendChild(passValue);
        
        // Cabin detail
        const cabinGroup = document.createElement('div');
        cabinGroup.className = 'detail-group';
        
        const cabinLabel = document.createElement('span');
        cabinLabel.className = 'detail-label';
        cabinLabel.textContent = 'Cabin:';
        
        const cabinValue = document.createElement('span');
        cabinValue.className = 'detail-value';
        cabinValue.textContent = cabinText;
        
        cabinGroup.appendChild(cabinLabel);
    detailsDiv.appendChild(cabinGroup);
    
    // Assemble main content
    contentDiv.appendChild(routeDiv);
    contentDiv.appendChild(datesDiv);
    contentDiv.appendChild(detailsDiv);
    
    // Clear and append new content
    searchSummaryDetailsEl.innerHTML = '';
    searchSummaryDetailsEl.appendChild(contentDiv);
    }

    async function fetchFlightResults(searchParams) {
        console.log("Fetching flight results with params:", searchParams);
        if (loadingPlaceholder) loadingPlaceholder.classList.remove('hidden');
        if (noFlightsFoundPlaceholder) noFlightsFoundPlaceholder.classList.add('hidden');
        if (resultsContainer) resultsContainer.innerHTML = ''; // Clear previous cards

        try {
            // Prepare request data in the format expected by the backend
            let odSegments = [];
            
            if (searchParams.segments && searchParams.segments.length > 0) {
                // If segments are already provided in the searchParams
                odSegments = searchParams.segments;
            } else if (searchParams.origin && searchParams.destination && searchParams.departureDate) {
                // For one-way or round-trip from URL parameters
                odSegments = [{
                    Origin: searchParams.origin,
                    Destination: searchParams.destination,
                    DepartureDate: searchParams.departureDate
                }];
                
                // Add return segment for round-trip
                if (searchParams.tripType === 'ROUND_TRIP' && searchParams.returnDate) {
                    odSegments.push({
                        Origin: searchParams.destination,
                        Destination: searchParams.origin,
                        DepartureDate: searchParams.returnDate
                    });
                }
            }

            
            const requestData = {
                tripType: searchParams.tripType || 'ONE_WAY',
                odSegments: odSegments,
                numAdults: searchParams.adults || 1,
                numChildren: searchParams.children || 0,
                numInfants: searchParams.infants || 0,
                cabinPreference: searchParams.cabinClass || 'ECONOMY'
            };

            console.log("Sending request to /api/verteil/air-shopping:", requestData);

            const response = await fetch(`${API_BASE_URL}/api/verteil/air-shopping`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });

            console.log("API Response Status:", response.status);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
            }
            
            const responseText = await response.text();
            console.log("Raw API response text:", responseText);
            
            let responseData;
            try {
                responseData = JSON.parse(responseText);
                console.log("Parsed API response:", responseData);
            } catch (e) {
                console.error("Failed to parse API response as JSON:", e);
                throw new Error("Invalid response format from server");
            }

            // Handle the response format from the backend
            let offers = [];
            if (responseData && responseData.status === 'success' && responseData.offers) {
                console.log("Found offers in response.offers");
                offers = responseData.offers;
            } else if (Array.isArray(responseData)) {
                console.log("Response is directly an array of offers");
                offers = responseData;
            } else if (responseData && responseData.offers) {
                console.log("Found offers in responseData.offers without status check");
                offers = responseData.offers;
            } else {
                console.warn("Unexpected response format:", responseData);
            }

            console.log("Final offers array to process:", offers);

            if (offers && offers.length > 0) {
                allFlightOffers = offers;
                console.log("Storing allFlightOffers:", allFlightOffers);
                populateAirlineFilters(allFlightOffers);
                applyFiltersAndSort(); // Initial render
            } else {
                console.warn('No offers found in response. Response data:', responseData);
                console.warn('Response status:', responseData?.status);
                console.warn('Offers array exists?', Array.isArray(responseData?.offers));
                console.warn('Response keys:', responseData ? Object.keys(responseData) : 'no response data');
                allFlightOffers = [];
                renderFlightResults([]); // Show no flights found
            }
        } catch (error) {
            console.error('Error fetching flight results:', error);
            if (resultsContainer) {
                resultsContainer.innerHTML = `
                    <div class="error-message results-error">
                        Error fetching flights: ${error.message || 'Unknown error occurred'}. Please try again.
                    </div>
                `;
            }
            if (resultsCountText) resultsCountText.textContent = '';
        } finally {
            if (loadingPlaceholder) loadingPlaceholder.classList.add('hidden');
        }
    }

    // Fall back to localStorage
    function getSearchParams() {
        const params = localStorage.getItem('flightSearchParams');
        if (params) {
            try {
                return JSON.parse(params);
            } catch (e) {
                console.error("Error parsing flightSearchParams from localStorage:", e);
                return null;
            }
        }
        return null;
    }

    function renderFlightResults(offersToRender) {
        if (!resultsContainer || !resultsCountText) {
            console.error("Results container or count text element not found.");
            return;
        }
        
        resultsContainer.innerHTML = ''; // Clear previous results
        
        if (offersToRender && offersToRender.length > 0) {
            offersToRender.forEach(offer => {
                const card = createFlightCard(offer);
                if (card) resultsContainer.appendChild(card);
            });
            resultsCountText.textContent = `${offersToRender.length} flight${offersToRender.length > 1 ? 's' : ''} found.`;
            if (noFlightsFoundPlaceholder) noFlightsFoundPlaceholder.classList.add('hidden');
        } else {
            resultsCountText.textContent = '0 flights found.';
            if (noFlightsFoundPlaceholder) {
                resultsContainer.appendChild(noFlightsFoundPlaceholder); // Ensure it's in the container
                noFlightsFoundPlaceholder.classList.remove('hidden');
            }
        }
    }

    function createFlightCard(offer) {
        console.log("Creating flight card for offer:", JSON.parse(JSON.stringify(offer)));
        
        if (!offer || !offer.segments || offer.segments.length === 0) {
            console.warn("Skipping offer due to missing data:", offer);
            return null;
        }

        const card = document.createElement('div');
        card.className = 'flight-card';

        try {
            const offerPrice = offer.price ? formatCurrency(offer.price.amount, offer.price.currency) : 'N/A';
            const firstSegment = offer.segments[0];
            
            if (!firstSegment) {
                console.error("First segment is missing or invalid:", offer);
                return null;
            }

            const airlineCode = offer.airline || firstSegment.airline; // Prefer offer-level airline, fallback to first segment
            const airlineName = getAirlineName(airlineCode);
            const airlineLogoUrl = getAirlineLogoUrl(airlineCode);
            
            // Log segment details for debugging
            console.log(`Processing offer ${offer.id} with ${offer.segments.length} segments`);
            offer.segments.forEach((seg, idx) => {
                console.log(`Segment ${idx + 1}:`, {
                    origin: seg.origin,
                    destination: seg.destination,
                    departure: seg.departure_time,
                    arrival: seg.arrival_time,
                    flight_number: seg.flight_number,
                    airline: seg.airline
                });
            });
            
            const totalDurationMinutes = getTotalDurationInMinutes(offer.segments);
            card.dataset.price = offer.price ? offer.price.amount : Infinity;
            card.dataset.duration = totalDurationMinutes !== Infinity ? totalDurationMinutes : Infinity;
            card.dataset.airline = airlineCode ? airlineCode.toLowerCase() : 'unknown';
            card.dataset.stops = countStops(offer.segments);
            card.dataset.departureTime = firstSegment.departure_time || ''; // For sorting
            
            const flightSegmentsContainer = document.createElement('div');
            flightSegmentsContainer.className = 'flight-segments-container';

            offer.segments.forEach(segment => {
                const segmentDiv = document.createElement('div');
                segmentDiv.className = 'segment';
                
                const routeDiv = document.createElement('div');
                routeDiv.className = 'segment-route';
                
                const originSpan = document.createElement('span');
                originSpan.className = 'airport';
                originSpan.textContent = segment.origin;
                
                const separator1 = document.createElement('span');
                separator1.className = 'separator';
                separator1.textContent = '→';
                
                const destSpan = document.createElement('span');
                destSpan.className = 'airport';
                destSpan.textContent = segment.destination;
                
                routeDiv.appendChild(originSpan);
                routeDiv.appendChild(separator1);
                routeDiv.appendChild(destSpan);
                
                // Times div
                const timesDiv = document.createElement('div');
                timesDiv.className = 'segment-times';
                
                const depTime = document.createElement('span');
                depTime.className = 'time';
                depTime.textContent = segment.departure_time;
                
                const separator2 = document.createElement('span');
                separator2.className = 'separator';
                separator2.textContent = '-';
                
                const arrTime = document.createElement('span');
                arrTime.className = 'time';
                arrTime.textContent = segment.arrival_time;
                
                timesDiv.appendChild(depTime);
                timesDiv.appendChild(separator2);
                timesDiv.appendChild(arrTime);
                
                // Details div
                const detailsDiv = document.createElement('div');
                detailsDiv.className = 'segment-details';
                
                const durationSpan = document.createElement('span');
                durationSpan.className = 'duration';
                durationSpan.textContent = segment.duration;
                
                const stopsSpan = document.createElement('span');
                stopsSpan.className = 'stops';
                stopsSpan.textContent = segment.stops + ' ' + (segment.stops === 1 ? 'stop' : 'stops');
                
                detailsDiv.appendChild(durationSpan);
                detailsDiv.appendChild(stopsSpan);
                
                // Assemble segment
                segmentDiv.appendChild(routeDiv);
                segmentDiv.appendChild(timesDiv);
                segmentDiv.appendChild(detailsDiv);
                
                // Add to container
                flightSegmentsContainer.appendChild(segmentDiv);
            });

            const airlineLogo = document.createElement('img');
            airlineLogo.src = airlineLogoUrl;
            airlineLogo.alt = airlineName + ' Logo';
            airlineLogo.className = 'airline-logo';
            airlineLogo.onerror = function() {
                this.style.display = 'none';
                const parent = this.parentNode;
                const textLogo = document.createElement('div');
                textLogo.className = 'airline-logo-text-fallback';
                textLogo.textContent = airlineCode;
                parent.insertBefore(textLogo, this.nextSibling);
                this.remove();
            };

            const airlineNameEl = document.createElement('span');
            airlineNameEl.className = 'airline-name';
            airlineNameEl.textContent = airlineName;

            const flightNumberEl = document.createElement('span');
            flightNumberEl.className = 'flight-number-details';
            flightNumberEl.textContent = offer.flight_number || firstSegment.flight_number;

            const airlineNameDetails = document.createElement('div');
            airlineNameDetails.className = 'airline-name-details';
            airlineNameDetails.appendChild(airlineNameEl);
            airlineNameDetails.appendChild(flightNumberEl);

            const airlineInfo = document.createElement('div');
            airlineInfo.className = 'airline-info';
            airlineInfo.appendChild(airlineLogo);
            airlineInfo.appendChild(airlineNameDetails);
            const priceEl = document.createElement('span');
            priceEl.className = 'price';
            priceEl.textContent = offerPrice;

            const priceDetailsEl = document.createElement('span');
            priceDetailsEl.className = 'price-details';
            const adults = (currentSearchParams && currentSearchParams.adults) || 0;
            const children = (currentSearchParams && currentSearchParams.children) || 0;
            const infants = (currentSearchParams && currentSearchParams.infants) || 0;
            const totalTravelers = adults + children + infants;
            priceDetailsEl.textContent = 'Total for ' + totalTravelers + ' traveler' + (totalTravelers !== 1 ? 's' : '');

            const selectButton = document.createElement('button');
            selectButton.className = 'select-flight-btn';
            selectButton.dataset.offerId = offer.id;
            
            const buttonText = document.createTextNode('Select Flight');
            selectButton.appendChild(buttonText);

            const priceActionSection = document.createElement('div');
            priceActionSection.className = 'price-action-section';
            priceActionSection.appendChild(priceEl);
            priceActionSection.appendChild(priceDetailsEl);
            priceActionSection.appendChild(selectButton);

            const flightHeader = document.createElement('div');
            flightHeader.className = 'flight-header';
            flightHeader.appendChild(airlineInfo);
            flightHeader.appendChild(priceActionSection);

            const segmentsContainer = document.createElement('div');
            segmentsContainer.className = 'flight-segments-container';
            segmentsContainer.appendChild(flightSegmentsContainer);

            card.appendChild(flightHeader);
            card.appendChild(segmentsContainer);
            
            return card;
            
        } catch (error) {
            console.error("Error creating flight card:", error, "\nOffer data:", offer);
            return null;
        }
    }

    function populateAirlineFilters(offers) {
        if (!airlineFiltersContainer) return;
        const airlines = new Set();
        offers.forEach(offer => {
            if (offer.segments && offer.segments.length > 0) {
                 offer.segments.forEach(segment => {
                    if(segment.airline) airlines.add(segment.airline);
                 });
            } else if (offer.airline) { // Fallback to offer-level airline
                airlines.add(offer.airline);
            }
        });
        console.log("Populating airline filters with:", airlines);

        airlineFiltersContainer.innerHTML = ''; // Clear loading/previous
        if (airlines.size === 0) {
            airlineFiltersContainer.innerHTML = '<p class="text-on-dark-secondary">No airlines to filter.</p>';
            return;
        }

        airlines.forEach(airlineCode => {
            const airlineName = getAirlineName(airlineCode);
            const label = document.createElement('label');
            label.className = 'filter-checkbox';
            label.innerHTML = `<input type="checkbox" name="airline" value="${airlineCode.toLowerCase()}" class="filter-toggle"> ${airlineName} (${airlineCode})`;
            airlineFiltersContainer.appendChild(label);
        });
        
        document.querySelectorAll('input[name="airline"]').forEach(checkbox => {
            checkbox.addEventListener('change', applyFiltersAndSort);
        });
    }

    function getSelectedFilters() {
        const selectedStops = Array.from(document.querySelectorAll('input[name="stops"]:checked')).map(cb => cb.value);
        const selectedAirlines = Array.from(document.querySelectorAll('input[name="airline"]:checked')).map(cb => cb.value);
        const selectedDepartureTimes = Array.from(document.querySelectorAll('input[name="departureTime"]:checked')).map(cb => cb.value);
        const priceVal = priceRangeSlider ? parseInt(priceRangeSlider.value) : 500000; // Default high if no slider (500,000 INR)

        return {
            stops: selectedStops,
            priceMax: priceVal,
            airlines: selectedAirlines,
            departureTimes: selectedDepartureTimes
        };
    }

    function filterFlightOffers(offers, filters) {
        console.log("Filtering offers with:", filters);
        return offers.filter(offer => {
            if (!offer || !offer.price || !offer.segments || offer.segments.length === 0) return false;

            if (offer.price.amount > filters.priceMax) return false;

            const numStops = offer.segments.length - 1;
            if (filters.stops.length > 0) {
                let stopMatch = false;
                if (filters.stops.includes('0') && numStops === 0) stopMatch = true;
                else if (filters.stops.includes('1') && numStops === 1) stopMatch = true;
                else if (filters.stops.includes('2+') && numStops >= 2) stopMatch = true;
                if (!stopMatch) return false;
            }

            if (filters.airlines.length > 0) {
                const offerAirlines = new Set(offer.segments.map(s => s.airline.toLowerCase()));
                 if (offer.airline) offerAirlines.add(offer.airline.toLowerCase()); // Check offer level airline too
                if (!filters.airlines.some(fa => offerAirlines.has(fa))) return false;
            }

            if (filters.departureTimes.length > 0) {
                const departureHour = new Date(offer.segments[0].departure_time).getHours();
                let timeMatch = false;
                if (filters.departureTimes.includes('morning') && departureHour >= 5 && departureHour < 12) timeMatch = true;
                else if (filters.departureTimes.includes('afternoon') && departureHour >= 12 && departureHour < 17) timeMatch = true;
                else if (filters.departureTimes.includes('evening') && departureHour >= 17 && departureHour < 21) timeMatch = true;
                else if (filters.departureTimes.includes('night') && (departureHour >= 21 || departureHour < 5)) timeMatch = true;
                if (!timeMatch) return false;
            }
            return true;
        });
    }

    function sortFlightOffers(offers, sortBy) {
        const sortedOffers = [...offers];
        console.log("Sorting offers by:", sortBy);
        switch (sortBy) {
            case 'price-asc':
                sortedOffers.sort((a, b) => (a.price ? a.price.amount : Infinity) - (b.price ? b.price.amount : Infinity));
                break;
            case 'price-desc':
                sortedOffers.sort((a, b) => (b.price ? b.price.amount : -Infinity) - (a.price ? a.price.amount : -Infinity));
                break;
            case 'duration-asc':
                sortedOffers.sort((a, b) => getTotalDurationInMinutes(a.segments) - getTotalDurationInMinutes(b.segments));
                break;
            case 'departure-asc':
                sortedOffers.sort((a, b) => 
                    (a.segments.length > 0 ? new Date(a.segments[0].departure_time).getTime() : Infinity) - 
                    (b.segments.length > 0 ? new Date(b.segments[0].departure_time).getTime() : Infinity)
                );
                break;
            case 'arrival-asc':
                 sortedOffers.sort((a, b) => 
                    (a.segments.length > 0 ? new Date(a.segments[a.segments.length - 1].arrival_time).getTime() : Infinity) - 
                    (b.segments.length > 0 ? new Date(b.segments[b.segments.length - 1].arrival_time).getTime() : Infinity)
                );
                break;
        }
        return sortedOffers;
    }

    function applyFiltersAndSort() {
        console.log("Applying filters and sorting...");
        const filters = getSelectedFilters();
        const filteredOffers = filterFlightOffers(allFlightOffers, filters);
        
        const sortBy = sortResultsSelect ? sortResultsSelect.value : 'duration-asc';
        const sortedAndFilteredOffers = sortFlightOffers(filteredOffers, sortBy);
        
        renderFlightResults(sortedAndFilteredOffers);
    }

    // Helper Functions
    function formatDate(dateString) {
        if (!dateString || dateString.toLowerCase().includes('invalid')) return 'N/A';
        try {
            const date = new Date(dateString);
            if (isNaN(date.getTime())) return 'N/A'; // Invalid date
            return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
        } catch (e) {
            console.error("Error formatting date:", dateString, e);
            return 'N/A';
        }
    }

    function formatTime(dateString) {
        if (!dateString || dateString.toLowerCase().includes('invalid')) return 'N/A';
        try {
            const date = new Date(dateString);
            if (isNaN(date.getTime())) return 'N/A';
            return date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', hour12: true });
        } catch (e) {
            console.error("Error formatting time:", dateString, e);
            return 'N/A';
        }
    }

    function calculateDuration(departureTimeStr, arrivalTimeStr) {
        if (!departureTimeStr || !arrivalTimeStr || departureTimeStr.toLowerCase().includes('invalid') || arrivalTimeStr.toLowerCase().includes('invalid')) return 'N/A';
        try {
            const departure = new Date(departureTimeStr);
            const arrival = new Date(arrivalTimeStr);
            if (isNaN(departure.getTime()) || isNaN(arrival.getTime())) return 'N/A';

            let diff = arrival.getTime() - departure.getTime();
            if (diff < 0) diff = 0; 
            
            const hours = Math.floor(diff / (1000 * 60 * 60));
            diff -= hours * (1000 * 60 * 60);
            const minutes = Math.floor(diff / (1000 * 60));
            
            return `${hours}h ${minutes}m`;
        } catch (e) {
            console.error("Error calculating duration:", departureTimeStr, arrivalTimeStr, e);
            return 'N/A';
        }
    }
    
    function getTotalDurationInMinutes(segments) {
        if (!segments || segments.length === 0) return Infinity;
        try {
            const firstDeparture = new Date(segments[0].departure_time);
            const lastArrival = new Date(segments[segments.length - 1].arrival_time);
            if (isNaN(firstDeparture.getTime()) || isNaN(lastArrival.getTime())) return Infinity;
            return (lastArrival.getTime() - firstDeparture.getTime()) / (1000 * 60); // Duration in minutes
        } catch(e) {
            console.error("Error calculating total duration in minutes for segments:", segments, e);
            return Infinity;
        }
    }

    function formatCurrency(amount, currencyCode = 'USD') {
        if (amount === undefined || amount === null ) return 'N/A';
        try {
            return new Intl.NumberFormat(undefined, { style: 'currency', currency: currencyCode }).format(amount);
        } catch (e) {
            // Fallback for unknown currency codes
            console.warn(`Currency formatting failed for ${currencyCode}. Defaulting display.`, e);
            return `${currencyCode} ${Number(amount).toFixed(2)}`;
        }
    }
    
    const airlineNameMap = { // Add more as needed
        "WY": "Oman Air",
        "BA": "British Airways",
        "EK": "Emirates",
        "LH": "Lufthansa",
        "AF": "Air France",
        "SQ": "Singapore Airlines",
        "QR": "Qatar Airways",
        "EY": "Etihad Airways",
        "TK": "Turkish Airlines",
        "CX": "Cathay Pacific",
        "AA": "American Airlines",
        "DL": "Delta Air Lines",
        "UA": "United Airlines"
    };

    function getAirlineName(airlineCode) {
        return airlineNameMap[airlineCode.toUpperCase()] || airlineCode;
    }

    function getAirlineLogoUrl(airlineCode) {
        if (!airlineCode) return `https://via.placeholder.com/40x40?text=AL`; // Default placeholder
        // Using clearbit for logos, fallback to a text-based placeholder if clearbit fails (handled by onerror in HTML)
        return `https://logo.clearbit.com/${airlineCode.toLowerCase()}.com`;
    }

    function countStops(segments) {
        if (!segments || !Array.isArray(segments)) return 0;
        return Math.max(0, segments.length - 1);
    }

    function setupMobileNav() {
        const mobileNavToggle = document.querySelector('.mobile-nav-toggle');
        const mainNav = document.querySelector('.main-nav');

        if (mobileNavToggle && mainNav) {
            mobileNavToggle.addEventListener('click', () => {
                const isExpanded = mobileNavToggle.getAttribute('aria-expanded') === 'true' || false;
                mobileNavToggle.setAttribute('aria-expanded', !isExpanded);
                mainNav.classList.toggle('active');
                mobileNavToggle.classList.toggle('active');
            });
        }
    }
});
