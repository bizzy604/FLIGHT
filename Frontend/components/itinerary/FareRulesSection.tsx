"use client"

import React from 'react';
import { PassengerFareRules, FareRule } from '@/utils/itinerary-data-transformer';

interface FareRulesSectionProps {
  fareRules: PassengerFareRules[];
}

const FareRulesSection: React.FC<FareRulesSectionProps> = ({ fareRules }) => {
  if (!fareRules || fareRules.length === 0) {
    return (
      <div className="border-t border-gray-300 p-6">
        <h2 className="text-xl font-bold mb-4 text-gray-800">Fare Rules</h2>
        <div className="bg-gray-50 p-4 rounded-lg text-center text-gray-600">
          No specific fare rules available for this booking.
        </div>
      </div>
    );
  }

  const getRuleIcon = (type: string) => {
    return type === 'Cancel' ? '❌' : '🔄';
  };

  const getRuleColor = (allowed: boolean) => {
    return allowed ? 'text-green-600' : 'text-red-600';
  };

  const formatAmount = (amount: number, currency: string) => {
    if (amount === 0) return 'Free';
    return `${amount} ${currency}`;
  };

  const getInterpretation = (rule: FareRule) => {
    if (rule.type === 'Cancel') {
      if (rule.allowed) {
        return rule.minAmount === 0 && rule.maxAmount === 0 
          ? 'Cancellation is allowed without penalty'
          : `Cancellation allowed with penalty fees`;
      } else {
        return 'Cancellation is not permitted for this fare';
      }
    } else {
      if (rule.allowed) {
        return rule.minAmount === 0 && rule.maxAmount === 0 
          ? 'Changes are allowed without penalty'
          : `Changes allowed with penalty fees`;
      } else {
        return 'Changes are not permitted for this fare';
      }
    }
  };

  return (
    <div className="border-t border-gray-300 p-6">
      <h2 className="text-xl font-bold mb-4 text-gray-800">Fare Rules & Penalties</h2>
      
      <div className="space-y-6">
        {fareRules.map((passengerRules, index) => (
          <div key={index} className="bg-gray-50 p-4 rounded-lg">
            <h3 className="font-semibold text-lg mb-3 text-gray-700">
              {passengerRules.passengerType === 'ADT' ? 'Adult' : 
               passengerRules.passengerType === 'CHD' ? 'Child' : 
               passengerRules.passengerType === 'INF' ? 'Infant' : 
               passengerRules.passengerType} Passenger Rules
            </h3>
            
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-300">
                    <th className="text-left py-2 px-3 font-medium text-gray-700">Rule Type</th>
                    <th className="text-left py-2 px-3 font-medium text-gray-700">Timing</th>
                    <th className="text-left py-2 px-3 font-medium text-gray-700">Min Fee</th>
                    <th className="text-left py-2 px-3 font-medium text-gray-700">Max Fee</th>
                    <th className="text-left py-2 px-3 font-medium text-gray-700">Status</th>
                    <th className="text-left py-2 px-3 font-medium text-gray-700">Interpretation</th>
                  </tr>
                </thead>
                <tbody>
                  {passengerRules.rules.map((rule, ruleIndex) => (
                    <tr key={ruleIndex} className="border-b border-gray-200">
                      <td className="py-2 px-3">
                        <span className="flex items-center">
                          <span className="mr-2">{getRuleIcon(rule.type)}</span>
                          {rule.type}
                        </span>
                      </td>
                      <td className="py-2 px-3 text-gray-600">
                        {rule.application}
                      </td>
                      <td className="py-2 px-3 font-medium">
                        {formatAmount(rule.minAmount, rule.currency)}
                      </td>
                      <td className="py-2 px-3 font-medium">
                        {formatAmount(rule.maxAmount, rule.currency)}
                      </td>
                      <td className="py-2 px-3">
                        <span className={`font-medium ${getRuleColor(rule.allowed)}`}>
                          {rule.allowed ? 'Allowed' : 'Not Allowed'}
                        </span>
                      </td>
                      <td className="py-2 px-3 text-gray-600 text-xs">
                        {getInterpretation(rule)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </div>

      {/* General Fare Rules Information */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg border-l-4 border-blue-400">
        <h4 className="font-semibold text-gray-800 mb-2">Important Fare Rules Information</h4>
        <ul className="text-sm text-gray-700 space-y-1">
          <li>• Fare rules vary by passenger type and ticket conditions</li>
          <li>• Penalty fees are subject to change based on timing and circumstances</li>
          <li>• Some fares may be non-refundable or non-changeable</li>
          <li>• Additional airline fees may apply beyond the penalties shown</li>
          <li>• Contact the airline or travel agent for specific rule clarifications</li>
          <li>• Rules apply per passenger and may differ for group bookings</li>
        </ul>
      </div>
    </div>
  );
};

export default FareRulesSection;
