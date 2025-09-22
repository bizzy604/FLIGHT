/**
 * Comprehensive countries data for passenger form
 * Includes all UN member states and major territories
 * Data follows ISO 3166-1 alpha-2 standard
 */

export interface Country {
  code: string;        // ISO 3166-1 alpha-2 country code
  name: string;        // Full country name
  flag: string;        // Unicode flag emoji
  region: string;      // Geographic region for grouping
  commonName?: string; // Alternative common name
}

export const COUNTRIES: Country[] = [
  // Africa
  { code: "DZ", name: "Algeria", flag: "🇩🇿", region: "Africa" },
  { code: "AO", name: "Angola", flag: "🇦🇴", region: "Africa" },
  { code: "BJ", name: "Benin", flag: "🇧🇯", region: "Africa" },
  { code: "BW", name: "Botswana", flag: "🇧🇼", region: "Africa" },
  { code: "BF", name: "Burkina Faso", flag: "🇧🇫", region: "Africa" },
  { code: "BI", name: "Burundi", flag: "🇧🇮", region: "Africa" },
  { code: "CV", name: "Cape Verde", flag: "🇨🇻", region: "Africa" },
  { code: "CM", name: "Cameroon", flag: "🇨🇲", region: "Africa" },
  { code: "CF", name: "Central African Republic", flag: "🇨🇫", region: "Africa" },
  { code: "TD", name: "Chad", flag: "🇹🇩", region: "Africa" },
  { code: "KM", name: "Comoros", flag: "🇰🇲", region: "Africa" },
  { code: "CG", name: "Congo", flag: "🇨🇬", region: "Africa" },
  { code: "CD", name: "Congo, Democratic Republic of the", flag: "🇨🇩", region: "Africa" },
  { code: "CI", name: "Côte d'Ivoire", flag: "🇨🇮", region: "Africa" },
  { code: "DJ", name: "Djibouti", flag: "🇩🇯", region: "Africa" },
  { code: "EG", name: "Egypt", flag: "🇪🇬", region: "Africa" },
  { code: "GQ", name: "Equatorial Guinea", flag: "🇬🇶", region: "Africa" },
  { code: "ER", name: "Eritrea", flag: "🇪🇷", region: "Africa" },
  { code: "ET", name: "Ethiopia", flag: "🇪🇹", region: "Africa" },
  { code: "GA", name: "Gabon", flag: "🇬🇦", region: "Africa" },
  { code: "GM", name: "Gambia", flag: "🇬🇲", region: "Africa" },
  { code: "GH", name: "Ghana", flag: "🇬🇭", region: "Africa" },
  { code: "GN", name: "Guinea", flag: "🇬🇳", region: "Africa" },
  { code: "GW", name: "Guinea-Bissau", flag: "🇬🇼", region: "Africa" },
  { code: "KE", name: "Kenya", flag: "🇰🇪", region: "Africa" },
  { code: "LS", name: "Lesotho", flag: "🇱🇸", region: "Africa" },
  { code: "LR", name: "Liberia", flag: "🇱🇷", region: "Africa" },
  { code: "LY", name: "Libya", flag: "🇱🇾", region: "Africa" },
  { code: "MG", name: "Madagascar", flag: "🇲🇬", region: "Africa" },
  { code: "MW", name: "Malawi", flag: "🇲🇼", region: "Africa" },
  { code: "ML", name: "Mali", flag: "🇲🇱", region: "Africa" },
  { code: "MR", name: "Mauritania", flag: "🇲🇷", region: "Africa" },
  { code: "MU", name: "Mauritius", flag: "🇲🇺", region: "Africa" },
  { code: "MA", name: "Morocco", flag: "🇲🇦", region: "Africa" },
  { code: "MZ", name: "Mozambique", flag: "🇲🇿", region: "Africa" },
  { code: "NA", name: "Namibia", flag: "🇳🇦", region: "Africa" },
  { code: "NE", name: "Niger", flag: "🇳🇪", region: "Africa" },
  { code: "NG", name: "Nigeria", flag: "🇳🇬", region: "Africa" },
  { code: "RW", name: "Rwanda", flag: "🇷🇼", region: "Africa" },
  { code: "ST", name: "São Tomé and Príncipe", flag: "🇸🇹", region: "Africa" },
  { code: "SN", name: "Senegal", flag: "🇸🇳", region: "Africa" },
  { code: "SC", name: "Seychelles", flag: "🇸🇨", region: "Africa" },
  { code: "SL", name: "Sierra Leone", flag: "🇸🇱", region: "Africa" },
  { code: "SO", name: "Somalia", flag: "🇸🇴", region: "Africa" },
  { code: "ZA", name: "South Africa", flag: "🇿🇦", region: "Africa" },
  { code: "SS", name: "South Sudan", flag: "🇸🇸", region: "Africa" },
  { code: "SD", name: "Sudan", flag: "🇸🇩", region: "Africa" },
  { code: "SZ", name: "Eswatini", flag: "🇸🇿", region: "Africa" },
  { code: "TZ", name: "Tanzania", flag: "🇹🇿", region: "Africa" },
  { code: "TG", name: "Togo", flag: "🇹🇬", region: "Africa" },
  { code: "TN", name: "Tunisia", flag: "🇹🇳", region: "Africa" },
  { code: "UG", name: "Uganda", flag: "🇺🇬", region: "Africa" },
  { code: "ZM", name: "Zambia", flag: "🇿🇲", region: "Africa" },
  { code: "ZW", name: "Zimbabwe", flag: "🇿🇼", region: "Africa" },

  // Asia
  { code: "AF", name: "Afghanistan", flag: "🇦🇫", region: "Asia" },
  { code: "AM", name: "Armenia", flag: "🇦🇲", region: "Asia" },
  { code: "AZ", name: "Azerbaijan", flag: "🇦🇿", region: "Asia" },
  { code: "BH", name: "Bahrain", flag: "🇧🇭", region: "Asia" },
  { code: "BD", name: "Bangladesh", flag: "🇧🇩", region: "Asia" },
  { code: "BT", name: "Bhutan", flag: "🇧🇹", region: "Asia" },
  { code: "BN", name: "Brunei", flag: "🇧🇳", region: "Asia" },
  { code: "KH", name: "Cambodia", flag: "🇰🇭", region: "Asia" },
  { code: "CN", name: "China", flag: "🇨🇳", region: "Asia" },
  { code: "GE", name: "Georgia", flag: "🇬🇪", region: "Asia" },
  { code: "IN", name: "India", flag: "🇮🇳", region: "Asia" },
  { code: "ID", name: "Indonesia", flag: "🇮🇩", region: "Asia" },
  { code: "IR", name: "Iran", flag: "🇮🇷", region: "Asia" },
  { code: "IQ", name: "Iraq", flag: "🇮🇶", region: "Asia" },
  { code: "IL", name: "Israel", flag: "🇮🇱", region: "Asia" },
  { code: "JP", name: "Japan", flag: "🇯🇵", region: "Asia" },
  { code: "JO", name: "Jordan", flag: "🇯🇴", region: "Asia" },
  { code: "KZ", name: "Kazakhstan", flag: "🇰🇿", region: "Asia" },
  { code: "KW", name: "Kuwait", flag: "🇰🇼", region: "Asia" },
  { code: "KG", name: "Kyrgyzstan", flag: "🇰🇬", region: "Asia" },
  { code: "LA", name: "Laos", flag: "🇱🇦", region: "Asia" },
  { code: "LB", name: "Lebanon", flag: "🇱🇧", region: "Asia" },
  { code: "MY", name: "Malaysia", flag: "🇲🇾", region: "Asia" },
  { code: "MV", name: "Maldives", flag: "🇲🇻", region: "Asia" },
  { code: "MN", name: "Mongolia", flag: "🇲🇳", region: "Asia" },
  { code: "MM", name: "Myanmar", flag: "🇲🇲", region: "Asia" },
  { code: "NP", name: "Nepal", flag: "🇳🇵", region: "Asia" },
  { code: "KP", name: "North Korea", flag: "🇰🇵", region: "Asia" },
  { code: "OM", name: "Oman", flag: "🇴🇲", region: "Asia" },
  { code: "PK", name: "Pakistan", flag: "🇵🇰", region: "Asia" },
  { code: "PS", name: "Palestine", flag: "🇵🇸", region: "Asia" },
  { code: "PH", name: "Philippines", flag: "🇵🇭", region: "Asia" },
  { code: "QA", name: "Qatar", flag: "🇶🇦", region: "Asia" },
  { code: "SA", name: "Saudi Arabia", flag: "🇸🇦", region: "Asia" },
  { code: "SG", name: "Singapore", flag: "🇸🇬", region: "Asia" },
  { code: "KR", name: "South Korea", flag: "🇰🇷", region: "Asia" },
  { code: "LK", name: "Sri Lanka", flag: "🇱🇰", region: "Asia" },
  { code: "SY", name: "Syria", flag: "🇸🇾", region: "Asia" },
  { code: "TW", name: "Taiwan", flag: "🇹🇼", region: "Asia" },
  { code: "TJ", name: "Tajikistan", flag: "🇹🇯", region: "Asia" },
  { code: "TH", name: "Thailand", flag: "🇹🇭", region: "Asia" },
  { code: "TL", name: "Timor-Leste", flag: "🇹🇱", region: "Asia" },
  { code: "TR", name: "Turkey", flag: "🇹🇷", region: "Asia" },
  { code: "TM", name: "Turkmenistan", flag: "🇹🇲", region: "Asia" },
  { code: "AE", name: "United Arab Emirates", flag: "🇦🇪", region: "Asia" },
  { code: "UZ", name: "Uzbekistan", flag: "🇺🇿", region: "Asia" },
  { code: "VN", name: "Vietnam", flag: "🇻🇳", region: "Asia" },
  { code: "YE", name: "Yemen", flag: "🇾🇪", region: "Asia" },

  // Europe
  { code: "AL", name: "Albania", flag: "🇦🇱", region: "Europe" },
  { code: "AD", name: "Andorra", flag: "🇦🇩", region: "Europe" },
  { code: "AT", name: "Austria", flag: "🇦🇹", region: "Europe" },
  { code: "BY", name: "Belarus", flag: "🇧🇾", region: "Europe" },
  { code: "BE", name: "Belgium", flag: "🇧🇪", region: "Europe" },
  { code: "BA", name: "Bosnia and Herzegovina", flag: "🇧🇦", region: "Europe" },
  { code: "BG", name: "Bulgaria", flag: "🇧🇬", region: "Europe" },
  { code: "HR", name: "Croatia", flag: "🇭🇷", region: "Europe" },
  { code: "CY", name: "Cyprus", flag: "🇨🇾", region: "Europe" },
  { code: "CZ", name: "Czech Republic", flag: "🇨🇿", region: "Europe" },
  { code: "DK", name: "Denmark", flag: "🇩🇰", region: "Europe" },
  { code: "EE", name: "Estonia", flag: "🇪🇪", region: "Europe" },
  { code: "FI", name: "Finland", flag: "🇫🇮", region: "Europe" },
  { code: "FR", name: "France", flag: "🇫🇷", region: "Europe" },
  { code: "DE", name: "Germany", flag: "🇩🇪", region: "Europe" },
  { code: "GR", name: "Greece", flag: "🇬🇷", region: "Europe" },
  { code: "HU", name: "Hungary", flag: "🇭🇺", region: "Europe" },
  { code: "IS", name: "Iceland", flag: "🇮🇸", region: "Europe" },
  { code: "IE", name: "Ireland", flag: "🇮🇪", region: "Europe" },
  { code: "IT", name: "Italy", flag: "🇮🇹", region: "Europe" },
  { code: "LV", name: "Latvia", flag: "🇱🇻", region: "Europe" },
  { code: "LI", name: "Liechtenstein", flag: "🇱🇮", region: "Europe" },
  { code: "LT", name: "Lithuania", flag: "🇱🇹", region: "Europe" },
  { code: "LU", name: "Luxembourg", flag: "🇱🇺", region: "Europe" },
  { code: "MT", name: "Malta", flag: "🇲🇹", region: "Europe" },
  { code: "MD", name: "Moldova", flag: "🇲🇩", region: "Europe" },
  { code: "MC", name: "Monaco", flag: "🇲🇨", region: "Europe" },
  { code: "ME", name: "Montenegro", flag: "🇲🇪", region: "Europe" },
  { code: "NL", name: "Netherlands", flag: "🇳🇱", region: "Europe" },
  { code: "MK", name: "North Macedonia", flag: "🇲🇰", region: "Europe" },
  { code: "NO", name: "Norway", flag: "🇳🇴", region: "Europe" },
  { code: "PL", name: "Poland", flag: "🇵🇱", region: "Europe" },
  { code: "PT", name: "Portugal", flag: "🇵🇹", region: "Europe" },
  { code: "RO", name: "Romania", flag: "🇷🇴", region: "Europe" },
  { code: "RU", name: "Russia", flag: "🇷🇺", region: "Europe" },
  { code: "SM", name: "San Marino", flag: "🇸🇲", region: "Europe" },
  { code: "RS", name: "Serbia", flag: "🇷🇸", region: "Europe" },
  { code: "SK", name: "Slovakia", flag: "🇸🇰", region: "Europe" },
  { code: "SI", name: "Slovenia", flag: "🇸🇮", region: "Europe" },
  { code: "ES", name: "Spain", flag: "🇪🇸", region: "Europe" },
  { code: "SE", name: "Sweden", flag: "🇸🇪", region: "Europe" },
  { code: "CH", name: "Switzerland", flag: "🇨🇭", region: "Europe" },
  { code: "UA", name: "Ukraine", flag: "🇺🇦", region: "Europe" },
  { code: "GB", name: "United Kingdom", flag: "🇬🇧", region: "Europe" },
  { code: "VA", name: "Vatican City", flag: "🇻🇦", region: "Europe" },

  // North America
  { code: "CA", name: "Canada", flag: "🇨🇦", region: "North America" },
  { code: "MX", name: "Mexico", flag: "🇲🇽", region: "North America" },
  { code: "US", name: "United States", flag: "🇺🇸", region: "North America" },
  { code: "AG", name: "Antigua and Barbuda", flag: "🇦🇬", region: "North America" },
  { code: "BS", name: "Bahamas", flag: "🇧🇸", region: "North America" },
  { code: "BB", name: "Barbados", flag: "🇧🇧", region: "North America" },
  { code: "BZ", name: "Belize", flag: "🇧🇿", region: "North America" },
  { code: "CR", name: "Costa Rica", flag: "🇨🇷", region: "North America" },
  { code: "CU", name: "Cuba", flag: "🇨🇺", region: "North America" },
  { code: "DM", name: "Dominica", flag: "🇩🇲", region: "North America" },
  { code: "DO", name: "Dominican Republic", flag: "🇩🇴", region: "North America" },
  { code: "SV", name: "El Salvador", flag: "🇸🇻", region: "North America" },
  { code: "GD", name: "Grenada", flag: "🇬🇩", region: "North America" },
  { code: "GT", name: "Guatemala", flag: "🇬🇹", region: "North America" },
  { code: "HN", name: "Honduras", flag: "🇭🇳", region: "North America" },
  { code: "JM", name: "Jamaica", flag: "🇯🇲", region: "North America" },
  { code: "NI", name: "Nicaragua", flag: "🇳🇮", region: "North America" },
  { code: "PA", name: "Panama", flag: "🇵🇦", region: "North America" },
  { code: "KN", name: "Saint Kitts and Nevis", flag: "🇰🇳", region: "North America" },
  { code: "LC", name: "Saint Lucia", flag: "🇱🇨", region: "North America" },
  { code: "VC", name: "Saint Vincent and the Grenadines", flag: "🇻🇨", region: "North America" },
  { code: "TT", name: "Trinidad and Tobago", flag: "🇹🇹", region: "North America" },

  // South America
  { code: "AR", name: "Argentina", flag: "🇦🇷", region: "South America" },
  { code: "BO", name: "Bolivia", flag: "🇧🇴", region: "South America" },
  { code: "BR", name: "Brazil", flag: "🇧🇷", region: "South America" },
  { code: "CL", name: "Chile", flag: "🇨🇱", region: "South America" },
  { code: "CO", name: "Colombia", flag: "🇨🇴", region: "South America" },
  { code: "EC", name: "Ecuador", flag: "🇪🇨", region: "South America" },
  { code: "GY", name: "Guyana", flag: "🇬🇾", region: "South America" },
  { code: "PY", name: "Paraguay", flag: "🇵🇾", region: "South America" },
  { code: "PE", name: "Peru", flag: "🇵🇪", region: "South America" },
  { code: "SR", name: "Suriname", flag: "🇸🇷", region: "South America" },
  { code: "UY", name: "Uruguay", flag: "🇺🇾", region: "South America" },
  { code: "VE", name: "Venezuela", flag: "🇻🇪", region: "South America" },

  // Oceania
  { code: "AU", name: "Australia", flag: "🇦🇺", region: "Oceania" },
  { code: "FJ", name: "Fiji", flag: "🇫🇯", region: "Oceania" },
  { code: "KI", name: "Kiribati", flag: "🇰🇮", region: "Oceania" },
  { code: "MH", name: "Marshall Islands", flag: "🇲🇭", region: "Oceania" },
  { code: "FM", name: "Micronesia", flag: "🇫🇲", region: "Oceania" },
  { code: "NR", name: "Nauru", flag: "🇳🇷", region: "Oceania" },
  { code: "NZ", name: "New Zealand", flag: "🇳🇿", region: "Oceania" },
  { code: "PW", name: "Palau", flag: "🇵🇼", region: "Oceania" },
  { code: "PG", name: "Papua New Guinea", flag: "🇵🇬", region: "Oceania" },
  { code: "WS", name: "Samoa", flag: "🇼🇸", region: "Oceania" },
  { code: "SB", name: "Solomon Islands", flag: "🇸🇧", region: "Oceania" },
  { code: "TO", name: "Tonga", flag: "🇹🇴", region: "Oceania" },
  { code: "TV", name: "Tuvalu", flag: "🇹🇻", region: "Oceania" },
  { code: "VU", name: "Vanuatu", flag: "🇻🇺", region: "Oceania" },
];

