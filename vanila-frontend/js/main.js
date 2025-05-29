// js/main.js
document.addEventListener('DOMContentLoaded', function () {
    const flightSearchForm = document.getElementById('flightSearchForm');
    const tripTypeRadios = document.querySelectorAll('input[name="tripType"]');
    const odSegmentsContainer = document.getElementById('od-segments-container');
    const returnSegmentContainer = document.getElementById('return-segment-container'); // Specifically the return date part for round trip
    const addMultiCityLegBtn = document.getElementById('addMultiCityLegBtn');
    const loadingIndicator = document.getElementById('loading-indicator');
    const searchErrorMessage = document.getElementById('search-error-message');
    
    // Set min date for date inputs to today
    const today = new Date().toISOString().split('T')[0];
    document.querySelectorAll('input[type="date"]').forEach(dateInput => {
        dateInput.setAttribute('min', today);
    });

    // --- Airport Autocomplete/Suggestion Logic ---
    function setupAirportInput(originInputId, originDatalistId, destInputId, destDatalistId) {
        const originInput = document.getElementById(originInputId);
        const destInput = document.getElementById(destInputId);

        if (originInput) {
            originInput.addEventListener('input', function(e) {
                populateAirportSuggestions(originInputId, originDatalistId, e.target.value);
            });
        }
        if (destInput) {
            destInput.addEventListener('input', function(e) {
                populateAirportSuggestions(destInputId, destDatalistId, e.target.value);
            });
        }
    }
    
        // Initialize variables
    let legCounter = 1; // Start with 1 because leg 0 is always there
    
    // Initialize the form when the DOM is fully loaded
    function initializeForm() {
        try {
            // Set up the first leg
            setupAirportInput('origin-0', 'airport-suggestions-origin-0', 'destination-0', 'airport-suggestions-destination-0');
            
            // Set initial trip type
            const initialTripType = document.querySelector('input[name="tripType"]:checked');
            if (initialTripType) {
                initialTripType.checked = true;
            } else if (tripTypeRadios.length > 0) {
                // If no trip type is selected, select the first one
                tripTypeRadios[0].checked = true;
            }
            
            // Initialize the form based on the selected trip type
            handleTripTypeChange();
        } catch (error) {
            console.error('Error initializing form:', error);
        }
    }
    
    // Set up the form initialization
    function setupForm() {
        // Remove any existing listeners to prevent duplicates
        document.removeEventListener('DOMContentLoaded', setupForm);
        
        // Initialize the form
        initializeForm();
        
        // Set up trip type change listeners
        if (tripTypeRadios && tripTypeRadios.length > 0) {
            tripTypeRadios.forEach(radio => {
                radio.removeEventListener('change', handleTripTypeChange);
                radio.addEventListener('change', handleTripTypeChange);
            });
        }
    }
    
    // Start the initialization
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupForm);
    } else {
        setupForm();
    }
    
    // --- Trip Type Change Handler ---

    function handleTripTypeChange() {
        const selectedTripType = document.querySelector('input[name="tripType"]:checked').value;
        
        // Safety check
        if (!odSegmentsContainer) {
            console.error('odSegmentsContainer not found');
            return;
        }

        // Clear dynamic segments first, keeping the first one
        let maxIterations = 10; // Prevent infinite loops
        while (odSegmentsContainer.children.length > 1 && maxIterations-- > 0) {
            const lastChild = odSegmentsContainer.lastChild;
            
            // Skip if this is the return segment container in round trip mode
            if (lastChild.id === 'return-segment-container' && selectedTripType === "ROUND_TRIP") {
                break;
            }
            
            // For one-way trips, keep only the first segment
            if (selectedTripType === "ONE_WAY" && odSegmentsContainer.children.length > 1) {
                if (lastChild.dataset.legIndex !== "0") {
                    odSegmentsContainer.removeChild(lastChild);
                } else {
                    break;
                }
            } 
            // For round trip, keep first segment and return segment
            else if (selectedTripType === "ROUND_TRIP" && odSegmentsContainer.children.length > 2) {
                if (lastChild.id !== 'return-segment-container' && lastChild.dataset.legIndex !== "0") {
                    odSegmentsContainer.removeChild(lastChild);
                } else {
                    break;
                }
            } 
            // For multi-city, keep all segments
            else {
                break;
            }
        }
        
        if (maxIterations <= 0) {
            console.error('Exceeded maximum iterations in handleTripTypeChange');
        }
        legCounter = odSegmentsContainer.children.length -1;


        if (selectedTripType === "ONE_WAY") {
            if (returnSegmentContainer) returnSegmentContainer.style.display = 'none';
            if (addMultiCityLegBtn) addMultiCityLegBtn.style.display = 'none';
            // Ensure only one OD segment is visible and inputs are correct
            document.querySelectorAll('.od-segment').forEach((seg, index) => {
                seg.style.display = index === 0 ? 'grid' : 'none';
            });
        } else if (selectedTripType === "ROUND_TRIP") {
            if (returnSegmentContainer) {
                returnSegmentContainer.style.display = 'grid'; // Show return date input
                // Ensure only date input is visible in return segment container
                const returnSegChildren = returnSegmentContainer.children;
                for(let i=0; i < returnSegChildren.length; i++) {
                    if(!returnSegChildren[i].querySelector('input[type="date"]')) {
                        returnSegChildren[i].style.display = 'none';
                    } else {
                        returnSegChildren[i].style.display = 'flex'; // or 'block'
                    }
                }
            }
            if (addMultiCityLegBtn) addMultiCityLegBtn.style.display = 'none';
             document.querySelectorAll('.od-segment').forEach((seg, index) => {
                if (index === 0) seg.style.display = 'grid';
                else if (index === 1 && seg.id === 'return-segment-container') seg.style.display = 'grid';
                else seg.style.display = 'none';
            });

        } else if (selectedTripType === "MULTI_CITY") {
            if (returnSegmentContainer) returnSegmentContainer.style.display = 'none'; // Hide simple return
            if (addMultiCityLegBtn) addMultiCityLegBtn.style.display = 'block';
            // Ensure at least two full OD segments are visible, and allow adding more
            document.querySelectorAll('.od-segment').forEach((seg, index) => {
                seg.style.display = 'grid'; // Show all existing segments
                // Make sure all inputs are visible for multi-city segments
                const children = seg.children;
                for(let i=0; i<children.length; i++) {
                    children[i].style.display = 'flex'; // or 'block'
                }
            });
            if (odSegmentsContainer.children.length < 2) { // Ensure at least 2 for multi-city start
                addLegElement(); 
            }
        }
    }

    tripTypeRadios.forEach(radio => radio.addEventListener('change', handleTripTypeChange));
    
    // --- Multi-City Leg Management ---
    function addLegElement() {
        if (legCounter >= 4) { // Max 5 legs total (0 to 4)
            alert("Maximum of 5 legs for multi-city search.");
            return;
        }
        legCounter++;
        const newSegment = document.createElement('div');
        newSegment.classList.add('od-segment');
        newSegment.setAttribute('data-leg-index', legCounter);
        newSegment.innerHTML = `
            <div class="form-group">
                <label for="origin-${legCounter}">From (Leg ${legCounter + 1})</label>
                <input type="text" id="origin-${legCounter}" name="origin-${legCounter}" placeholder="Origin" required list="airport-suggestions-origin-${legCounter}">
                <datalist id="airport-suggestions-origin-${legCounter}"></datalist>
            </div>
            <div class="form-group">
                <label for="destination-${legCounter}">To (Leg ${legCounter + 1})</label>
                <input type="text" id="destination-${legCounter}" name="destination-${legCounter}" placeholder="Destination" required list="airport-suggestions-destination-${legCounter}">
                <datalist id="airport-suggestions-destination-${legCounter}"></datalist>
            </div>
            <div class="form-group">
                <label for="departureDate-${legCounter}">Depart (Leg ${legCounter + 1})</label>
                <input type="date" id="departureDate-${legCounter}" name="departureDate-${legCounter}" required min="${today}">
            </div>
            <button type="button" class="remove-leg-btn" data-remove-index="${legCounter}">Remove Leg</button>
        `;
        odSegmentsContainer.appendChild(newSegment);
        setupAirportInput(`origin-${legCounter}`, `airport-suggestions-origin-${legCounter}`, `destination-${legCounter}`, `airport-suggestions-destination-${legCounter}`);
        
        // Add event listener for the new remove button
        newSegment.querySelector('.remove-leg-btn').addEventListener('click', function() {
            odSegmentsContainer.removeChild(newSegment);
            // Renumber subsequent legs if needed, or adjust legCounter (simpler to just remove)
            // For robust re-numbering, you'd iterate and update IDs/names.
            // For now, we just decrement legCounter if the removed was the last one dynamically added.
            // A more robust solution would be to manage segments in a JS array and re-render.
            // This simple removal can lead to gaps in legCounter if not careful.
        });
    }

    if (addMultiCityLegBtn) {
        addMultiCityLegBtn.addEventListener('click', addLegElement);
    }
    // Initial call to set form based on default checked radio
    handleTripTypeChange(); 


    // --- Form Submission ---
    if (flightSearchForm) {
        flightSearchForm.addEventListener('submit', async function (event) {
            event.preventDefault();
            console.log('Form submission started');
            if (loadingIndicator) loadingIndicator.style.display = 'block';
            if (searchErrorMessage) searchErrorMessage.style.display = 'none';
            
            // Debug: Log form data
            const formData = new FormData(flightSearchForm);
            console.log('Form data:', Object.fromEntries(formData.entries()));

            const tripType = formData.get('tripType');
            
            const odSegmentsData = [];
            const numSegments = tripType === "ONE_WAY" ? 1 : 
                                (tripType === "ROUND_TRIP" ? 2 : 
                                 document.querySelectorAll('#od-segments-container .od-segment').length);

            for (let i = 0; i < numSegments; i++) {
                const origin = formData.get(`origin-${i}`)?.toString().toUpperCase();
                const destination = formData.get(`destination-${i}`)?.toString().toUpperCase();
                const departureDate = formData.get(`departureDate-${i}`);

                if (tripType === "ROUND_TRIP" && i === 1) { // Return leg for round trip
                    if (departureDate) { // Only date is needed
                        odSegmentsData.push({ DepartureDate: departureDate });
                    } else {
                        if (loadingIndicator) loadingIndicator.style.display = 'none';
                        if (searchErrorMessage) {
                            searchErrorMessage.textContent = "Return date is required for round trip.";
                            searchErrorMessage.style.display = 'block';
                        }
                        return;
                    }
                } else if (origin && destination && departureDate) {
                    odSegmentsData.push({
                        Origin: origin,
                        Destination: destination,
                        DepartureDate: departureDate
                    });
                } else if (tripType === "MULTI_CITY" && i < odSegmentsContainer.children.length) { 
                    // For multi-city, all fields are required for active segments
                    if (loadingIndicator) loadingIndicator.style.display = 'none';
                    if (searchErrorMessage) {
                         searchErrorMessage.textContent = `Please fill all fields for Leg ${i + 1}.`;
                         searchErrorMessage.style.display = 'block';
                    }
                    return;
                }
            }
            if (tripType === "ONE_WAY" && odSegmentsData.length === 0) {
                if (loadingIndicator) loadingIndicator.style.display = 'none';
                if (searchErrorMessage) { searchErrorMessage.textContent = "Please fill in flight details."; searchErrorMessage.style.display = 'block';}
                return;
            }


            const searchCriteria = {
                tripType: tripType,
                odSegments: odSegmentsData,
                numAdults: parseInt(formData.get('numAdults')),
                numChildren: parseInt(formData.get('numChildren')),
                numInfants: parseInt(formData.get('numInfants')),
                cabinPreference: formData.get('cabinPreference')
            };

            // Basic client-side validation
            if (searchCriteria.numInfants > searchCriteria.numAdults && searchCriteria.numAdults > 0) {
                if (loadingIndicator) loadingIndicator.style.display = 'none';
                if (searchErrorMessage) {
                    searchErrorMessage.textContent = "Number of infants cannot exceed adults.";
                    searchErrorMessage.style.display = 'block';
                }
                return;
            }
            if (searchCriteria.numAdults === 0 && (searchCriteria.numChildren > 0 || searchCriteria.numInfants > 0)) {
                 if (loadingIndicator) loadingIndicator.style.display = 'none';
                 if (searchErrorMessage) {
                    searchErrorMessage.textContent = "Children or infants must travel with an adult.";
                    searchErrorMessage.style.display = 'block';
                 }
                return;
            }
            console.log("Sending request to backend with data:", searchCriteria);
            try {
                console.log('Making API call to:', 'http://localhost:5000/api/verteil/air-shopping');
                const response = await fetch('http://localhost:5000/api/verteil/air-shopping', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify(searchCriteria),
                    mode: 'cors',
                    credentials: 'same-origin'
                });

                console.log('Response status:', response.status);
                
                if (loadingIndicator) loadingIndicator.style.display = 'none';

                if (!response.ok) {
                    console.error('Response not OK, status:', response.status);
                    let errorData;
                    try {
                        errorData = await response.json();
                        console.error('Error response:', errorData);
                    } catch (e) {
                        console.error('Could not parse error response as JSON');
                        errorData = { error: `HTTP error! status: ${response.status}` };
                    }
                    throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
                }

                const results = await response.json();
                console.log('Received results:', results);
                
                // Store results in session storage for the results page
                // The backend now returns the offers array directly
                sessionStorage.setItem('flightSearchResults', JSON.stringify(Array.isArray(results) ? results : []));
                sessionStorage.setItem('searchCriteria', JSON.stringify(searchCriteria));
                
                // Store additional metadata if available (for backward compatibility)
                if (results.shoppingResponseId) {
                    sessionStorage.setItem('shoppingResponseId', results.shoppingResponseId);
                }
                if (results.owner) {
                    sessionStorage.setItem('shoppingOwner', results.owner);
                }

                // Build URL parameters for the results page
                const queryParams = new URLSearchParams({
                    origin: searchCriteria.odSegments[0].Origin,
                    destination: searchCriteria.odSegments[0].Destination,
                    departureDate: searchCriteria.odSegments[0].DepartureDate,
                    adults: searchCriteria.numAdults,
                    children: searchCriteria.numChildren,
                    infants: searchCriteria.numInfants,
                    cabin: searchCriteria.cabinPreference,
                    tripType: searchCriteria.tripType
                });
                
                // Add return date for round trips
                if (searchCriteria.tripType === "ROUND_TRIP" && searchCriteria.odSegments[1]) {
                    queryParams.set("returnDate", searchCriteria.odSegments[1].DepartureDate);
                }
                
                // Store the full search criteria in session storage for reference
                sessionStorage.setItem('fullSearchCriteria', JSON.stringify(searchCriteria));
                
                // Redirect to the results page
                window.location.href = `results.html?${queryParams.toString()}`;

            } catch (error) {
                console.error('Search Error:', error);
                if (loadingIndicator) loadingIndicator.style.display = 'none';
                if (searchErrorMessage) {
                    searchErrorMessage.textContent = error.message || "Failed to fetch flights. Please try again.";
                    searchErrorMessage.style.display = 'block';
                }
            }
        });
    }

    // Set current year in footer
    const currentYearSpan = document.getElementById('currentYear');
    if (currentYearSpan) {
        currentYearSpan.textContent = new Date().getFullYear();
    }
});