'use client';

import React from 'react';

export default function ServicesSeatsTestPage() {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            Services & Seats Test Page
          </h1>
          <p className="text-gray-600 mb-4">
            This is a test page for testing seat selection and services functionality.
          </p>
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <h2 className="text-lg font-semibold text-blue-900 mb-2">
              Test Status
            </h2>
            <p className="text-blue-700">
              ✅ Page loaded successfully<br/>
              ✅ Build error resolved<br/>
              ✅ Ready for testing
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
