/**
 * Comprehensive country codes utility for phone numbers
 * Includes international dialing codes for all countries
 * Data follows ITU-T E.164 standard
 */

export interface CountryCode {
  code: string;           // ISO 3166-1 alpha-2 country code
  name: string;           // Country name
  dialCode: string;       // International dialing code (e.g., "+1", "+44")
  flag: string;           // Unicode flag emoji
  region: string;         // Geographic region
  priority?: number;      // Priority for sorting (higher = more common)
}

export const COUNTRY_CODES: CountryCode[] = [
  // Most common countries (high priority)
  { code: "US", name: "United States", dialCode: "+1", flag: "🇺🇸", region: "North America", priority: 100 },
  { code: "GB", name: "United Kingdom", dialCode: "+44", flag: "🇬🇧", region: "Europe", priority: 95 },
  { code: "CA", name: "Canada", dialCode: "+1", flag: "🇨🇦", region: "North America", priority: 90 },
  { code: "AU", name: "Australia", dialCode: "+61", flag: "🇦🇺", region: "Oceania", priority: 85 },
  { code: "DE", name: "Germany", dialCode: "+49", flag: "🇩🇪", region: "Europe", priority: 80 },
  { code: "FR", name: "France", dialCode: "+33", flag: "🇫🇷", region: "Europe", priority: 80 },
  { code: "IT", name: "Italy", dialCode: "+39", flag: "🇮🇹", region: "Europe", priority: 75 },
  { code: "ES", name: "Spain", dialCode: "+34", flag: "🇪🇸", region: "Europe", priority: 75 },
  { code: "NL", name: "Netherlands", dialCode: "+31", flag: "🇳🇱", region: "Europe", priority: 70 },
  { code: "JP", name: "Japan", dialCode: "+81", flag: "🇯🇵", region: "Asia", priority: 70 },
  { code: "CN", name: "China", dialCode: "+86", flag: "🇨🇳", region: "Asia", priority: 70 },
  { code: "IN", name: "India", dialCode: "+91", flag: "🇮🇳", region: "Asia", priority: 70 },
  { code: "BR", name: "Brazil", dialCode: "+55", flag: "🇧🇷", region: "South America", priority: 65 },
  { code: "KE", name: "Kenya", dialCode: "+254", flag: "🇰🇪", region: "Africa", priority: 60 },
  { code: "ZA", name: "South Africa", dialCode: "+27", flag: "🇿🇦", region: "Africa", priority: 60 },

  // Europe
  { code: "SE", name: "Sweden", dialCode: "+46", flag: "🇸🇪", region: "Europe", priority: 50 },
  { code: "NO", name: "Norway", dialCode: "+47", flag: "🇳🇴", region: "Europe", priority: 50 },
  { code: "DK", name: "Denmark", dialCode: "+45", flag: "🇩🇰", region: "Europe", priority: 50 },
  { code: "FI", name: "Finland", dialCode: "+358", flag: "🇫🇮", region: "Europe", priority: 50 },
  { code: "CH", name: "Switzerland", dialCode: "+41", flag: "🇨🇭", region: "Europe", priority: 50 },
  { code: "AT", name: "Austria", dialCode: "+43", flag: "🇦🇹", region: "Europe", priority: 45 },
  { code: "BE", name: "Belgium", dialCode: "+32", flag: "🇧🇪", region: "Europe", priority: 45 },
  { code: "IE", name: "Ireland", dialCode: "+353", flag: "🇮🇪", region: "Europe", priority: 45 },
  { code: "PT", name: "Portugal", dialCode: "+351", flag: "🇵🇹", region: "Europe", priority: 45 },
  { code: "GR", name: "Greece", dialCode: "+30", flag: "🇬🇷", region: "Europe", priority: 40 },
  { code: "PL", name: "Poland", dialCode: "+48", flag: "🇵🇱", region: "Europe", priority: 40 },
  { code: "CZ", name: "Czech Republic", dialCode: "+420", flag: "🇨🇿", region: "Europe", priority: 40 },
  { code: "HU", name: "Hungary", dialCode: "+36", flag: "🇭🇺", region: "Europe", priority: 40 },
  { code: "RO", name: "Romania", dialCode: "+40", flag: "🇷🇴", region: "Europe", priority: 40 },
  { code: "BG", name: "Bulgaria", dialCode: "+359", flag: "🇧🇬", region: "Europe", priority: 35 },
  { code: "HR", name: "Croatia", dialCode: "+385", flag: "🇭🇷", region: "Europe", priority: 35 },
  { code: "SI", name: "Slovenia", dialCode: "+386", flag: "🇸🇮", region: "Europe", priority: 35 },
  { code: "SK", name: "Slovakia", dialCode: "+421", flag: "🇸🇰", region: "Europe", priority: 35 },
  { code: "LT", name: "Lithuania", dialCode: "+370", flag: "🇱🇹", region: "Europe", priority: 35 },
  { code: "LV", name: "Latvia", dialCode: "+371", flag: "🇱🇻", region: "Europe", priority: 35 },
  { code: "EE", name: "Estonia", dialCode: "+372", flag: "🇪🇪", region: "Europe", priority: 35 },
  { code: "RU", name: "Russia", dialCode: "+7", flag: "🇷🇺", region: "Europe", priority: 40 },
  { code: "UA", name: "Ukraine", dialCode: "+380", flag: "🇺🇦", region: "Europe", priority: 35 },
  { code: "TR", name: "Turkey", dialCode: "+90", flag: "🇹🇷", region: "Europe", priority: 40 },

  // Asia
  { code: "KR", name: "South Korea", dialCode: "+82", flag: "🇰🇷", region: "Asia", priority: 60 },
  { code: "SG", name: "Singapore", dialCode: "+65", flag: "🇸🇬", region: "Asia", priority: 55 },
  { code: "HK", name: "Hong Kong", dialCode: "+852", flag: "🇭🇰", region: "Asia", priority: 55 },
  { code: "TW", name: "Taiwan", dialCode: "+886", flag: "🇹🇼", region: "Asia", priority: 50 },
  { code: "TH", name: "Thailand", dialCode: "+66", flag: "🇹🇭", region: "Asia", priority: 50 },
  { code: "MY", name: "Malaysia", dialCode: "+60", flag: "🇲🇾", region: "Asia", priority: 50 },
  { code: "ID", name: "Indonesia", dialCode: "+62", flag: "🇮🇩", region: "Asia", priority: 50 },
  { code: "PH", name: "Philippines", dialCode: "+63", flag: "🇵🇭", region: "Asia", priority: 50 },
  { code: "VN", name: "Vietnam", dialCode: "+84", flag: "🇻🇳", region: "Asia", priority: 50 },
  { code: "BD", name: "Bangladesh", dialCode: "+880", flag: "🇧🇩", region: "Asia", priority: 45 },
  { code: "PK", name: "Pakistan", dialCode: "+92", flag: "🇵🇰", region: "Asia", priority: 45 },
  { code: "LK", name: "Sri Lanka", dialCode: "+94", flag: "🇱🇰", region: "Asia", priority: 40 },
  { code: "NP", name: "Nepal", dialCode: "+977", flag: "🇳🇵", region: "Asia", priority: 40 },
  { code: "MM", name: "Myanmar", dialCode: "+95", flag: "🇲🇲", region: "Asia", priority: 40 },
  { code: "KH", name: "Cambodia", dialCode: "+855", flag: "🇰🇭", region: "Asia", priority: 40 },
  { code: "LA", name: "Laos", dialCode: "+856", flag: "🇱🇦", region: "Asia", priority: 40 },
  { code: "MN", name: "Mongolia", dialCode: "+976", flag: "🇲🇳", region: "Asia", priority: 40 },
  { code: "KZ", name: "Kazakhstan", dialCode: "+7", flag: "🇰🇿", region: "Asia", priority: 40 },
  { code: "UZ", name: "Uzbekistan", dialCode: "+998", flag: "🇺🇿", region: "Asia", priority: 40 },
  { code: "KG", name: "Kyrgyzstan", dialCode: "+996", flag: "🇰🇬", region: "Asia", priority: 40 },
  { code: "TJ", name: "Tajikistan", dialCode: "+992", flag: "🇹🇯", region: "Asia", priority: 40 },
  { code: "TM", name: "Turkmenistan", dialCode: "+993", flag: "🇹🇲", region: "Asia", priority: 40 },
  { code: "AF", name: "Afghanistan", dialCode: "+93", flag: "🇦🇫", region: "Asia", priority: 40 },
  { code: "IR", name: "Iran", dialCode: "+98", flag: "🇮🇷", region: "Asia", priority: 40 },
  { code: "IQ", name: "Iraq", dialCode: "+964", flag: "🇮🇶", region: "Asia", priority: 40 },
  { code: "IL", name: "Israel", dialCode: "+972", flag: "🇮🇱", region: "Asia", priority: 40 },
  { code: "JO", name: "Jordan", dialCode: "+962", flag: "🇯🇴", region: "Asia", priority: 40 },
  { code: "LB", name: "Lebanon", dialCode: "+961", flag: "🇱🇧", region: "Asia", priority: 40 },
  { code: "SY", name: "Syria", dialCode: "+963", flag: "🇸🇾", region: "Asia", priority: 40 },
  { code: "SA", name: "Saudi Arabia", dialCode: "+966", flag: "🇸🇦", region: "Asia", priority: 45 },
  { code: "AE", name: "United Arab Emirates", dialCode: "+971", flag: "🇦🇪", region: "Asia", priority: 45 },
  { code: "QA", name: "Qatar", dialCode: "+974", flag: "🇶🇦", region: "Asia", priority: 45 },
  { code: "KW", name: "Kuwait", dialCode: "+965", flag: "🇰🇼", region: "Asia", priority: 45 },
  { code: "BH", name: "Bahrain", dialCode: "+973", flag: "🇧🇭", region: "Asia", priority: 45 },
  { code: "OM", name: "Oman", dialCode: "+968", flag: "🇴🇲", region: "Asia", priority: 45 },
  { code: "YE", name: "Yemen", dialCode: "+967", flag: "🇾🇪", region: "Asia", priority: 40 },

  // Africa
  { code: "NG", name: "Nigeria", dialCode: "+234", flag: "🇳🇬", region: "Africa", priority: 55 },
  { code: "EG", name: "Egypt", dialCode: "+20", flag: "🇪🇬", region: "Africa", priority: 50 },
  { code: "ET", name: "Ethiopia", dialCode: "+251", flag: "🇪🇹", region: "Africa", priority: 50 },
  { code: "GH", name: "Ghana", dialCode: "+233", flag: "🇬🇭", region: "Africa", priority: 50 },
  { code: "TZ", name: "Tanzania", dialCode: "+255", flag: "🇹🇿", region: "Africa", priority: 50 },
  { code: "UG", name: "Uganda", dialCode: "+256", flag: "🇺🇬", region: "Africa", priority: 50 },
  { code: "RW", name: "Rwanda", dialCode: "+250", flag: "🇷🇼", region: "Africa", priority: 50 },
  { code: "MW", name: "Malawi", dialCode: "+265", flag: "🇲🇼", region: "Africa", priority: 45 },
  { code: "ZM", name: "Zambia", dialCode: "+260", flag: "🇿🇲", region: "Africa", priority: 45 },
  { code: "ZW", name: "Zimbabwe", dialCode: "+263", flag: "🇿🇼", region: "Africa", priority: 45 },
  { code: "BW", name: "Botswana", dialCode: "+267", flag: "🇧🇼", region: "Africa", priority: 45 },
  { code: "NA", name: "Namibia", dialCode: "+264", flag: "🇳🇦", region: "Africa", priority: 45 },
  { code: "SZ", name: "Eswatini", dialCode: "+268", flag: "🇸🇿", region: "Africa", priority: 45 },
  { code: "LS", name: "Lesotho", dialCode: "+266", flag: "🇱🇸", region: "Africa", priority: 45 },
  { code: "MZ", name: "Mozambique", dialCode: "+258", flag: "🇲🇿", region: "Africa", priority: 45 },
  { code: "MG", name: "Madagascar", dialCode: "+261", flag: "🇲🇬", region: "Africa", priority: 45 },
  { code: "MU", name: "Mauritius", dialCode: "+230", flag: "🇲🇺", region: "Africa", priority: 45 },
  { code: "SC", name: "Seychelles", dialCode: "+248", flag: "🇸🇨", region: "Africa", priority: 45 },
  { code: "KM", name: "Comoros", dialCode: "+269", flag: "🇰🇲", region: "Africa", priority: 45 },
  { code: "DJ", name: "Djibouti", dialCode: "+253", flag: "🇩🇯", region: "Africa", priority: 45 },
  { code: "SO", name: "Somalia", dialCode: "+252", flag: "🇸🇴", region: "Africa", priority: 45 },
  { code: "ER", name: "Eritrea", dialCode: "+291", flag: "🇪🇷", region: "Africa", priority: 45 },
  { code: "SD", name: "Sudan", dialCode: "+249", flag: "🇸🇩", region: "Africa", priority: 45 },
  { code: "SS", name: "South Sudan", dialCode: "+211", flag: "🇸🇸", region: "Africa", priority: 45 },
  { code: "CF", name: "Central African Republic", dialCode: "+236", flag: "🇨🇫", region: "Africa", priority: 40 },
  { code: "TD", name: "Chad", dialCode: "+235", flag: "🇹🇩", region: "Africa", priority: 40 },
  { code: "CM", name: "Cameroon", dialCode: "+237", flag: "🇨🇲", region: "Africa", priority: 40 },
  { code: "GQ", name: "Equatorial Guinea", dialCode: "+240", flag: "🇬🇶", region: "Africa", priority: 40 },
  { code: "GA", name: "Gabon", dialCode: "+241", flag: "🇬🇦", region: "Africa", priority: 40 },
  { code: "CG", name: "Congo", dialCode: "+242", flag: "🇨🇬", region: "Africa", priority: 40 },
  { code: "CD", name: "Congo, Democratic Republic of the", dialCode: "+243", flag: "🇨🇩", region: "Africa", priority: 40 },
  { code: "AO", name: "Angola", dialCode: "+244", flag: "🇦🇴", region: "Africa", priority: 40 },
  { code: "ST", name: "São Tomé and Príncipe", dialCode: "+239", flag: "🇸🇹", region: "Africa", priority: 40 },
  { code: "CV", name: "Cape Verde", dialCode: "+238", flag: "🇨🇻", region: "Africa", priority: 40 },
  { code: "GW", name: "Guinea-Bissau", dialCode: "+245", flag: "🇬🇼", region: "Africa", priority: 40 },
  { code: "GN", name: "Guinea", dialCode: "+224", flag: "🇬🇳", region: "Africa", priority: 40 },
  { code: "SL", name: "Sierra Leone", dialCode: "+232", flag: "🇸🇱", region: "Africa", priority: 40 },
  { code: "LR", name: "Liberia", dialCode: "+231", flag: "🇱🇷", region: "Africa", priority: 40 },
  { code: "CI", name: "Côte d'Ivoire", dialCode: "+225", flag: "🇨🇮", region: "Africa", priority: 40 },
  { code: "ML", name: "Mali", dialCode: "+223", flag: "🇲🇱", region: "Africa", priority: 40 },
  { code: "BF", name: "Burkina Faso", dialCode: "+226", flag: "🇧🇫", region: "Africa", priority: 40 },
  { code: "NE", name: "Niger", dialCode: "+227", flag: "🇳🇪", region: "Africa", priority: 40 },
  { code: "SN", name: "Senegal", dialCode: "+221", flag: "🇸🇳", region: "Africa", priority: 40 },
  { code: "GM", name: "Gambia", dialCode: "+220", flag: "🇬🇲", region: "Africa", priority: 40 },
  { code: "BI", name: "Burundi", dialCode: "+257", flag: "🇧🇮", region: "Africa", priority: 40 },
  { code: "DZ", name: "Algeria", dialCode: "+213", flag: "🇩🇿", region: "Africa", priority: 40 },
  { code: "TN", name: "Tunisia", dialCode: "+216", flag: "🇹🇳", region: "Africa", priority: 40 },
  { code: "LY", name: "Libya", dialCode: "+218", flag: "🇱🇾", region: "Africa", priority: 40 },
  { code: "MA", name: "Morocco", dialCode: "+212", flag: "🇲🇦", region: "Africa", priority: 40 },

  // North America
  { code: "MX", name: "Mexico", dialCode: "+52", flag: "🇲🇽", region: "North America", priority: 60 },
  { code: "GT", name: "Guatemala", dialCode: "+502", flag: "🇬🇹", region: "North America", priority: 40 },
  { code: "BZ", name: "Belize", dialCode: "+501", flag: "🇧🇿", region: "North America", priority: 40 },
  { code: "SV", name: "El Salvador", dialCode: "+503", flag: "🇸🇻", region: "North America", priority: 40 },
  { code: "HN", name: "Honduras", dialCode: "+504", flag: "🇭🇳", region: "North America", priority: 40 },
  { code: "NI", name: "Nicaragua", dialCode: "+505", flag: "🇳🇮", region: "North America", priority: 40 },
  { code: "CR", name: "Costa Rica", dialCode: "+506", flag: "🇨🇷", region: "North America", priority: 40 },
  { code: "PA", name: "Panama", dialCode: "+507", flag: "🇵🇦", region: "North America", priority: 40 },
  { code: "CU", name: "Cuba", dialCode: "+53", flag: "🇨🇺", region: "North America", priority: 40 },
  { code: "JM", name: "Jamaica", dialCode: "+1", flag: "🇯🇲", region: "North America", priority: 40 },
  { code: "HT", name: "Haiti", dialCode: "+509", flag: "🇭🇹", region: "North America", priority: 40 },
  { code: "DO", name: "Dominican Republic", dialCode: "+1", flag: "🇩🇴", region: "North America", priority: 40 },
  { code: "PR", name: "Puerto Rico", dialCode: "+1", flag: "🇵🇷", region: "North America", priority: 40 },
  { code: "TT", name: "Trinidad and Tobago", dialCode: "+1", flag: "🇹🇹", region: "North America", priority: 40 },
  { code: "BB", name: "Barbados", dialCode: "+1", flag: "🇧🇧", region: "North America", priority: 40 },
  { code: "AG", name: "Antigua and Barbuda", dialCode: "+1", flag: "🇦🇬", region: "North America", priority: 40 },
  { code: "DM", name: "Dominica", dialCode: "+1", flag: "🇩🇲", region: "North America", priority: 40 },
  { code: "GD", name: "Grenada", dialCode: "+1", flag: "🇬🇩", region: "North America", priority: 40 },
  { code: "KN", name: "Saint Kitts and Nevis", dialCode: "+1", flag: "🇰🇳", region: "North America", priority: 40 },
  { code: "LC", name: "Saint Lucia", dialCode: "+1", flag: "🇱🇨", region: "North America", priority: 40 },
  { code: "VC", name: "Saint Vincent and the Grenadines", dialCode: "+1", flag: "🇻🇨", region: "North America", priority: 40 },

  // South America
  { code: "AR", name: "Argentina", dialCode: "+54", flag: "🇦🇷", region: "South America", priority: 50 },
  { code: "CL", name: "Chile", dialCode: "+56", flag: "🇨🇱", region: "South America", priority: 50 },
  { code: "CO", name: "Colombia", dialCode: "+57", flag: "🇨🇴", region: "South America", priority: 50 },
  { code: "PE", name: "Peru", dialCode: "+51", flag: "🇵🇪", region: "South America", priority: 50 },
  { code: "VE", name: "Venezuela", dialCode: "+58", flag: "🇻🇪", region: "South America", priority: 50 },
  { code: "EC", name: "Ecuador", dialCode: "+593", flag: "🇪🇨", region: "South America", priority: 45 },
  { code: "BO", name: "Bolivia", dialCode: "+591", flag: "🇧🇴", region: "South America", priority: 45 },
  { code: "PY", name: "Paraguay", dialCode: "+595", flag: "🇵🇾", region: "South America", priority: 45 },
  { code: "UY", name: "Uruguay", dialCode: "+598", flag: "🇺🇾", region: "South America", priority: 45 },
  { code: "GY", name: "Guyana", dialCode: "+592", flag: "🇬🇾", region: "South America", priority: 40 },
  { code: "SR", name: "Suriname", dialCode: "+597", flag: "🇸🇷", region: "South America", priority: 40 },

  // Oceania
  { code: "NZ", name: "New Zealand", dialCode: "+64", flag: "🇳🇿", region: "Oceania", priority: 60 },
  { code: "FJ", name: "Fiji", dialCode: "+679", flag: "🇫🇯", region: "Oceania", priority: 40 },
  { code: "PG", name: "Papua New Guinea", dialCode: "+675", flag: "🇵🇬", region: "Oceania", priority: 40 },
  { code: "SB", name: "Solomon Islands", dialCode: "+677", flag: "🇸🇧", region: "Oceania", priority: 40 },
  { code: "VU", name: "Vanuatu", dialCode: "+678", flag: "🇻🇺", region: "Oceania", priority: 40 },
  { code: "NC", name: "New Caledonia", dialCode: "+687", flag: "🇳🇨", region: "Oceania", priority: 40 },
  { code: "PF", name: "French Polynesia", dialCode: "+689", flag: "🇵🇫", region: "Oceania", priority: 40 },
  { code: "WS", name: "Samoa", dialCode: "+685", flag: "🇼🇸", region: "Oceania", priority: 40 },
  { code: "TO", name: "Tonga", dialCode: "+676", flag: "🇹🇴", region: "Oceania", priority: 40 },
  { code: "KI", name: "Kiribati", dialCode: "+686", flag: "🇰🇮", region: "Oceania", priority: 40 },
  { code: "TV", name: "Tuvalu", dialCode: "+688", flag: "🇹🇻", region: "Oceania", priority: 40 },
  { code: "NR", name: "Nauru", dialCode: "+674", flag: "🇳🇷", region: "Oceania", priority: 40 },
  { code: "PW", name: "Palau", dialCode: "+680", flag: "🇵🇼", region: "Oceania", priority: 40 },
  { code: "MH", name: "Marshall Islands", dialCode: "+692", flag: "🇲🇭", region: "Oceania", priority: 40 },
  { code: "FM", name: "Micronesia", dialCode: "+691", flag: "🇫🇲", region: "Oceania", priority: 40 },
];

