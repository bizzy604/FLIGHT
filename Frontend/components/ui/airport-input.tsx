"use client";

import * as React from "react";
import { Check, ChevronsUpDown, MapPin } from "lucide-react";
import { cn } from "@/lib/utils"; // Assuming you have a utils.ts for cn
import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { ScrollArea } from "@/components/ui/scroll-area";

export interface Airport {
  code: string; // e.g., "JFK"
  name: string; // e.g., "John F. Kennedy International Airport"
  city: string; // e.g., "New York"
  country?: string; // e.g., "USA"
}

// Extended mock airport data - in a real app, this would come from an API
// or a much larger static list.
const AIRPORTS_DATA: Airport[] = [
  { code: "JFK", name: "John F. Kennedy Intl.", city: "New York", country: "USA" },
  { code: "LGA", name: "LaGuardia Airport", city: "New York", country: "USA" },
  { code: "EWR", name: "Newark Liberty Intl.", city: "Newark/New York", country: "USA" },
  { code: "LAX", name: "Los Angeles Intl.", city: "Los Angeles", country: "USA" },
  { code: "BUR", name: "Hollywood Burbank Airport", city: "Burbank/Los Angeles", country: "USA" },
  { code: "LGB", name: "Long Beach Airport", city: "Long Beach/Los Angeles", country: "USA" },
  { code: "LHR", name: "Heathrow Airport", city: "London", country: "United Kingdom" },
  { code: "LGW", name: "Gatwick Airport", city: "London", country: "United Kingdom" },
  { code: "STN", name: "Stansted Airport", city: "London", country: "United Kingdom" },
  { code: "LTN", name: "Luton Airport", city: "London", country: "United Kingdom" },
  { code: "CDG", name: "Charles de Gaulle Airport", city: "Paris", country: "France" },
  { code: "ORY", name: "Orly Airport", city: "Paris", country: "France" },
  { code: "HND", name: "Haneda Airport", city: "Tokyo", country: "Japan" },
  { code: "NRT", name: "Narita International Airport", city: "Tokyo", country: "Japan" },
  { code: "BOM", name: "Chhatrapati Shivaji Maharaj Intl.", city: "Mumbai", country: "India" },
  { code: "DEL", name: "Indira Gandhi Intl.", city: "Delhi", country: "India" },
  { code: "DXB", name: "Dubai International Airport", city: "Dubai", country: "UAE" },
  { code: "AUH", name: "Abu Dhabi International Airport", city: "Abu Dhabi", country: "UAE" },
  { code: "SIN", name: "Singapore Changi Airport", city: "Singapore", country: "Singapore" },
  { code: "HKG", name: "Hong Kong International Airport", city: "Hong Kong", country: "China" },
  { code: "AMS", name: "Amsterdam Airport Schiphol", city: "Amsterdam", country: "Netherlands" },
  { code: "FRA", name: "Frankfurt Airport", city: "Frankfurt", country: "Germany" },
  { code: "MUC", name: "Munich Airport", city: "Munich", country: "Germany" },
  { code: "SYD", name: "Sydney Kingsford Smith Airport", city: "Sydney", country: "Australia" },
  { code: "MEL", name: "Melbourne Airport", city: "Melbourne", country: "Australia" },
  { code: "YYZ", name: "Toronto Pearson Intl.", city: "Toronto", country: "Canada" },
  { code: "YVR", name: "Vancouver International Airport", city: "Vancouver", country: "Canada" },
  // Add many more airports as needed for a real application
];

interface AirportInputProps {
  value: string; // The selected airport code (e.g., "JFK")
  onValueChange: (value: string) => void; // Callback with the airport code
  placeholder?: string;
  id?: string;
  disabled?: boolean;
  className?: string;
}

export function AirportInput({
  value,
  onValueChange,
  placeholder = "Select airport...",
  id,
  disabled = false,
  className,
}: AirportInputProps) {
  const [open, setOpen] = React.useState(false);
  const [searchTerm, setSearchTerm] = React.useState("");

  const selectedAirport = AIRPORTS_DATA.find(
    (airport) => airport.code.toLowerCase() === value?.toLowerCase()
  );

  const filteredAirports = React.useMemo(() => {
    if (!searchTerm.trim()) return AIRPORTS_DATA.slice(0, 200); // Show a limited list initially or when search is empty
    const lowerSearchTerm = searchTerm.toLowerCase();
    return AIRPORTS_DATA.filter(
      (airport) =>
        airport.name.toLowerCase().includes(lowerSearchTerm) ||
        airport.city.toLowerCase().includes(lowerSearchTerm) ||
        airport.code.toLowerCase().startsWith(lowerSearchTerm) || // Match start of code
        (airport.country && airport.country.toLowerCase().includes(lowerSearchTerm))
    ).slice(0, 200); // Limit results for performance
  }, [searchTerm]);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          id={id}
          variant="outline"
          role="combobox"
          aria-expanded={open}
          disabled={disabled}
          className={cn(
            "w-full justify-start text-left font-normal h-10", // Ensure consistent height
            !value && "text-muted-foreground",
            className
          )}
        >
          <MapPin className="mr-2 h-4 w-4 flex-shrink-0 text-muted-foreground" />
          {selectedAirport ? (
            <>
              <span className="font-medium mr-1">{selectedAirport.code}</span>
              <span className="truncate text-sm text-muted-foreground hidden sm:inline">
                 - {selectedAirport.city}, {selectedAirport.name.length > 25 ? selectedAirport.name.substring(0,25)+'...' : selectedAirport.name}
              </span>
              <span className="truncate text-sm text-muted-foreground sm:hidden">
                 - {selectedAirport.city}
              </span>
            </>
          ) : (
            placeholder
          )}
           <ChevronsUpDown className="ml-auto h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent 
        className="w-[--radix-popover-trigger-width] max-h-[--radix-popover-content-available-height] p-0"
        style={{ minWidth: '300px' }} // Ensure a minimum width for the popover
      >
        <Command shouldFilter={false}> {/* We handle filtering with searchTerm */}
          <CommandInput 
            placeholder="Search city or airport..." 
            value={searchTerm}
            onValueChange={setSearchTerm} // Update searchTerm as user types
            className="h-9"
          />
          <CommandList>
            <ScrollArea className="max-h-60"> {/* Make the list scrollable */}
                <CommandEmpty>
                    {searchTerm ? "No airport found." : "Type to search..."}
                </CommandEmpty>
                <CommandGroup>
                    {filteredAirports.map((airport) => (
                    <CommandItem
                        key={airport.code}
                        // The value prop for CommandItem is used for internal filtering if enabled,
                        // but also for keyboard navigation. Keep it descriptive.
                        value={`${airport.code} ${airport.city} ${airport.name}`}
                        onSelect={() => {
                        onValueChange(airport.code); // Return only the airport code
                        setOpen(false);
                        setSearchTerm(""); // Clear search term after selection
                        }}
                        className="cursor-pointer flex items-center justify-between w-full"
                    >
                        <div className="flex items-center">
                            <Check
                                className={cn(
                                "mr-2 h-4 w-4",
                                value === airport.code ? "opacity-100" : "opacity-0"
                                )}
                            />
                            <div className="flex flex-col items-start">
                                <span className="font-medium text-sm">{airport.city} ({airport.code})</span>
                                <span className="text-xs text-muted-foreground truncate max-w-[200px] sm:max-w-[250px]">
                                    {airport.name}
                                </span>
                            </div>
                        </div>
                    </CommandItem>
                    ))}
                </CommandGroup>
            </ScrollArea>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}