// js/main.js
document.addEventListener('DOMContentLoaded', function () {
    const flightSearchForm = document.getElementById('flightSearchForm');
    const tripTypeOptions = document.querySelectorAll('.trip-type-option');
    const odSegmentsContainer = document.getElementById('od-segments-container');
    const addMultiCityLegBtn = document.getElementById('addMultiCityLegBtn');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const errorMessage = document.getElementById('errorMessage');
    
    // Passenger Selector Elements
    const passengerSelectorBtn = document.getElementById('passenger-selector-btn');
    const passengerSelectorDropdown = document.getElementById('passenger-selector-dropdown');
    const passengerDoneBtn = document.getElementById('passenger-done-btn');

    // Cabin Selector Elements
    const cabinSelectorBtn = document.getElementById('cabin-selector-btn');
    const cabinSelectorDropdown = document.getElementById('cabin-selector-dropdown');
    const cabinOptionLabels = document.querySelectorAll('#cabin-selector-dropdown .cabin-option');
    const cabinDoneBtn = document.getElementById('cabin-done-btn');

    // Mobile Nav
    const mobileNavToggle = document.querySelector('.mobile-nav-toggle');
    const mainNav = document.querySelector('.main-nav');

    let legCounter = 0; 

    function getSelectedTripType() {
        const selectedRadio = document.querySelector('input[name="tripType"]:checked');
        return selectedRadio ? selectedRadio.value : 'one-way';
    }

    function updatePassengerButtonText() {
        if (!passengerSelectorBtn) return;
        const adults = parseInt(document.getElementById('adults-count-display').textContent);
        const children = parseInt(document.getElementById('children-count-display').textContent);
        const infants = parseInt(document.getElementById('infants-count-display').textContent);

        let text = `${adults} Adult`;
        if (adults > 1) text = `${adults} Adults`;
        if (children > 0) text += `, ${children} Child${children > 1 ? 'ren' : ''}`;
        if (infants > 0) text += `, ${infants} Infant${infants > 1 ? 's' : ''}`;
        passengerSelectorBtn.textContent = text;
    }

    function updateCabinButtonText() {
        if (!cabinSelectorBtn) return;
        const selectedCabinRadio = document.querySelector('input[name="cabinClass"]:checked');
        if (selectedCabinRadio) {
            const label = selectedCabinRadio.closest('.cabin-option');
            const span = label ? label.querySelector('span') : null;
            cabinSelectorBtn.textContent = span ? span.textContent : 'Economy';
        } else {
            cabinSelectorBtn.textContent = 'Economy'; // Default
        }
    }

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
                if (value.length < 2) {
                    suggestionsContainer.classList.remove('active');
                    return;
                }

                const filteredAirports = airports_data.filter(airport => 
                    airport.name.toLowerCase().includes(value) || 
                    airport.iata_code.toLowerCase().includes(value) ||
                    airport.city.toLowerCase().includes(value)
                ).slice(0, 7);

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
            
            document.addEventListener('click', function(e) {
                if (suggestionsContainer && !inputElement.contains(e.target) && !suggestionsContainer.contains(e.target)) {
                    suggestionsContainer.classList.remove('active');
                }
            });
        }
    }
    
    function handleTripTypeChange() {
        const selectedTripType = getSelectedTripType();
        const firstSegment = document.getElementById('od-segment-0');
        const returnDateGroup = document.getElementById('return-date-group-0');

        tripTypeOptions.forEach(optLabel => {
            const radioInput = document.getElementById(optLabel.htmlFor);
            if (radioInput && radioInput.checked) {
                optLabel.classList.add('active');
            } else {
                optLabel.classList.remove('active');
            }
        });

        while (odSegmentsContainer.children.length > 1) {
            if (odSegmentsContainer.lastChild.id !== 'od-segment-0') {
                 odSegmentsContainer.removeChild(odSegmentsContainer.lastChild);
            } else {
                break; 
            }
        }
        legCounter = 0; 

        if (selectedTripType === "one-way") {
            if (returnDateGroup) returnDateGroup.classList.add('hidden');
            if (firstSegment) firstSegment.classList.add('one-way-layout');
            if (addMultiCityLegBtn) addMultiCityLegBtn.classList.add('hidden');
        } else if (selectedTripType === "round-trip") {
            if (returnDateGroup) returnDateGroup.classList.remove('hidden');
            if (firstSegment) firstSegment.classList.remove('one-way-layout');
            if (addMultiCityLegBtn) addMultiCityLegBtn.classList.add('hidden');
        } else if (selectedTripType === "multi-city") {
            if (returnDateGroup) returnDateGroup.classList.add('hidden');
            if (firstSegment) firstSegment.classList.remove('one-way-layout');
            if (addMultiCityLegBtn) addMultiCityLegBtn.classList.remove('hidden');
            if (odSegmentsContainer.children.length < 2) {
                addLegElement();
            }
            const firstLegRemoveBtn = document.getElementById('remove-leg-btn-0');
            if(firstLegRemoveBtn) firstLegRemoveBtn.classList.remove('hidden');
        }

        if (selectedTripType !== "multi-city") {
            const firstLegRemoveBtn = document.getElementById('remove-leg-btn-0');
            if(firstLegRemoveBtn) firstLegRemoveBtn.classList.add('hidden');
        }
    }

    tripTypeOptions.forEach(optionLabel => {
        optionLabel.addEventListener('click', function() {
            const radioId = this.htmlFor;
            const radioInput = document.getElementById(radioId);
            if (radioInput && !radioInput.checked) {
                radioInput.checked = true;
                handleTripTypeChange();
            }
        });
    });
    
    function addLegElement() {
        if (legCounter >= 4) {
            alert("Maximum of 5 flight legs allowed for multi-city search.");
            return;
        }
        legCounter++;
        const newSegment = document.createElement('div');
        newSegment.classList.add('od-segment');
        newSegment.id = `od-segment-${legCounter}`;
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
            <div class="form-group form-group-date hidden" id="return-date-group-${legCounter}">
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
            e.stopPropagation(); 
            passengerSelectorDropdown.classList.toggle('hidden');
            if (cabinSelectorDropdown && !cabinSelectorDropdown.classList.contains('hidden')) { // Close other dropdown
                cabinSelectorDropdown.classList.add('hidden');
            }
        });
    }
    if (passengerDoneBtn) {
        passengerDoneBtn.addEventListener('click', () => {
            if (passengerSelectorDropdown) passengerSelectorDropdown.classList.add('hidden');
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
                else if (type === 'infants' && currentValue < parseInt(document.getElementById('adults-count-display').textContent) && currentValue < 9) currentValue++;
            } else { 
                if (type === 'adults' && currentValue > 1) currentValue--;
                else if (type === 'children' && currentValue > 0) currentValue--;
                else if (type === 'infants' && currentValue > 0) currentValue--;
            }
            displaySpan.textContent = currentValue;
            updatePassengerButtonText();
            validatePassengerCounts(); 
        });
    });

    function validatePassengerCounts() {
        const adults = parseInt(document.getElementById('adults-count-display').textContent);
        const infants = parseInt(document.getElementById('infants-count-display').textContent);
        const infantPlusBtn = document.querySelector('.counter-btn.plus[data-type="infants"]');
        
        if (infantPlusBtn) {
            infantPlusBtn.disabled = (infants >= adults);
        }
    }

    // --- Cabin Selector Logic ---
    if (cabinSelectorBtn && cabinSelectorDropdown) {
        cabinSelectorBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            cabinSelectorDropdown.classList.toggle('hidden');
            if (passengerSelectorDropdown && !passengerSelectorDropdown.classList.contains('hidden')) { // Close other dropdown
                passengerSelectorDropdown.classList.add('hidden');
            }
        });
    }

    cabinOptionLabels.forEach(label => {
        label.addEventListener('click', function() {
            const radioInput = document.getElementById(this.htmlFor);
            if (radioInput && !radioInput.checked) {
                radioInput.checked = true; // Ensure radio is checked
            }
            cabinOptionLabels.forEach(lbl => lbl.classList.remove('active'));
            this.classList.add('active');
            updateCabinButtonText();
            // Optionally close dropdown on selection: cabinSelectorDropdown.classList.add('hidden');
        });
    });

    if (cabinDoneBtn) {
        cabinDoneBtn.addEventListener('click', () => {
            if (cabinSelectorDropdown) cabinSelectorDropdown.classList.add('hidden');
        });
    }
    
    // Global click listener to close dropdowns
    document.addEventListener('click', (e) => {
        if (passengerSelectorDropdown && !passengerSelectorDropdown.classList.contains('hidden') &&
            !passengerSelectorDropdown.contains(e.target) && !passengerSelectorBtn.contains(e.target)) {
            passengerSelectorDropdown.classList.add('hidden');
        }
        if (cabinSelectorDropdown && !cabinSelectorDropdown.classList.contains('hidden') &&
            !cabinSelectorDropdown.contains(e.target) && !cabinSelectorBtn.contains(e.target)) {
            cabinSelectorDropdown.classList.add('hidden');
        }
    });


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
                if (selectedTripType === 'one-way' && i > 0) continue;
                if (selectedTripType === 'round-trip' && i > 0) continue;

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
                segmentsData.push({ 
                    Origin: segmentsData[0].Destination, 
                    Destination: segmentsData[0].Origin,   
                    DepartureDate: returnDate 
                });
            }
            
            const numAdults = parseInt(document.getElementById('adults-count-display').textContent);
            const numChildren = parseInt(document.getElementById('children-count-display').textContent);
            const numInfants = parseInt(document.getElementById('infants-count-display').textContent);
            const selectedCabinRadio = document.querySelector('input[name="cabinClass"]:checked');
            const cabinPreference = selectedCabinRadio ? selectedCabinRadio.value : 'ECONOMY';


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
                tripType: selectedTripType.toUpperCase().replace('-', '_'),
                odSegments: segmentsData,
                numAdults: numAdults,
                numChildren: numChildren,
                numInfants: numInfants,
                cabinPreference: cabinPreference
            };
            
            console.log("Sending request to backend with data:", JSON.stringify(searchCriteria, null, 2));
            try {
                const response = await fetch(`${API_BASE_URL}/api/verteil/air-shopping`, {
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
                // Store the results array directly (it's already the array of offers)
                sessionStorage.setItem('flightSearchResults', JSON.stringify(results || [])); 
                sessionStorage.setItem('searchCriteria', JSON.stringify(searchCriteria));
                
                const queryParams = new URLSearchParams({
                    origin: searchCriteria.odSegments[0].Origin,
                    destination: searchCriteria.odSegments[0].Destination,
                    departureDate: searchCriteria.odSegments[0].DepartureDate,
                    tripType: searchCriteria.tripType,
                    adults: numAdults,
                    children: numChildren,
                    infants: numInfants,
                    cabin: cabinPreference
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

    if (mobileNavToggle && mainNav) {
        mobileNavToggle.addEventListener('click', () => {
            const isExpanded = mobileNavToggle.getAttribute('aria-expanded') === 'true' || false;
            mobileNavToggle.setAttribute('aria-expanded', !isExpanded);
            mobileNavToggle.classList.toggle('active');
            mainNav.classList.toggle('active');
        });
    }
    
    function getTodayDateString() {
        return new Date().toISOString().split('T')[0];
    }

    document.querySelectorAll('input[type="date"]').forEach(dateInput => {
        dateInput.setAttribute('min', getTodayDateString());
    });
    
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
    const removeBtn0 = document.getElementById('remove-leg-btn-0');
    if(removeBtn0) {
        removeBtn0.addEventListener('click', function() {
            alert("Cannot remove the first leg. Change trip type if you need fewer legs.");
        });
    }

    handleTripTypeChange(); 
    updatePassengerButtonText(); 
    updateCabinButtonText(); // Initialize cabin button text
    validatePassengerCounts(); 

    const currentYearSpan = document.getElementById('currentYear');
    if (currentYearSpan) {
        currentYearSpan.textContent = new Date().getFullYear();
    }
});