// Helper functions
export const getCountryCodesByRegion = (region: string): CountryCode[] => {
  return COUNTRY_CODES.filter(countryCode => countryCode.region === region);
};

export const searchCountryCodes = (query: string): CountryCode[] => {
  const lowercaseQuery = query.toLowerCase();
  return COUNTRY_CODES.filter(countryCode => 
    countryCode.name.toLowerCase().includes(lowercaseQuery) ||
    countryCode.code.toLowerCase().includes(lowercaseQuery) ||
    countryCode.dialCode.toLowerCase().includes(lowercaseQuery)
  );
};

export const getCountryCodeByCode = (code: string): CountryCode | undefined => {
  return COUNTRY_CODES.find(countryCode => countryCode.code.toLowerCase() === code.toLowerCase());
};

export const getCountryCodeByDialCode = (dialCode: string): CountryCode | undefined => {
  return COUNTRY_CODES.find(countryCode => countryCode.dialCode === dialCode);
};

export const getCountryCodeByName = (name: string): CountryCode | undefined => {
  return COUNTRY_CODES.find(countryCode => 
    countryCode.name.toLowerCase() === name.toLowerCase()
  );
};

// Get all unique regions
export const getRegions = (): string[] => {
  const regionMap = new Map<string, boolean>();
  COUNTRY_CODES.forEach(countryCode => {
    regionMap.set(countryCode.region, true);
  });
  return Array.from(regionMap.keys()).sort();
};

// Sort country codes by priority (highest first) then alphabetically
export const getSortedCountryCodes = (): CountryCode[] => {
  return [...COUNTRY_CODES].sort((a, b) => {
    if (a.priority !== b.priority) {
      return (b.priority || 0) - (a.priority || 0);
    }
    return a.name.localeCompare(b.name);
  });
};

// Get country codes grouped by region
export const getCountryCodesByRegionGrouped = (): Record<string, CountryCode[]> => {
  const grouped: Record<string, CountryCode[]> = {};
  COUNTRY_CODES.forEach(countryCode => {
    if (!grouped[countryCode.region]) {
      grouped[countryCode.region] = [];
    }
    grouped[countryCode.region].push(countryCode);
  });
  
  // Sort countries within each region by priority then alphabetically
  Object.keys(grouped).forEach(region => {
    grouped[region].sort((a, b) => {
      if (a.priority !== b.priority) {
        return (b.priority || 0) - (a.priority || 0);
      }
      return a.name.localeCompare(b.name);
    });
  });
  
  return grouped;
};

// Get most common country codes (high priority)
export const getMostCommonCountryCodes = (limit: number = 20): CountryCode[] => {
  return getSortedCountryCodes().slice(0, limit);
};
