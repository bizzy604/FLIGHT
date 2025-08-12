import { Wifi, Power, Tv, Utensils, UserPlus, DollarSign } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { AdditionalServices } from "@/types/flight-api"

interface AdditionalServicesComponentProps {
  services: AdditionalServices
}

export function AdditionalServices({ services }: AdditionalServicesComponentProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">Additional Services</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 md:grid-cols-2">
          {/* Seat Selection */}
          {services.seatSelection && (
            <div className="rounded-md border p-3">
              <h3 className="flex items-center text-sm font-medium">
                <UserPlus className="mr-2 h-4 w-4" />
                Seat Selection
              </h3>
              
              <p className="mt-2 text-sm">
                {services.seatSelection.description || "Choose your preferred seat"}
              </p>
              
              <div className="mt-2">
                {services.seatSelection.complimentary ? (
                  <Badge variant="outline" className="bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                    Complimentary
                  </Badge>
                ) : (
                  <div className="flex items-center text-sm">
                    <DollarSign className="mr-1 h-3 w-3" />
                    <span>
                      {services.seatSelection.cost} {services.seatSelection.currency}
                    </span>
                  </div>
                )}
              </div>
              
              {services.seatSelection.seatOptions && services.seatSelection.seatOptions.length > 0 && (
                <div className="mt-3 space-y-1 text-xs text-muted-foreground">
                  <p className="font-medium">Available seat types:</p>
                  <div className="flex flex-wrap gap-1">
                    {services.seatSelection.seatOptions.map((option, index) => (
                      <Badge key={index} variant="secondary" className="font-normal">
                        {option.name}
                        {option.cost && ` (${option.cost} ${option.currency})`}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
          
          {/* Meals */}
          {services.meals && (
            <div className="rounded-md border p-3">
              <h3 className="flex items-center text-sm font-medium">
                <Utensils className="mr-2 h-4 w-4" />
                Meals
              </h3>
              
              <p className="mt-2 text-sm">
                {services.meals.description || (services.meals.complimentary ? "Complimentary meals provided" : "Meals available for purchase")}
              </p>
              
              <div className="mt-2">
                {services.meals.complimentary ? (
                  <Badge variant="outline" className="bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                    Included
                  </Badge>
                ) : services.meals.cost ? (
                  <div className="flex items-center text-sm">
                    <DollarSign className="mr-1 h-3 w-3" />
                    <span>
                      {services.meals.cost} {services.meals.currency}
                    </span>
                  </div>
                ) : (
                  <Badge variant="outline">For purchase</Badge>
                )}
              </div>
              
              {services.meals.options && services.meals.options.length > 0 && (
                <div className="mt-3 space-y-1 text-xs text-muted-foreground">
                  <p className="font-medium">Available meal options:</p>
                  <ul className="list-inside list-disc">
                    {services.meals.options.map((option, index) => (
                      <li key={index}>{option}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {services.meals.dietaryRestrictions && services.meals.dietaryRestrictions.length > 0 && (
                <div className="mt-3 space-y-1 text-xs text-muted-foreground">
                  <p className="font-medium">Dietary options available:</p>
                  <div className="flex flex-wrap gap-1">
                    {services.meals.dietaryRestrictions.map((option, index) => (
                      <Badge key={index} variant="outline" className="font-normal">
                        {option}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
          
          {/* Priority Boarding */}
          {services.priorityBoarding && (
            <div className="rounded-md border p-3">
              <h3 className="text-sm font-medium">Priority Boarding</h3>
              
              <p className="mt-2 text-sm">
                {services.priorityBoarding.description || "Board the aircraft before general boarding"}
              </p>
              
              <div className="mt-2">
                {services.priorityBoarding.complimentary ? (
                  <Badge variant="outline" className="bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                    Included
                  </Badge>
                ) : (
                  <div className="flex items-center text-sm">
                    <DollarSign className="mr-1 h-3 w-3" />
                    <span>
                      {services.priorityBoarding.cost} {services.priorityBoarding.currency}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
          
          {/* In-flight Amenities */}
          <div className="rounded-md border p-3">
            <h3 className="text-sm font-medium">In-flight Amenities</h3>
            
            <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
              <div className="flex items-center">
                <Wifi className="mr-2 h-4 w-4" />
                <div>
                  <p>Wi-Fi</p>
                  <p className="text-xs text-muted-foreground">
                    {services.wifiAvailable ? 
                     (services.wifiDetails?.cost ? 
                      `Available (${services.wifiDetails.cost} ${services.wifiDetails.currency})` : 
                      "Available") : 
                     "Not available"}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center">
                <Power className="mr-2 h-4 w-4" />
                <div>
                  <p>Power Outlets</p>
                  <p className="text-xs text-muted-foreground">
                    {services.powerOutlets ? "Available" : "Not available"}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center">
                <Tv className="mr-2 h-4 w-4" />
                <div>
                  <p>Entertainment</p>
                  <p className="text-xs text-muted-foreground">
                    {services.entertainmentSystem ? 
                     (services.entertainmentDetails ? 
                      services.entertainmentDetails : 
                      "Available") : 
                     "Not available"}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center">
                <Utensils className="mr-2 h-4 w-4" />
                <div>
                  <p>Refreshments</p>
                  <p className="text-xs text-muted-foreground">
                    {services.meals?.available ? 
                     (services.meals.complimentary ? 
                      "Complimentary" : 
                      "For purchase") : 
                     "Not available"}
                  </p>
                </div>
              </div>
            </div>
            
            {services.additionalAmenities && services.additionalAmenities.length > 0 && (
              <div className="mt-3 space-y-1 text-xs text-muted-foreground">
                <p className="font-medium">Additional amenities:</p>
                <ul className="list-inside list-disc">
                  {services.additionalAmenities.map((amenity, index) => (
                    <li key={index}>{amenity}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
