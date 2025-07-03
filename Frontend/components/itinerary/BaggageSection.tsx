"use client"

import React from 'react';
import { BaggageDetails } from '@/utils/itinerary-data-transformer';

interface BaggageSectionProps {
  baggageAllowance: BaggageDetails;
}

const BaggageSection: React.FC<BaggageSectionProps> = ({ baggageAllowance }) => {
  return (
    <div className="border-t border-gray-300 p-6">
      <h2 className="text-xl font-bold mb-4 text-gray-800">Baggage Information</h2>
      
      <div className="grid md:grid-cols-2 gap-6">
        {/* Checked Baggage */}
        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="font-semibold text-lg mb-3 text-gray-700 flex items-center">
            <span className="mr-2">🧳</span>
            Checked Baggage
          </h3>
          
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600">Allowed Pieces:</span>
              <span className="font-medium">{baggageAllowance.checkedBags}</span>
            </div>
            
            {baggageAllowance.checkedBagAllowance?.pieces && (
              <div className="flex justify-between">
                <span className="text-gray-600">Total Allowance:</span>
                <span className="font-medium">{baggageAllowance.checkedBagAllowance.pieces} pieces</span>
              </div>
            )}
            
            {baggageAllowance.checkedBagAllowance?.weight && (
              <div className="flex justify-between">
                <span className="text-gray-600">Weight Limit:</span>
                <span className="font-medium">
                  {baggageAllowance.checkedBagAllowance.weight.value} {baggageAllowance.checkedBagAllowance.weight.unit}
                </span>
              </div>
            )}
            
            {baggageAllowance.checkedBagAllowance?.description && (
              <div className="mt-3 p-2 bg-blue-50 rounded text-sm text-blue-700">
                <span className="font-medium">Note:</span> {baggageAllowance.checkedBagAllowance.description}
              </div>
            )}
          </div>
        </div>

        {/* Carry-On Baggage */}
        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="font-semibold text-lg mb-3 text-gray-700 flex items-center">
            <span className="mr-2">🎒</span>
            Carry-On Baggage
          </h3>
          
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600">Allowed Pieces:</span>
              <span className="font-medium">{baggageAllowance.carryOnBags}</span>
            </div>
            
            {baggageAllowance.carryOnAllowance?.pieces && (
              <div className="flex justify-between">
                <span className="text-gray-600">Total Allowance:</span>
                <span className="font-medium">{baggageAllowance.carryOnAllowance.pieces} pieces</span>
              </div>
            )}
            
            {baggageAllowance.carryOnAllowance?.weight && (
              <div className="flex justify-between">
                <span className="text-gray-600">Weight Limit:</span>
                <span className="font-medium">
                  {baggageAllowance.carryOnAllowance.weight.value} {baggageAllowance.carryOnAllowance.weight.unit}
                </span>
              </div>
            )}
            
            {baggageAllowance.carryOnAllowance?.description && (
              <div className="mt-3 p-2 bg-blue-50 rounded text-sm text-blue-700">
                <span className="font-medium">Note:</span> {baggageAllowance.carryOnAllowance.description}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* General Baggage Guidelines */}
      <div className="mt-6 p-4 bg-yellow-50 rounded-lg border-l-4 border-yellow-400">
        <h4 className="font-semibold text-gray-800 mb-2">Important Baggage Guidelines</h4>
        <ul className="text-sm text-gray-700 space-y-1">
          <li>• Ensure all baggage complies with airline size and weight restrictions</li>
          <li>• Prohibited items must not be packed in carry-on or checked baggage</li>
          <li>• Additional baggage fees may apply for excess weight or pieces</li>
          <li>• Fragile items should be properly protected and declared</li>
          <li>• Check with the airline for specific restrictions on liquids and electronics</li>
        </ul>
      </div>
    </div>
  );
};

export default BaggageSection;
