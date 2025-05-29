// js/main.js
document.addEventListener('DOMContentLoaded', function () {
    const flightSearchForm = document.getElementById('flightSearchForm');
    const tripTypeOptions = document.querySelectorAll('.trip-type-option'); // Use labels for click
    const odSegmentsContainer = document.getElementById('od-segments-container');
    const addMultiCityLegBtn = document.getElementById('addMultiCityLegBtn');
    const loadingIndicator = document.getElementById('loadingIndicator'); // Corrected ID
    const errorMessage = document.getElementById('errorMessage'); // Corrected ID
    
    // Passenger Selector Elements
    const passengerSelectorBtn = document.getElementById('passenger-selector-btn');
    const passengerSelectorDropdown = document.getElementById('passenger-selector-dropdown');
    const passengerDoneBtn = document.getElementById('passenger-done-btn');
    const cabinClassSelect = document.getElementById('cabin-class-dropdown');

    // Mobile Nav
    const mobileNavToggle = document.querySelector('.mobile-nav-toggle');
    const mainNav = document.querySelector('.main-nav');

    let legCounter = 0; // Start with leg 0 already in HTML

    // --- Utility Functions ---
    function getSelectedTripType() {
        const selectedRadio = document.querySelector('input[name="tripType"]:checked');
        return selectedRadio ? selectedRadio.value : 'one-way'; // Default to one-way
    }

    function updatePassengerButtonText() {
        if (!passengerSelectorBtn) return;

        const adults = parseInt(document.getElementById('adults-count-display').textContent);
        const children = parseInt(document.getElementById('children-count-display').textContent);
        const infants = parseInt(document.getElementById('infants-count-display').textContent);
        const cabin = cabinClassSelect.options[cabinClassSelect.selectedIndex].text;

        let text = `${adults} Adult`;
        if (adults > 1) text = `${adults} Adults`;
        
        if (children > 0) {
            text += `, ${children} Child${children > 1 ? 'ren' : ''}`;
        }
        if (infants > 0) {
            text += `, ${infants} Infant${infants > 1 ? 's' : ''}`;
        }
        text += `, ${cabin}`;
        passengerSelectorBtn.textContent = text;
    }


    // --- Airport Autocomplete/Suggestion Logic (Simplified) ---
    function setupAirportInput(inputId) {
        const inputElement = document.getElementById(inputId);
        const suggestionsContainerId = `${inputId}-suggestions`;
        let suggestionsContainer = document.getElementById(suggestionsContainerId);

        if (inputElement) {
            if (!suggestionsContainer) {
                suggestionsContainer = document.createElement('div');
                suggestionsContainer.id = suggestionsContainerId;
                suggestionsContainer.classList.add('autocomplete-suggestions');
                inputElement.parentNode.appendChild(suggestionsContainer);
            }
            
            inputElement.addEventListener('input', function(e) {
                const value = e.target.value.toLowerCase();
                suggestionsContainer.innerHTML = '';
                if (value.length < 2) { // Start suggesting after 2 characters
                    suggestionsContainer.classList.remove('active');
                    return;
                }

                const filteredAirports = airports_data.filter(airport => 
                    airport.name.toLowerCase().includes(value) || 
                    airport.iata_code.toLowerCase().includes(value) ||
                    airport.city.toLowerCase().includes(value)
                ).slice(0, 7); // Limit suggestions

                if (filteredAirports.length > 0) {
                    filteredAirports.forEach(airport => {
                        const div = document.createElement('div');
                        div.textContent = `${airport.name} (${airport.iata_code}) - ${airport.city}`;
                        div.addEventListener('click', () => {
                            inputElement.value = `${airport.city} (${airport.iata_code})`;
                            suggestionsContainer.innerHTML = '';
                            suggestionsContainer.classList.remove('active');
                        });
                        suggestionsContainer.appendChild(div);
                    });
                    suggestionsContainer.classList.add('active');
                } else {
                    suggestionsContainer.classList.remove('active');
                }
            });
            
            // Hide suggestions when clicking outside
            document.addEventListener('click', function(e) {
                if (!inputElement.contains(e.target) && !suggestionsContainer.contains(e.target)) {
                    suggestionsContainer.classList.remove('active');
                }
            });
        }
    }
    
    // --- Trip Type Change Handler ---
    function handleTripTypeChange() {
        const selectedTripType = getSelectedTripType();
        const firstSegment = document.getElementById('od-segment-0');
        const returnDateGroup = document.getElementById('return-date-group-0');

        // Update active class on labels
        tripTypeOptions.forEach(opt => {
            if (opt.htmlFor === document.querySelector('input[name="tripType"]:checked').id) {
                opt.classList.add('active');
            } else {
                opt.classList.remove('active');
            }
        });

        // Remove all but the first segment
        while (odSegmentsContainer.children.length > 1) {
            if (odSegmentsContainer.lastChild.id !== 'od-segment-0') { // Ensure we don't remove the first segment
                 odSegmentsContainer.removeChild(odSegmentsContainer.lastChild);
            } else {
                break; // Should not happen if logic is correct
            }
        }
        legCounter = 0; // Reset leg counter as we only have leg 0 now

        if (selectedTripType === "one-way") {
            if (returnDateGroup) returnDateGroup.classList.add('hidden');
            if (firstSegment) firstSegment.classList.add('one-way-layout');
            if (addMultiCityLegBtn) addMultiCityLegBtn.classList.add('hidden');
        } else if (selectedTripType === "round-trip") {
            if (returnDateGroup) returnDateGroup.classList.remove('hidden');
            if (firstSegment) firstSegment.classList.remove('one-way-layout');
            if (addMultiCityLegBtn) addMultiCityLegBtn.classList.add('hidden');
        } else if (selectedTripType === "multi-city") {
            if (returnDateGroup) returnDateGroup.classList.add('hidden'); // No single return date for multi-city
            if (firstSegment) firstSegment.classList.remove('one-way-layout');
            if (addMultiCityLegBtn) addMultiCityLegBtn.classList.remove('hidden');
            // Ensure at least two legs for multi-city start
            if (odSegmentsContainer.children.length < 2) {
                addLegElement();
            }
            // Make remove button visible for the first leg in multi-city
            const firstLegRemoveBtn = document.getElementById('remove-leg-btn-0');
            if(firstLegRemoveBtn) firstLegRemoveBtn.classList.remove('hidden');
        }

        // Hide remove button for first leg if not multi-city
        if (selectedTripType !== "multi-city") {
            const firstLegRemoveBtn = document.getElementById('remove-leg-btn-0');
            if(firstLegRemoveBtn) firstLegRemoveBtn.classList.add('hidden');
        }
    }

    tripTypeOptions.forEach(optionLabel => {
        optionLabel.addEventListener('click', function() {
            // Manually check the radio button associated with this label
            const radioId = this.htmlFor;
            const radioInput = document.getElementById(radioId);
            if (radioInput && !radioInput.checked) {
                radioInput.checked = true;
                // Dispatch change event if needed, or call handler directly
                handleTripTypeChange();
            }
        });
    });
    
    // --- Multi-City Leg Management ---
    function addLegElement() {
        if (legCounter >= 4) { // Max 5 legs (0 to 4)
            alert("Maximum of 5 flight legs allowed for multi-city search.");
            return;
        }
        legCounter++;
        const newSegment = document.createElement('div');
        newSegment.classList.add('od-segment');
        newSegment.id = `od-segment-${legCounter}`;
        // Note: For multi-city, return date is not applicable per leg in this simplified UI
        newSegment.innerHTML = `
            <div class="form-group form-group-origin">
                <label for="origin-${legCounter}"><svg class="icon" viewBox="0 0 24 24"><path fill="currentColor" d="M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z"></path></svg> Origin</label>
                <input type="text" id="origin-${legCounter}" name="origin-${legCounter}" placeholder="City or Airport" required>
                <div class="autocomplete-suggestions" id="origin-${legCounter}-suggestions"></div>
            </div>
            <button type="button" class="swap-od-btn" id="swap-od-btn-${legCounter}" aria-label="Swap origin and destination">
                <svg class="icon" viewBox="0 0 24 24"><path fill="currentColor" d="M6.99 11L3 15l3.99 4v-3H14v-2H6.99v-3zM21 9l-3.99-4v3H10v2h7.01v3L21 9z"></path></svg>
            </button>
            <div class="form-group form-group-destination">
                <label for="destination-${legCounter}"><svg class="icon" viewBox="0 0 24 24"><path fill="currentColor" d="M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z"></path></svg> Destination</label>
                <input type="text" id="destination-${legCounter}" name="destination-${legCounter}" placeholder="City or Airport" required>
                <div class="autocomplete-suggestions" id="destination-${legCounter}-suggestions"></div>
            </div>
            <div class="form-group form-group-date" id="departure-date-group-${legCounter}">
                <label for="departure-date-${legCounter}"><svg class="icon" viewBox="0 0 24 24"><path fill="currentColor" d="M17 13h-5v5h5v-5zM16 2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2h-1V2h-2zm3 18H5V9h14v11z"></path></svg> Departure Date</label>
                <input type="date" id="departure-date-${legCounter}" name="departure-date-${legCounter}" required>
            </div>
            <div class="form-group form-group-date hidden" id="return-date-group-${legCounter}"> {/* Hidden for multi-city */}
                 <label for="return-date-${legCounter}">Return Date</label>
                 <input type="date" id="return-date-${legCounter}" name="return-date-${legCounter}">
            </div>
            <button type="button" class="remove-leg-btn" id="remove-leg-btn-${legCounter}" aria-label="Remove this leg">
                <svg class="icon" viewBox="0 0 24 24"><path fill="currentColor" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"></path></svg>
            </button>
        `;
        odSegmentsContainer.appendChild(newSegment);
        setupAirportInput(`origin-${legCounter}`);
        setupAirportInput(`destination-${legCounter}`);
        newSegment.querySelector(`#departure-date-${legCounter}`).setAttribute('min', getTodayDateString());
        
        newSegment.querySelector('.remove-leg-btn').addEventListener('click', function() {
            odSegmentsContainer.removeChild(newSegment);
            // No need to decrement legCounter here as it's used for adding new, not tracking current count
            // If we were re-indexing, that would be different.
        });
        newSegment.querySelector(`#swap-od-btn-${legCounter}`).addEventListener('click', function() {
            const originInput = document.getElementById(`origin-${legCounter}`);
            const destInput = document.getElementById(`destination-${legCounter}`);
            const temp = originInput.value;
            originInput.value = destInput.value;
            destInput.value = temp;
        });
    }

    if (addMultiCityLegBtn) {
        addMultiCityLegBtn.addEventListener('click', addLegElement);
    }
    
    // --- Passenger Selector Logic ---
    if (passengerSelectorBtn && passengerSelectorDropdown) {
        passengerSelectorBtn.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent click from closing immediately
            passengerSelectorDropdown.classList.toggle('hidden');
        });

        document.addEventListener('click', (e) => { // Close dropdown if clicked outside
            if (!passengerSelectorDropdown.classList.contains('hidden') && 
                !passengerSelectorDropdown.contains(e.target) &&
                !passengerSelectorBtn.contains(e.target)) {
                passengerSelectorDropdown.classList.add('hidden');
            }
        });
    }

    if (passengerDoneBtn) {
        passengerDoneBtn.addEventListener('click', () => {
            passengerSelectorDropdown.classList.add('hidden');
        });
    }
    
    document.querySelectorAll('.counter-btn').forEach(button => {
        button.addEventListener('click', function() {
            const type = this.dataset.type;
            const action = this.classList.contains('plus') ? 'increment' : 'decrement';
            const displaySpan = document.getElementById(`${type}-count-display`);
            let currentValue = parseInt(displaySpan.textContent);

            if (action === 'increment') {
                if (type === 'adults' && currentValue < 9) currentValue++;
                else if (type === 'children' && currentValue < 9) currentValue++;
                else if (type === 'infants' && currentValue < parseInt(document.getElementById('adults-count-display').textContent) && currentValue < 9) currentValue++; // Infants <= Adults
            } else { // decrement
                if (type === 'adults' && currentValue > 1) currentValue--;
                else if (type === 'children' && currentValue > 0) currentValue--;
                else if (type === 'infants' && currentValue > 0) currentValue--;
            }
            displaySpan.textContent = currentValue;
            updatePassengerButtonText();
            validatePassengerCounts(); // Validate after each change
        });
    });

    if(cabinClassSelect) {
        cabinClassSelect.addEventListener('change', updatePassengerButtonText);
    }

    function validatePassengerCounts() {
        const adults = parseInt(document.getElementById('adults-count-display').textContent);
        const infants = parseInt(document.getElementById('infants-count-display').textContent);
        const infantPlusBtn = document.querySelector('.counter-btn.plus[data-type="infants"]');
        
        if (infantPlusBtn) {
            infantPlusBtn.disabled = (infants >= adults);
        }
        // Add more validation rules if needed
    }

    // --- Form Submission ---
    if (flightSearchForm) {
        flightSearchForm.addEventListener('submit', async function (event) {
            event.preventDefault();
            if (loadingIndicator) loadingIndicator.classList.remove('hidden');
            if (errorMessage) errorMessage.classList.add('hidden');
            
            const selectedTripType = getSelectedTripType();
            const segmentsData = [];
            const allSegments = odSegmentsContainer.querySelectorAll('.od-segment');

            for (let i = 0; i < allSegments.length; i++) {
                const segmentDiv = allSegments[i];
                if (selectedTripType === 'one-way' && i > 0) continue;
                if (selectedTripType === 'round-trip' && i > 0) continue; // Handled separately for return date

                const origin = document.getElementById(`origin-${i}`)?.value.trim();
                const destination = document.getElementById(`destination-${i}`)?.value.trim();
                const departureDate = document.getElementById(`departure-date-${i}`)?.value;

                if (!origin || !destination || !departureDate) {
                    if (errorMessage) {
                        errorMessage.textContent = `Please fill all fields for Leg ${i + 1}.`;
                        errorMessage.classList.remove('hidden');
                    }
                    if (loadingIndicator) loadingIndicator.classList.add('hidden');
                    return;
                }
                segmentsData.push({ Origin: origin, Destination: destination, DepartureDate: departureDate });
            }

            if (selectedTripType === 'round-trip') {
                const returnDate = document.getElementById('return-date-0')?.value;
                if (!returnDate) {
                     if (errorMessage) {
                        errorMessage.textContent = "Return date is required for round trip.";
                        errorMessage.classList.remove('hidden');
                    }
                    if (loadingIndicator) loadingIndicator.classList.add('hidden');
                    return;
                }
                // For round trip, the second "segment" is just the return date from the first segment's inputs
                segmentsData.push({ 
                    Origin: segmentsData[0].Destination, // Return origin is first leg's destination
                    Destination: segmentsData[0].Origin,   // Return destination is first leg's origin
                    DepartureDate: returnDate 
                });
            }
            
            const numAdults = parseInt(document.getElementById('adults-count-display').textContent);
            const numChildren = parseInt(document.getElementById('children-count-display').textContent);
            const numInfants = parseInt(document.getElementById('infants-count-display').textContent);
            const cabinPreference = cabinClassSelect.value;

            if (numInfants > numAdults && numAdults > 0) {
                 if (errorMessage) {
                    errorMessage.textContent = "Number of infants cannot exceed adults.";
                    errorMessage.classList.remove('hidden');
                }
                if (loadingIndicator) loadingIndicator.classList.add('hidden');
                return;
            }
            if (numAdults === 0 && (numChildren > 0 || numInfants > 0)) {
                 if (errorMessage) {
                    errorMessage.textContent = "Children or infants must travel with at least one adult.";
                    errorMessage.classList.remove('hidden');
                 }
                if (loadingIndicator) loadingIndicator.classList.add('hidden');
                return;
            }

            const searchCriteria = {
                tripType: selectedTripType.toUpperCase().replace('-', '_'), // e.g., ONE_WAY
                odSegments: segmentsData,
                numAdults: numAdults,
                numChildren: numChildren,
                numInfants: numInfants,
                cabinPreference: cabinPreference
            };
            
            console.log("Sending request to backend with data:", JSON.stringify(searchCriteria, null, 2));
            try {
                const response = await fetch('http://localhost:5000/api/verteil/air-shopping', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                    body: JSON.stringify(searchCriteria)
                });

                if (loadingIndicator) loadingIndicator.classList.add('hidden');

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({ error: `HTTP error! Status: ${response.status}` }));
                    throw new Error(errorData.error || `Server error: ${response.status}`);
                }

                const results = await response.json();
                sessionStorage.setItem('flightSearchResults', JSON.stringify(results.offers || [])); // Assuming backend sends { offers: [...] }
                sessionStorage.setItem('searchCriteria', JSON.stringify(searchCriteria));
                
                // Build query params for results page (simplified)
                const queryParams = new URLSearchParams({
                    origin: searchCriteria.odSegments[0].Origin,
                    destination: searchCriteria.odSegments[0].Destination,
                    departureDate: searchCriteria.odSegments[0].DepartureDate,
                    tripType: searchCriteria.tripType,
                    pax: `${numAdults}A-${numChildren}C-${numInfants}I`
                });
                if (searchCriteria.tripType === 'ROUND_TRIP' && searchCriteria.odSegments[1]) {
                    queryParams.set("returnDate", searchCriteria.odSegments[1].DepartureDate);
                }
                window.location.href = `results.html?${queryParams.toString()}`;

            } catch (error) {
                console.error('Search Error:', error);
                if (loadingIndicator) loadingIndicator.classList.add('hidden');
                if (errorMessage) {
                    errorMessage.textContent = error.message || "Failed to fetch flights. Please try again.";
                    errorMessage.classList.remove('hidden');
                }
            }
        });
    }

    // --- Mobile Navigation Toggle ---
    if (mobileNavToggle && mainNav) {
        mobileNavToggle.addEventListener('click', () => {
            const isExpanded = mobileNavToggle.getAttribute('aria-expanded') === 'true' || false;
            mobileNavToggle.setAttribute('aria-expanded', !isExpanded);
            mobileNavToggle.classList.toggle('active');
            mainNav.classList.toggle('active');
        });
    }
    
    // --- Initialize Form Elements ---
    function getTodayDateString() {
        return new Date().toISOString().split('T')[0];
    }

    document.querySelectorAll('input[type="date"]').forEach(dateInput => {
        dateInput.setAttribute('min', getTodayDateString());
    });
    
    // Setup for initial leg 0
    setupAirportInput('origin-0');
    setupAirportInput('destination-0');
    const swapBtn0 = document.getElementById('swap-od-btn-0');
    if(swapBtn0) {
        swapBtn0.addEventListener('click', function() {
            const originInput = document.getElementById(`origin-0`);
            const destInput = document.getElementById(`destination-0`);
            const temp = originInput.value;
            originInput.value = destInput.value;
            destInput.value = temp;
        });
    }
    // Remove button for leg 0 is initially hidden, shown for multi-city
    const removeBtn0 = document.getElementById('remove-leg-btn-0');
    if(removeBtn0) {
        removeBtn0.addEventListener('click', function() {
            alert("Cannot remove the first leg. Change trip type if you need fewer legs.");
        });
    }


    // Initial setup
    handleTripTypeChange(); // Set form based on default checked radio
    updatePassengerButtonText(); // Set initial passenger button text
    validatePassengerCounts(); // Initial validation for passenger counts

    // Set current year in footer
    const currentYearSpan = document.getElementById('currentYear');
    if (currentYearSpan) {
        currentYearSpan.textContent = new Date().getFullYear();
    }
});
