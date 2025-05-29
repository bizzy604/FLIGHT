import Image from "next/image"
import { ArrowRight } from "lucide-react"

import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

interface DestinationCardProps {
  image: string
  city: string
  country: string
  price: string
}

export function DestinationCard({ image, city, country, price }: DestinationCardProps) {
  return (
    <Card className="overflow-hidden transition-all hover:shadow-lg">
      <div className="relative h-48">
        <Image src={image || "/placeholder.svg"} alt={`${city}, ${country}`} fill className="object-cover" />
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-4 text-white">
          <h3 className="text-xl font-bold">{city}</h3>
          <p className="text-sm">{country}</p>
        </div>
      </div>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Flights from</p>
            <p className="text-lg font-bold">{price}</p>
          </div>
          <Button variant="outline" size="sm" className="group">
            View Flights
            <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

