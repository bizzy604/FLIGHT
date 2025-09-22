/**
 * Test suite for SeatSelection component
 * Tests the no-seats-available functionality and other key features
 */

import { render, screen } from '@testing-library/react'
import { SeatSelection } from '../seat-selection'

// Mock the logger to avoid console output during tests
jest.mock('@/utils/logger', () => ({
  logger: {
    info: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
  },
}))

// Mock the API client
jest.mock('@/utils/api-client', () => ({
  api: {
    getSeatAvailability: jest.fn(),
  },
}))

// Mock the cache manager
jest.mock('@/utils/seat-service-cache-manager', () => ({
  seatServiceCache: {
    getSeatAvailability: jest.fn(),
  },
}))

// Mock the simple cache manager
jest.mock('@/utils/simple-cache-manager', () => ({
  simpleCacheManager: {
    getSeatAvailability: jest.fn(),
  },
}))

const mockPassengers = [
  { objectKey: 'p1', name: 'John Doe', type: 'adult' },
  { objectKey: 'p2', name: 'Jane Doe', type: 'adult' },
]

const mockOnSeatChange = jest.fn()

describe('SeatSelection Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('No Seats Available State', () => {
    it('should show no seats available message when no seat data is provided', () => {
      render(
        <SeatSelection
          flightPriceResponse={null}
          flightType="outbound"
          selectedSeats={[]}
          onSeatChange={mockOnSeatChange}
          passengers={mockPassengers}
          preloadedData={null}
          loading={false}
          error={null}
        />
      )

      expect(screen.getByText('No Seats Available')).toBeInTheDocument()
      expect(screen.getByText(/seat selection is not available for this flight/)).toBeInTheDocument()
      expect(screen.getByText(/seats will be assigned by the airline/)).toBeInTheDocument()
    })

    it('should show no seats available message when seats array is empty', () => {
      const emptySeatData = {
        flights: [
          {
            cabin: [
              {
                seatDisplay: {
                  columns: [
                    { value: "A", position: "left" },
                    { value: "B", position: "center" },
                    { value: "C", position: "right" }
                  ],
                  rows: { first: 1, last: 10, upperDeckInd: false }
                }
              }
            ]
          }
        ],
        dataLists: {
          seatList: {
            seats: [] // Empty seats array
          }
        }
      }

      render(
        <SeatSelection
          flightPriceResponse={null}
          flightType="outbound"
          selectedSeats={[]}
          onSeatChange={mockOnSeatChange}
          passengers={mockPassengers}
          preloadedData={emptySeatData}
          loading={false}
          error={null}
        />
      )

      expect(screen.getByText('No Seats Available')).toBeInTheDocument()
    })
  })

  describe('Component Structure', () => {
    it('should render with correct flight type in title', () => {
      render(
        <SeatSelection
          flightPriceResponse={null}
          flightType="return"
          selectedSeats={[]}
          onSeatChange={mockOnSeatChange}
          passengers={mockPassengers}
          preloadedData={null}
          loading={false}
          error={null}
        />
      )

      expect(screen.getByText('Seat Selection - return')).toBeInTheDocument()
    })

    it('should render with custom className', () => {
      const { container } = render(
        <SeatSelection
          flightPriceResponse={null}
          flightType="outbound"
          selectedSeats={[]}
          onSeatChange={mockOnSeatChange}
          passengers={mockPassengers}
          preloadedData={null}
          loading={false}
          error={null}
          className="custom-class"
        />
      )

      expect(container.firstChild).toHaveClass('custom-class')
    })
  })
})
