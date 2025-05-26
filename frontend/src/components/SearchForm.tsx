"use client";

import { useState } from 'react';
import { useForm } from 'react-hook-form';

type SearchFormProps = {
  onSearch: (data: SearchFormData) => void;
  isLoading: boolean;
};

export type SearchFormData = {
  origin: string;
  destination: string;
  departureDate: string;
  returnDate?: string;
  adults: number;
  children: number;
  cabinClass: string;
  tripType: 'oneway' | 'roundtrip';
};

const SearchForm = ({ onSearch, isLoading }: SearchFormProps) => {
  const { register, handleSubmit, watch, formState: { errors } } = useForm<SearchFormData>({
    defaultValues: {
      origin: '',
      destination: '',
      departureDate: new Date().toISOString().split('T')[0],
      returnDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      adults: 1,
      children: 0,
      cabinClass: 'ECONOMY',
      tripType: 'roundtrip',
    },
  });

  const tripType = watch('tripType');
  const isRoundTrip = tripType === 'roundtrip';

  return (
    <form onSubmit={handleSubmit(onSearch)} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Origin */}
        <div>
          <label htmlFor="origin" className="block text-sm font-medium text-gray-700 mb-1">
            From
          </label>
          <input
            id="origin"
            type="text"
            placeholder="Airport code or city"
            {...register('origin', { required: 'Origin is required' })}
            className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border"
          />
          {errors.origin && <p className="text-red-500 text-xs mt-1">{errors.origin.message}</p>}
        </div>

        {/* Destination */}
        <div>
          <label htmlFor="destination" className="block text-sm font-medium text-gray-700 mb-1">
            To
          </label>
          <input
            id="destination"
            type="text"
            placeholder="Airport code or city"
            {...register('destination', { required: 'Destination is required' })}
            className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border"
          />
          {errors.destination && <p className="text-red-500 text-xs mt-1">{errors.destination.message}</p>}
        </div>
      </div>

      {/* Trip Type */}
      <div className="flex space-x-4 mb-4">
        <label className="inline-flex items-center">
          <input
            type="radio"
            value="roundtrip"
            {...register('tripType')}
            className="form-radio h-4 w-4 text-blue-600"
          />
          <span className="ml-2 text-gray-700">Round Trip</span>
        </label>
        <label className="inline-flex items-center">
          <input
            type="radio"
            value="oneway"
            {...register('tripType')}
            className="form-radio h-4 w-4 text-blue-600"
          />
          <span className="ml-2 text-gray-700">One Way</span>
        </label>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Departure Date */}
        <div>
          <label htmlFor="departureDate" className="block text-sm font-medium text-gray-700 mb-1">
            Departure Date
          </label>
          <input
            id="departureDate"
            type="date"
            {...register('departureDate', { required: 'Departure date is required' })}
            className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border"
          />
          {errors.departureDate && <p className="text-red-500 text-xs mt-1">{errors.departureDate.message}</p>}
        </div>

        {/* Return Date (only shown for round trips) */}
        {isRoundTrip && (
          <div>
            <label htmlFor="returnDate" className="block text-sm font-medium text-gray-700 mb-1">
              Return Date
            </label>
            <input
              id="returnDate"
              type="date"
              {...register('returnDate', { required: isRoundTrip ? 'Return date is required' : false })}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border"
            />
            {errors.returnDate && <p className="text-red-500 text-xs mt-1">{errors.returnDate.message}</p>}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Number of Adults */}
        <div>
          <label htmlFor="adults" className="block text-sm font-medium text-gray-700 mb-1">
            Adults
          </label>
          <select
            id="adults"
            {...register('adults')}
            className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border"
          >
            {[1, 2, 3, 4, 5, 6, 7, 8, 9].map(num => (
              <option key={num} value={num}>{num}</option>
            ))}
          </select>
        </div>

        {/* Number of Children */}
        <div>
          <label htmlFor="children" className="block text-sm font-medium text-gray-700 mb-1">
            Children
          </label>
          <select
            id="children"
            {...register('children')}
            className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border"
          >
            {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map(num => (
              <option key={num} value={num}>{num}</option>
            ))}
          </select>
        </div>

        {/* Cabin Class */}
        <div>
          <label htmlFor="cabinClass" className="block text-sm font-medium text-gray-700 mb-1">
            Cabin Class
          </label>
          <select
            id="cabinClass"
            {...register('cabinClass')}
            className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border"
          >
            <option value="ECONOMY">Economy</option>
            <option value="PREMIUM_ECONOMY">Premium Economy</option>
            <option value="BUSINESS">Business</option>
            <option value="FIRST">First Class</option>
          </select>
        </div>
      </div>

      <div className="pt-4">
        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors duration-200"
        >
          {isLoading ? 'Searching...' : 'Search Flights'}
        </button>
      </div>
    </form>
  );
};

export default SearchForm;