// Helper functions
export const getCountriesByRegion = (region: string): Country[] => {
  return COUNTRIES.filter(country => country.region === region);
};

export const searchCountries = (query: string): Country[] => {
  const lowercaseQuery = query.toLowerCase();
  return COUNTRIES.filter(country => 
    country.name.toLowerCase().includes(lowercaseQuery) ||
    country.code.toLowerCase().includes(lowercaseQuery) ||
    (country.commonName && country.commonName.toLowerCase().includes(lowercaseQuery))
  );
};

export const getCountryByCode = (code: string): Country | undefined => {
  return COUNTRIES.find(country => country.code.toLowerCase() === code.toLowerCase());
};

export const getCountryByName = (name: string): Country | undefined => {
  return COUNTRIES.find(country => 
    country.name.toLowerCase() === name.toLowerCase() ||
    (country.commonName && country.commonName.toLowerCase() === name.toLowerCase())
  );
};

// Get all unique regions
export const getRegions = (): string[] => {
  return Array.from(new Set(COUNTRIES.map(country => country.region))).sort(); 
};

// Sort countries alphabetically by name
export const getSortedCountries = (): Country[] => {
  return [...COUNTRIES].sort((a, b) => a.name.localeCompare(b.name));
};

// Get countries grouped by region
export const getCountriesByRegionGrouped = (): Record<string, Country[]> => {
  const grouped: Record<string, Country[]> = {};
  COUNTRIES.forEach(country => {
    if (!grouped[country.region]) {
      grouped[country.region] = [];
    }
    grouped[country.region].push(country);
  });
  
  // Sort countries within each region
  Object.keys(grouped).forEach(region => {
    grouped[region].sort((a, b) => a.name.localeCompare(b.name));
  });
  
  return grouped;
};
