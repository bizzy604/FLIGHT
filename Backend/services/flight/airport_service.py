import os
from typing import List, Dict, Optional

from .airport_data_parser import parse_airport_data

class AirportService:
    _airports_data: Optional[List[Dict[str, str]]] = None
    _csv_path: Optional[str] = None

    def __init__(self, csv_file_path: Optional[str] = None) -> None:
        """
        Initializes the AirportService.

        Args:
            csv_file_path (Optional[str]): Absolute path to the airports CSV file.
                                           If None, it defaults to 'airports.csv' in the project root.
        """
        if AirportService._airports_data is None:
            if csv_file_path:
                AirportService._csv_path = csv_file_path
            else:
                # Default path: FLIGHT/airports.csv
                # Assumes this service file is in FLIGHT/Backend/services/flight/
                current_script_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.abspath(os.path.join(current_script_dir, '..', '..', '..'))
                AirportService._csv_path = os.path.join(project_root, 'airports.csv')
            
            self._load_data()

    def _load_data(self) -> None:
        """Loads airport data from the CSV file."""
        if AirportService._csv_path and os.path.exists(AirportService._csv_path):
            AirportService._airports_data = parse_airport_data(AirportService._csv_path)
            if AirportService._airports_data:
                print(f"Successfully loaded {len(AirportService._airports_data)} airports from {AirportService._csv_path}")
            else:
                print(f"Warning: No airport data loaded from {AirportService._csv_path}. The file might be empty or improperly formatted.")
        else:
            # If the CSV file is not found, _airports_data remains as it was (e.g., None if not yet loaded).
            # This allows search_airports to correctly print "Error: Airport data is not loaded."
            # when data loading fails and _airports_data was initially None.
            print(f"Error: Airport CSV file not found at {AirportService._csv_path}. Airport search will not work.")

    def search_airports(self, query: str, search_by: str = 'city') -> List[Dict[str, str]]:
        """
        Searches for airports based on a query string.

        Args:
            query (str): The search term (e.g., city name or airport name).
            search_by (str): The field to search by ('city' or 'airport_name'). Defaults to 'city'.

        Returns:
            List[Dict[str, str]]: A list of matching airports.
        """
        if AirportService._airports_data is None:
            # Attempt to load data if not already loaded (e.g., if init failed silently)
            self._load_data()
            if AirportService._airports_data is None: # Still None after trying to load
                 print("Error: Airport data is not loaded. Cannot perform search.")
                 return []
        
        if not query or not AirportService._airports_data:
            return []

        query = query.lower().strip()
        results: List[Dict[str, str]] = []

        field_map = {
            'city': 'city',
            'airport_name': 'airport_name'
        }

        search_field = field_map.get(search_by)
        if not search_field:
            print(f"Warning: Invalid search_by parameter '{search_by}'. Defaulting to 'city'.")
            search_field = 'city'

        for airport in AirportService._airports_data:
            value_to_check = airport.get(search_field)
            if value_to_check and query in value_to_check.lower():
                results.append({
                    'iata': airport.get('iata_code'),
                    'name': airport.get('airport_name'),
                    'city': airport.get('city'),
                    'country': airport.get('country')
                })
        return results

# Example Usage (for testing purposes)
if __name__ == '__main__':
    # This will use the default path resolution
    service = AirportService()

    # Test search by city
    city_query = "London"
    print(f"\nSearching for airports in city: '{city_query}'")
    city_results = service.search_airports(query=city_query, search_by='city')
    if city_results:
        for airport in city_results[:5]: # Print first 5 results
            print(airport)
    else:
        print(f"No airports found for city '{city_query}'.")

    # Test search by airport name
    name_query = "Heathrow"
    print(f"\nSearching for airports with name containing: '{name_query}'")
    name_results = service.search_airports(query=name_query, search_by='airport_name')
    if name_results:
        for airport in name_results[:5]: # Print first 5 results
            print(airport)
    else:
        print(f"No airports found with name containing '{name_query}'.")

    # Test with a non-existent city
    non_existent_city_query = "Atlantis"
    print(f"\nSearching for airports in city: '{non_existent_city_query}'")
    non_existent_results = service.search_airports(query=non_existent_city_query, search_by='city')
    if not non_existent_results:
        print(f"Correctly found no airports for city '{non_existent_city_query}'.")

    # Test with empty query
    empty_query = ""
    print(f"\nSearching with empty query: '{empty_query}'")
    empty_results = service.search_airports(query=empty_query)
    if not empty_results:
        print("Correctly returned no results for empty query.")

    # Test with a different CSV path (if you have one for testing)
    # custom_csv_path = "/path/to/your/custom_airports.csv"
    # if os.path.exists(custom_csv_path):
    #     print(f"\nTesting with custom CSV: {custom_csv_path}")
    #     AirportService._airports_data = None # Reset class variable to force reload
    #     custom_service = AirportService(csv_file_path=custom_csv_path)
    #     custom_results = custom_service.search_airports(query="Paris", search_by='city')
    #     for airport in custom_results[:5]:
    #         print(airport)
    # else:
    #     print(f"\nSkipping custom CSV test, file not found: {custom_csv_path}")