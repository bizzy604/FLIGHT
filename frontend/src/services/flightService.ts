import { SearchFormData } from '../components/SearchForm';
import { Flight } from '../components/FlightResults';

const API_BASE_URL = 'http://localhost:5000/api';

export const searchFlights = async (searchData: SearchFormData): Promise<Flight[]> => {
  try {
    const response = await fetch(`${API_BASE_URL}/flights/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(searchData),
    });

    if (!response.ok) {
      throw new Error(`Error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error searching flights:', error);
    throw error;
  }
};

export const bookFlight = async (flightId: string, passengerDetails: any): Promise<any> => {
  try {
    const response = await fetch(`${API_BASE_URL}/flights/book`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        flightId,
        passengerDetails,
      }),
    });

    if (!response.ok) {
      throw new Error(`Error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error booking flight:', error);
    throw error;
  }
};
