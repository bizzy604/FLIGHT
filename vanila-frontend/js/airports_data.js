// js/airports_data.js

const AIRPORTS_DATA = [
    { code: "JFK", name: "John F. Kennedy International Airport", city: "New York", country: "USA" },
    { code: "LGA", name: "LaGuardia Airport", city: "New York", country: "USA" },
    { code: "EWR", name: "Newark Liberty International Airport", city: "Newark/New York", country: "USA" },
    { code: "LAX", name: "Los Angeles International Airport", city: "Los Angeles", country: "USA" },
    { code: "BUR", name: "Hollywood Burbank Airport", city: "Burbank/Los Angeles", country: "USA" },
    { code: "LGB", name: "Long Beach Airport", city: "Long Beach/Los Angeles", country: "USA" },
    { code: "LHR", name: "Heathrow Airport", city: "London", country: "United Kingdom" },
    { code: "LGW", name: "Gatwick Airport", city: "London", country: "United Kingdom" },
    { code: "STN", name: "Stansted Airport", city: "London", country: "United Kingdom" },
    { code: "LTN", name: "Luton Airport", city: "London", country: "United Kingdom" },
    { code: "CDG", name: "Charles de Gaulle Airport", city: "Paris", country: "France" },
    { code: "ORY", name: "Orly Airport", city: "Paris", country: "France" },
    { code: "HND", name: "Haneda Airport", city: "Tokyo", country: "Japan" },
    { code: "NRT", name: "Narita International Airport", city: "Tokyo", country: "Japan" },
    { code: "BOM", name: "Chhatrapati Shivaji Maharaj International Airport", city: "Mumbai", country: "India" },
    { code: "DEL", name: "Indira Gandhi International Airport", city: "Delhi", country: "India" },
    { code: "DXB", name: "Dubai International Airport", city: "Dubai", country: "UAE" },
    { code: "AUH", name: "Abu Dhabi International Airport", city: "Abu Dhabi", country: "UAE" },
    { code: "SIN", name: "Singapore Changi Airport", city: "Singapore", country: "Singapore" },
    { code: "HKG", name: "Hong Kong International Airport", city: "Hong Kong", country: "China" },
    { code: "AMS", name: "Amsterdam Airport Schiphol", city: "Amsterdam", country: "Netherlands" },
    { code: "FRA", name: "Frankfurt Airport", city: "Frankfurt", country: "Germany" },
    { code: "MUC", name: "Munich Airport", city: "Munich", country: "Germany" },
    { code: "SYD", name: "Sydney Kingsford Smith Airport", city: "Sydney", country: "Australia" },
    { code: "MEL", name: "Melbourne Airport", city: "Melbourne", country: "Australia" },
    { code: "YYZ", name: "Toronto Pearson International Airport", city: "Toronto", country: "Canada" },
    { code: "YVR", name: "Vancouver International Airport", city: "Vancouver", country: "Canada" },
    // Add more airports
  ];
  
  // Function to populate datalist suggestions
  function populateAirportSuggestions(inputId, datalistId, searchTerm) {
      const datalist = document.getElementById(datalistId);
      if (!datalist) return;
  
      datalist.innerHTML = ''; // Clear previous suggestions
      if (!searchTerm || searchTerm.length < 2) return; // Start suggesting after 2 chars
  
      const lowerSearchTerm = searchTerm.toLowerCase();
      const filtered = AIRPORTS_DATA.filter(airport => 
          airport.city.toLowerCase().includes(lowerSearchTerm) ||
          airport.name.toLowerCase().includes(lowerSearchTerm) ||
          airport.code.toLowerCase().includes(lowerSearchTerm)
      ).slice(0, 10); // Limit suggestions
  
      filtered.forEach(airport => {
          const option = document.createElement('option');
          option.value = airport.code; // Value will be the code
          option.textContent = `${airport.city} - ${airport.name} (${airport.code})`; // Text displayed in dropdown
          datalist.appendChild(option);
      });
  }