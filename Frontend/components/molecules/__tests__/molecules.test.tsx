/**
 * Test suite for atomic design molecules
 * These tests ensure our refactored components maintain their functionality
 */

import { render, screen, fireEvent } from '@testing-library/react'
import { PriceDisplay } from '../price-display'
import { FlightRouteInfo } from '../flight-route-info'
import { PassengerSelector } from '../passenger-selector'
import type { PriceBreakdown } from '@/types/flight-api'

// Mock data for testing
const mockPriceBreakdown: PriceBreakdown = {
  baseFare: 500,
  taxes: 100,
  fees: 50,
  totalPrice: 650,
  currency: 'USD',
}

const mockPassengers = {
  adults: 1,
  children: 0,
  infants: 0,
}

describe('Atomic Design Molecules', () => {
  describe('PriceDisplay', () => {
    it('should render price breakdown correctly', () => {
      render(<PriceDisplay priceBreakdown={mockPriceBreakdown} />)
      
      expect(screen.getByText('Base fare')).toBeInTheDocument()
      expect(screen.getByText('500 USD')).toBeInTheDocument()
      expect(screen.getByText('Total price')).toBeInTheDocument()
      expect(screen.getByText('650 USD')).toBeInTheDocument()
    })

    it('should render compact mode correctly', () => {
      render(<PriceDisplay priceBreakdown={mockPriceBreakdown} compact />)
      
      expect(screen.getByText('Base fare')).toBeInTheDocument()
      expect(screen.getByText('Total')).toBeInTheDocument()
    })
  })

  describe('FlightRouteInfo', () => {
    it('should render flight route information', () => {
      render(
        <FlightRouteInfo
          origin="New York"
          originCode="JFK"
          destination="Los Angeles"
          destinationCode="LAX"
          departDate="2023-12-25"
          adults={1}
          children={0}
          infants={0}
          price={650}
          currency="USD"
        />
      )
      
      expect(screen.getAllByText(/New York \(JFK\) to Los Angeles \(LAX\)/).length).toBeGreaterThan(0)
      expect(screen.getByText('Flight Details & Booking')).toBeInTheDocument()
    })

    it('should render compact mode correctly', () => {
      render(
        <FlightRouteInfo
          origin="New York"
          originCode="JFK" 
          destination="Los Angeles"
          destinationCode="LAX"
          departDate="2023-12-25"
          adults={2}
          children={1}
          infants={0}
          compact
        />
      )
      
      expect(screen.getByText('JFK')).toBeInTheDocument()
      expect(screen.getByText('LAX')).toBeInTheDocument()
      expect(screen.getByText('3p')).toBeInTheDocument()
    })
  })

  describe('PassengerSelector', () => {
    it('should render passenger selector', () => {
      const mockOnChange = jest.fn()
      
      render(
        <PassengerSelector 
          passengers={mockPassengers}
          onPassengersChange={mockOnChange}
        />
      )
      
      expect(screen.getByText('1 Passenger')).toBeInTheDocument()
    })

    it('should show plural passengers when more than 1', () => {
      const mockOnChange = jest.fn()
      const multiplePassengers = { adults: 2, children: 1, infants: 0 }
      
      render(
        <PassengerSelector 
          passengers={multiplePassengers}
          onPassengersChange={mockOnChange}
        />
      )
      
      expect(screen.getByText('3 Passengers')).toBeInTheDocument()
    })
  })

  describe('Component Integration', () => {
    it('should integrate properly within atomic design structure', async () => {
      // Test that new atomic design components work
      const molecules = await import('../index')
      
      expect(molecules.PriceDisplay).toBeDefined()
      expect(molecules.FlightRouteInfo).toBeDefined() 
      expect(molecules.PassengerSelector).toBeDefined()
    })
  })
})