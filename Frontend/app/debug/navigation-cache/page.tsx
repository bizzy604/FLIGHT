"use client"

import { useState, useEffect } from 'react';
import { navigationCacheManager } from '@/utils/navigation-cache-manager';
import { redisFlightStorage } from '@/utils/redis-flight-storage';

export default function NavigationCacheDebugPage() {
  const [cacheStatus, setCacheStatus] = useState<any>(null);
  const [redisData, setRedisData] = useState<any>(null);
  const [logs, setLogs] = useState<string[]>([]);

  const addLog = (message: string) => {
    setLogs(prev => [...prev, `${new Date().toLocaleTimeString()}: ${message}`]);
  };

  const refreshStatus = async () => {
    try {
      // Get navigation cache status
      const status = navigationCacheManager.getCacheStatus();
      setCacheStatus(status);

      // Get Redis data
      const searchResult = await redisFlightStorage.getFlightSearch();
      const priceResult = await redisFlightStorage.getFlightPrice();
      
      setRedisData({
        search: searchResult,
        price: priceResult
      });

      addLog('Status refreshed');
    } catch (error) {
      addLog(`Error refreshing status: ${error}`);
    }
  };

  const simulateNavigation = (page: 'search' | 'details' | 'payment' | 'confirmation') => {
    navigationCacheManager.updateNavigationState(page, {
      searchParams: page === 'search' ? {
        origin: 'NBO',
        destination: 'LHR',
        departDate: '2025-08-15',
        tripType: 'one-way'
      } : undefined,
      flightId: page === 'details' ? 'test-flight-123' : undefined
    });
    
    addLog(`Simulated navigation to ${page}`);
    refreshStatus();
  };

  const testCacheValidation = async () => {
    try {
      const testParams = {
        origin: 'NBO',
        destination: 'LHR',
        departDate: '2025-08-15',
        tripType: 'one-way',
        adults: '1',
        children: '0',
        infants: '0',
        cabinClass: 'ECONOMY'
      };

      const validation = await navigationCacheManager.validateFlightSearchCache(testParams);
      addLog(`Cache validation result: ${validation.isValid ? 'VALID' : 'INVALID'} - ${validation.reason || 'No reason'}`);
    } catch (error) {
      addLog(`Cache validation error: ${error}`);
    }
  };

  const clearCache = () => {
    navigationCacheManager.clearCache();
    addLog('Cache cleared');
    refreshStatus();
  };

  useEffect(() => {
    refreshStatus();
  }, []);

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <h1 className="text-2xl font-bold mb-6">Navigation Cache Debug</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Controls */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Controls</h2>
          
          <div className="space-y-2">
            <button 
              onClick={() => simulateNavigation('search')}
              className="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Simulate Search Page
            </button>
            <button 
              onClick={() => simulateNavigation('details')}
              className="w-full px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
            >
              Simulate Details Page
            </button>
            <button 
              onClick={() => simulateNavigation('payment')}
              className="w-full px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600"
            >
              Simulate Payment Page
            </button>
            <button 
              onClick={() => simulateNavigation('confirmation')}
              className="w-full px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600"
            >
              Simulate Confirmation Page
            </button>
          </div>

          <div className="space-y-2">
            <button 
              onClick={testCacheValidation}
              className="w-full px-4 py-2 bg-indigo-500 text-white rounded hover:bg-indigo-600"
            >
              Test Cache Validation
            </button>
            <button 
              onClick={clearCache}
              className="w-full px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
            >
              Clear Cache
            </button>
            <button 
              onClick={refreshStatus}
              className="w-full px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
            >
              Refresh Status
            </button>
          </div>
        </div>

        {/* Status Display */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Cache Status</h2>
          
          {cacheStatus && (
            <div className="bg-gray-100 p-4 rounded">
              <pre className="text-sm">
                {JSON.stringify(cacheStatus, null, 2)}
              </pre>
            </div>
          )}

          <h3 className="text-md font-semibold">Redis Data</h3>
          {redisData && (
            <div className="bg-gray-100 p-4 rounded max-h-40 overflow-y-auto">
              <pre className="text-xs">
                {JSON.stringify(redisData, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>

      {/* Logs */}
      <div className="mt-6">
        <h2 className="text-lg font-semibold mb-2">Logs</h2>
        <div className="bg-black text-green-400 p-4 rounded h-40 overflow-y-auto font-mono text-sm">
          {logs.map((log, index) => (
            <div key={index}>{log}</div>
          ))}
        </div>
      </div>

      {/* Instructions */}
      <div className="mt-6 bg-blue-50 p-4 rounded">
        <h3 className="font-semibold mb-2">How to Test Navigation Cache:</h3>
        <ol className="list-decimal list-inside space-y-1 text-sm">
          <li>First, go to the flight search page and perform a search</li>
          <li>Navigate to flight details page</li>
          <li>Use browser back button to return to search</li>
          <li>Check this debug page to see if cache was used</li>
          <li>Look for "⚡ Using cached data" messages in browser console</li>
        </ol>
      </div>
    </div>
  );
}
