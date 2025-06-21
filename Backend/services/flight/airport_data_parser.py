import csv
import os

def parse_airport_data(csv_file_path):
    """
    Parses the airport data from a CSV file.

    Args:
        csv_file_path (str): The absolute path to the airports CSV file.

    Returns:
        list: A list of dictionaries, where each dictionary contains
              'iata_code', 'airport_name', 'city', and 'country' for an airport.
              Returns an empty list if the file is not found or an error occurs.
    """
    airports_data = []
    required_columns = ['code', 'name', 'city', 'country']

    if not os.path.isabs(csv_file_path):
        print(f"Error: Provided path '{csv_file_path}' is not an absolute path.")
        return airports_data

    try:
        with open(csv_file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            # Verify all required columns are in the header
            header = reader.fieldnames
            if not header:
                print(f"Error: CSV file '{csv_file_path}' is empty or has no header.")
                return airports_data
            
            missing_columns = [col for col in required_columns if col not in header]
            if missing_columns:
                print(f"Error: Missing required columns in CSV: {', '.join(missing_columns)}")
                return airports_data

            for row in reader:
                # Skip rows where essential data might be missing, though DictReader handles missing values as None or empty string
                # For this task, we assume 'code' (IATA) is crucial.
                if not row.get('code'):
                    continue
                
                airport_info = {
                    'iata_code': row.get('code'),
                    'airport_name': row.get('name'),
                    'city': row.get('city'),
                    'country': row.get('country')
                }
                airports_data.append(airport_info)
    except FileNotFoundError:
        print(f"Error: The file '{csv_file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred while parsing '{csv_file_path}': {e}")
    
    return airports_data

if __name__ == '__main__':
    # Determine the absolute path to airports.csv relative to this script's project structure
    # Assuming this script is in FLIGHT/Backend/services/flight/
    # and airports.csv is in FLIGHT/
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_script_dir, '..', '..', '..'))
    default_csv_path = os.path.join(project_root, 'airports.csv')

    print(f"Attempting to parse: {default_csv_path}")
    
    # Check if the default CSV path exists
    if not os.path.exists(default_csv_path):
        print(f"Error: The default CSV file was not found at '{default_csv_path}'.")
        print("Please ensure 'airports.csv' is in the project root directory 'FLIGHT'.")
    else:
        parsed_data = parse_airport_data(default_csv_path)
        if parsed_data:
            print(f"Successfully parsed {len(parsed_data)} airports.")
            print("First 5 entries:")
            for i, airport in enumerate(parsed_data[:5]):
                print(airport)
        else:
            print("No data parsed or an error occurred.")