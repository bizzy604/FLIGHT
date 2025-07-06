"""
Shared airline data including IATA code to name mappings.

This module provides a centralized location for airline code mappings
that can be used across different parts of the application.
"""

# Mapping of IATA airline codes to airline names
# Source: https://www.iata.org/en/publications/directories/code-search/
AIRLINE_NAMES = {
    # Major Airlines
    'AA': 'American Airlines',
    'KQ': 'Kenya Airways',
    'DL': 'Delta Air Lines',
    'UA': 'United Airlines',
    'WN': 'Southwest Airlines',
    'BA': 'British Airways',
    'AF': 'Air France',
    'LH': 'Lufthansa',
    'KL': 'KLM Royal Dutch Airlines',
    'EK': 'Emirates',
    'QR': 'Qatar Airways',
    'SQ': 'Singapore Airlines',
    'CX': 'Cathay Pacific',
    'QF': 'Qantas',
    'EY': 'Etihad Airways',
    'TK': 'Turkish Airlines',
    'NH': 'ANA All Nippon Airways',
    'JL': 'Japan Airlines',
    'CA': 'Air China',
    'CZ': 'China Southern Airlines',
    'MU': 'China Eastern Airlines',
    '6E': 'IndiGo',
    'AI': 'Air India',
    'IX': 'Air India Express',
    'SU': 'Aeroflot',
    'AC': 'Air Canada',
    'LY': 'El Al',
    'SV': 'Saudi Arabian Airlines',
    'ET': 'Ethiopian Airlines',
    'KE': 'Korean Air',
    'OZ': 'Asiana Airlines',
    'TG': 'Thai Airways',
    'VN': 'Vietnam Airlines',
    'GA': 'Garuda Indonesia',
    'MH': 'Malaysia Airlines',
    'PR': 'Philippine Airlines',
    'BR': 'EVA Air',
    'CI': 'China Airlines',
    'NZ': 'Air New Zealand',
    'VA': 'Virgin Australia',
    'FZ': 'flydubai',
    'G9': 'Air Arabia',
    'JQ': 'Jetstar',
    '3U': 'Sichuan Airlines',
    'HU': 'Hainan Airlines',
    'SC': 'Shandong Airlines',
    'FM': 'Shanghai Airlines',
    'MF': 'Xiamen Airlines',
    'KY': 'Kunming Airlines',
    '8L': 'Lucky Air',
    'GS': 'Tianjin Airlines',
    'PN': 'China West Air',
    'G5': 'China Express Airlines',
    'EU': 'Chengdu Airlines',
    'DR': 'Ruili Airlines',
    'UQ': 'Urumqi Air',
    'A6': 'Air Travel',
    'GT': 'Guangxi Beibu Gulf Airlines',
    'QW': 'Qingdao Airlines',
    'LT': 'LongJiang Airlines',
    'GJ': 'Loong Air',
    'RY': 'Jiangxi Air',
    'VD': 'Henan Airlines',
    'DZ': 'Donghai Airlines',
    'GX': 'GX Airlines'
}

def get_airline_name(airline_code: str, log_missing: bool = True) -> str:
    """
    Get airline name from IATA code with fallback to a generic name.
    
    Args:
        airline_code: 2-letter IATA airline code
        log_missing: Whether to log missing airline codes
        
    Returns:
        str: Airline name or generic name if not found
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if not airline_code:
        if log_missing:
            logger.debug("Empty airline code provided")
        return "Unknown Airline"
        
    if not isinstance(airline_code, str):
        airline_code = str(airline_code)
        if log_missing:
            logger.debug(f"Non-string airline code converted to string: {airline_code}")
    
    # Clean and normalize the code
    code = airline_code.strip().upper()
    
    # Return the name if found
    if code in AIRLINE_NAMES:
        return AIRLINE_NAMES[code]
    
    # Log missing airline codes at debug level to avoid cluttering logs
    if log_missing:
        logger.debug(f"Airline code not found in mapping: {code}")
    
    # Return a generic name for missing codes
    return f"Airline {code}"

def get_airline_logo_url(airline_code: str) -> str:
    """
    Return a local URL to the airline's logo based on the IATA code, for use with the frontend's /public/airlines directory.
    """
    code = (airline_code or "").strip().upper()
    if not code:
        return "/airlines/unknown.png"
    return f"/airlines/{code}.svg"
