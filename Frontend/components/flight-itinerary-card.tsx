"use client"

import Image from "next/image"
import { ArrowRight, Clock, Plane } from "lucide-react"
import { Separator } from "@/components/ui/separator"

// Define a type for a single flight segment, matching your backend output
interface FlightSegment {
  departure_airport: string;
  arrival_airport: string;
  departure_datetime: string;
  arrival_datetime: string;
  airline_code: string;
  airline_name: string;
  airline_logo_url: string | null;
  flight_number: string;
  duration: string;
}

interface FlightItineraryCardProps {
  flightSegments: FlightSegment[];
}

// Helper to calculate total duration from a list of human-readable segment durations
const calculateTotalDuration = (segments: FlightSegment[]): string => {
  let totalMinutes = 0;
  segments.forEach(segment => {
    const durationStr = segment.duration || "";
    const hoursMatch = durationStr.match(/(\d+)\s*h/);
    const minutesMatch = durationStr.match(/(\d+)\s*m/);
    if (hoursMatch) totalMinutes += parseInt(hoursMatch[1]) * 60;
    if (minutesMatch) totalMinutes += parseInt(minutesMatch[1]);
  });
  
  if (totalMinutes === 0) return "N/A";
  
  const hours = Math.floor(totalMinutes / 60);
  const mins = totalMinutes % 60;
  return `${hours}h ${mins}m`;
};

export function FlightItineraryCard({ flightSegments }: FlightItineraryCardProps) {
  if (!flightSegments || flightSegments.length === 0) {
    return <div className="p-4 text-muted-foreground">No flight segments available.</div>;
  }

  const firstSegment = flightSegments[0];
  const lastSegment = flightSegments[flightSegments.length - 1];
  const totalDuration = calculateTotalDuration(flightSegments);
  const stops = flightSegments.length - 1;

  // Format date and time for display
  const formatDateTime = (isoString: string) => {
    const date = new Date(isoString);
    return {
      time: date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false }),
      date: date.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' })
    };
  };

  const departure = formatDateTime(firstSegment.departure_datetime);
  const arrival = formatDateTime(lastSegment.arrival_datetime);

  return (
    <div className="p-3 sm:p-4 md:p-6">
      {/* Overall Itinerary Summary */}
      <div className="flex items-center justify-between mb-4">
        <div className="text-center flex-1">
          <div className="text-lg sm:text-xl md:text-2xl font-bold">{departure.time}</div>
          <div className="text-xs sm:text-sm text-muted-foreground">{firstSegment.departure_airport}</div>
          <div className="text-xs text-muted-foreground hidden sm:block">{departure.date}</div>
        </div>

        <div className="flex flex-col items-center px-2 sm:px-4 flex-1">
          <div className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
            <Clock className="h-3 w-3" />
            <span className="hidden sm:inline">{totalDuration}</span>
            <span className="sm:hidden text-xs">{totalDuration}</span>
          </div>
          <div className="flex w-full items-center">
            <div className="h-px flex-1 bg-border"></div>
            <Plane className="mx-1 sm:mx-2 h-3 w-3 sm:h-4 sm:w-4 text-muted-foreground" />
            <div className="h-px flex-1 bg-border"></div>
          </div>
          <div className="text-xs text-muted-foreground mt-1">
            {stops > 0 ? `${stops} stop${stops > 1 ? 's' : ''}` : 'Direct'}
          </div>
        </div>

        <div className="text-center flex-1">
          <div className="text-lg sm:text-xl md:text-2xl font-bold">{arrival.time}</div>
          <div className="text-xs sm:text-sm text-muted-foreground">{lastSegment.arrival_airport}</div>
          <div className="text-xs text-muted-foreground hidden sm:block">{arrival.date}</div>
        </div>
      </div>

      {/* Mobile Date Display */}
      <div className="flex justify-between text-xs text-muted-foreground mb-4 sm:hidden">
        <span>{departure.date}</span>
        <span>{arrival.date}</span>
      </div>

      <Separator className="my-4" />

      {/* Detailed Segments List */}
      <div className="space-y-3 sm:space-y-4">
        {flightSegments.map((segment, index) => (
          <div key={index} className="flex items-start gap-3 sm:gap-4">
            <Image
              src={segment.airline_logo_url || "/placeholder-logo.svg"}
              alt={segment.airline_name}
              width={28}
              height={28}
              className="rounded-full mt-1 sm:w-8 sm:h-8"
            />
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-sm sm:text-base truncate">{segment.airline_name}</p>
              <p className="text-xs sm:text-sm text-muted-foreground">{segment.flight_number}</p>
              <p className="text-xs text-muted-foreground">Duration: {segment.duration}</p>
            </div>
            <div className="text-right text-xs sm:text-sm flex-shrink-0">
                <p className="font-medium">{segment.departure_airport} → {segment.arrival_airport}</p>
                <p className="text-muted-foreground text-xs">
                  {formatDateTime(segment.departure_datetime).time} - {formatDateTime(segment.arrival_datetime).time}
                </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}