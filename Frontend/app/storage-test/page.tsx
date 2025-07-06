'use client'

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { runStorageTests, quickStorageTest } from '@/utils/storage-test';
import { setupRobustStorage } from '@/utils/storage-integration-example';
import { flightStorageManager } from '@/utils/flight-storage-manager';

interface TestResult {
  testName: string;
  passed: boolean;
  error?: string;
  details?: any;
}

export default function StorageTestPage() {
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [quickTestResult, setQuickTestResult] = useState<boolean | null>(null);
  const [storageStats, setStorageStats] = useState<any>(null);

  useEffect(() => {
    // Setup storage on page load
    setupRobustStorage();
    updateStorageStats();
  }, []);

  const updateStorageStats = () => {
    const stats = flightStorageManager.getStorageStats();
    setStorageStats(stats);
  };

  const runQuickTest = async () => {
    setIsRunning(true);
    try {
      console.log('🚀 Running quick storage test...');
      const result = await quickStorageTest();
      setQuickTestResult(result);
      updateStorageStats();
      console.log('Quick test result:', result);
    } catch (error) {
      console.error('Quick test error:', error);
      setQuickTestResult(false);
    } finally {
      setIsRunning(false);
    }
  };

  const runFullTests = async () => {
    setIsRunning(true);
    try {
      console.log('🧪 Running full storage test suite...');
      const results = await runStorageTests();
      setTestResults(results);
      updateStorageStats();
      console.log('Full test results:', results);
    } catch (error) {
      console.error('Full test error:', error);
    } finally {
      setIsRunning(false);
    }
  };

  const runHealthCheck = async () => {
    try {
      const health = await flightStorageManager.healthCheck();
      console.log('Storage health check:', health);
      updateStorageStats();
    } catch (error) {
      console.error('Health check error:', error);
    }
  };

  const clearAllData = async () => {
    try {
      await flightStorageManager.clearAllFlightData();
      console.log('All flight data cleared');
      updateStorageStats();
    } catch (error) {
      console.error('Clear data error:', error);
    }
  };

  const passedTests = testResults.filter(r => r.passed).length;
  const totalTests = testResults.length;

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Storage System Test Suite</h1>
        <p className="text-muted-foreground">
          Validate the robust storage manager and ensure corruption issues are resolved
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <Button 
          onClick={runQuickTest} 
          disabled={isRunning}
          className="h-12"
        >
          {isRunning ? 'Running...' : 'Quick Test'}
        </Button>
        
        <Button 
          onClick={runFullTests} 
          disabled={isRunning}
          variant="outline"
          className="h-12"
        >
          {isRunning ? 'Running...' : 'Full Test Suite'}
        </Button>
        
        <Button 
          onClick={runHealthCheck} 
          variant="outline"
          className="h-12"
        >
          Health Check
        </Button>
        
        <Button 
          onClick={clearAllData} 
          variant="destructive"
          className="h-12"
        >
          Clear All Data
        </Button>
      </div>

      {/* Quick Test Result */}
      {quickTestResult !== null && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              Quick Test Result
              <Badge variant={quickTestResult ? "default" : "destructive"}>
                {quickTestResult ? "PASSED" : "FAILED"}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className={quickTestResult ? "text-green-600" : "text-red-600"}>
              {quickTestResult 
                ? "✅ Storage system is working correctly!" 
                : "❌ Storage system has issues that need attention."
              }
            </p>
          </CardContent>
        </Card>
      )}

      {/* Storage Statistics */}
      {storageStats && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Storage Statistics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="font-semibold mb-2">Session Storage</h4>
                <p>Used: {Math.round(storageStats.sessionStorage.used / 1024)}KB</p>
                <p>Items: {storageStats.sessionStorage.itemCount}</p>
                <p>Available: {Math.round(storageStats.sessionStorage.available / 1024)}KB</p>
              </div>
              <div>
                <h4 className="font-semibold mb-2">Local Storage</h4>
                <p>Used: {Math.round(storageStats.localStorage.used / 1024)}KB</p>
                <p>Items: {storageStats.localStorage.itemCount}</p>
                <p>Available: {Math.round(storageStats.localStorage.available / 1024)}KB</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Full Test Results */}
      {testResults.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              Full Test Suite Results
              <Badge variant={passedTests === totalTests ? "default" : "destructive"}>
                {passedTests}/{totalTests} PASSED
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {testResults.map((result, index) => (
                <div 
                  key={index}
                  className={`p-4 rounded-lg border ${
                    result.passed 
                      ? 'border-green-200 bg-green-50' 
                      : 'border-red-200 bg-red-50'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className={result.passed ? 'text-green-600' : 'text-red-600'}>
                      {result.passed ? '✅' : '❌'}
                    </span>
                    <h4 className="font-semibold">{result.testName}</h4>
                  </div>
                  
                  {result.error && (
                    <p className="text-red-600 text-sm mb-2">
                      Error: {result.error}
                    </p>
                  )}
                  
                  {result.details && (
                    <div className="text-sm text-muted-foreground">
                      <pre className="bg-gray-100 p-2 rounded text-xs overflow-auto">
                        {JSON.stringify(result.details, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              ))}
            </div>
            
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h4 className="font-semibold mb-2">Summary</h4>
              <p>
                <span className="text-green-600">Passed: {passedTests}</span> | 
                <span className="text-red-600 ml-2">Failed: {totalTests - passedTests}</span> | 
                <span className="ml-2">Success Rate: {Math.round((passedTests / totalTests) * 100)}%</span>
              </p>
              
              {passedTests === totalTests ? (
                <p className="text-green-600 font-semibold mt-2">
                  🎉 All tests passed! Storage system is working correctly.
                </p>
              ) : (
                <p className="text-red-600 font-semibold mt-2">
                  ⚠️ Some tests failed. Please review the errors above.
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Instructions */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>How to Use</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <p><strong>Quick Test:</strong> Runs a basic validation of storage functionality</p>
            <p><strong>Full Test Suite:</strong> Comprehensive testing including corruption detection, migration, and concurrent access</p>
            <p><strong>Health Check:</strong> Checks the current state of all storage systems</p>
            <p><strong>Clear All Data:</strong> Removes all flight-related data from storage</p>
          </div>
          
          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
            <p className="text-blue-800 text-sm">
              💡 <strong>Tip:</strong> Open browser console (F12) to see detailed logs during testing
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
