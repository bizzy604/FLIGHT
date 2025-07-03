'use client';

import { useState } from 'react';

export default function TestPostmanPage() {
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const testPostmanRequest = async () => {
    setLoading(true);
    setResult(null);

    try {
      const response = await fetch('http://localhost:5000/api/verteil/air-shopping-test-postman', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({})
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      setResult({ error: error.message });
    } finally {
      setLoading(false);
    }
  };

  const testRegularRequest = async () => {
    setLoading(true);
    setResult(null);

    try {
      const response = await fetch('http://localhost:5000/api/verteil/air-shopping-test-regular', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({})
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      setResult({ error: error.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-8">
      <h1 className="text-2xl font-bold mb-6">Test Postman Request</h1>
      
      <div className="space-y-4">
        <p className="text-gray-600">
          This will test the exact same request that works in Postman:
        </p>
        <ul className="list-disc list-inside text-sm text-gray-500 space-y-1">
          <li>Round-trip: NBO → CDG → NBO</li>
          <li>Business class (C)</li>
          <li>Dates: 2025-07-20 to 2025-07-29</li>
          <li>Same headers as Postman</li>
          <li>No ThirdpartyId header</li>
        </ul>
        
        <div className="space-x-4">
          <button
            onClick={testPostmanRequest}
            disabled={loading}
            className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white px-6 py-2 rounded"
          >
            {loading ? 'Testing...' : 'Test Postman Request (Direct)'}
          </button>

          <button
            onClick={testRegularRequest}
            disabled={loading}
            className="bg-green-500 hover:bg-green-600 disabled:bg-gray-400 text-white px-6 py-2 rounded"
          >
            {loading ? 'Testing...' : 'Test Regular Air-Shopping (Updated)'}
          </button>
        </div>
        
        {result && (
          <div className="mt-6">
            <h2 className="text-lg font-semibold mb-2">Result:</h2>
            <div className={`p-3 rounded mb-3 ${result.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
              <strong>{result.success ? '✅ SUCCESS' : '❌ FAILED'}:</strong> {result.message || 'No message'}
            </div>
            <pre className="bg-gray-100 p-4 rounded overflow-auto text-sm max-h-96">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
