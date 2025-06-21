'use client';

import { useState } from 'react';
import axios from 'axios';

export default function TestConnection() {
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const testBackendConnection = async () => {
    setIsLoading(true);
    setError(null);
    setResponse(null);

    try {
      const result = await axios.post(
        `${process.env.NEXT_PUBLIC_API_BASE_URL || 'https://rea-travel-backend.onrender.com'}/api/verteil/air-shopping`,
        {
          tripType: 'ONE_WAY',
          odSegments: [
            {
              origin: 'JFK',
              destination: 'LAX',
              departureDate: '2025-07-15'
            }
          ],
          numAdults: 1,
          numChildren: 0,
          numInfants: 0,
          cabinPreference: 'ECONOMY',
          directOnly: false
        },
        {
          withCredentials: true,
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          }
        }
      );
      
      setResponse(result.data);
    } catch (err: any) {
      console.error('Test connection error:', err);
      setError(err.message);
      if (err.response) {
        setError(`Status: ${err.response.status} - ${JSON.stringify(err.response.data)}`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Backend Connection Test</h1>
          <p className="text-gray-600">
            Test the connection between frontend and backend
          </p>
        </div>

        <div className="bg-white shadow overflow-hidden sm:rounded-lg p-6">
          <div className="mb-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Test Backend Connection</h2>
            <p className="text-sm text-gray-500 mb-4">
              Click the button below to test the connection to the backend API.
            </p>
            <button
              onClick={testBackendConnection}
              disabled={isLoading}
              className={`px-4 py-2 rounded-md text-white font-medium ${
                isLoading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {isLoading ? 'Testing...' : 'Test Connection'}
            </button>
          </div>

          {error && (
            <div className="mt-6 p-4 bg-red-50 border-l-4 border-red-400">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg
                    className="h-5 w-5 text-red-400"
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              </div>
            </div>
          )}

          {response && (
            <div className="mt-6">
              <h3 className="text-lg font-medium text-gray-900 mb-2">Response:</h3>
              <pre className="bg-gray-50 p-4 rounded-md overflow-auto text-sm">
                {JSON.stringify(response, null, 2)}
              </pre>
            </div>
          )}
        </div>

        <div className="mt-8 bg-white shadow overflow-hidden sm:rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Connection Details</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h3 className="text-sm font-medium text-gray-500">Frontend URL</h3>
              <p className="mt-1 text-sm text-gray-900">
                {typeof window !== 'undefined' ? window.location.origin : 'Loading...'}
              </p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500">Backend URL</h3>
              <p className="mt-1 text-sm text-gray-900 break-all">
                {process.env.NEXT_PUBLIC_API_BASE_URL || 'https://rea-travel-backend.onrender.com'}
              </p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500">Environment</h3>
              <p className="mt-1 text-sm text-gray-900">
                {process.env.NODE_ENV || 'development'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
