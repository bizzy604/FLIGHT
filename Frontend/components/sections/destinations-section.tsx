import { motion } from "framer-motion"
import Image from "next/image"
import { MapPin } from "lucide-react"

interface Destination {
  id: number;
  image: string;
  city: string;
  country: string;
  price: number;
  duration: string;
}

export function DestinationsSection() {
  const destinations: Destination[] = [
    {
      id: 1,
      image: "/destinations/rome.jpg",
      city: "Rome",
      country: "Italy",
      price: 5420,
      duration: "10 days"
    },
    {
      id: 2,
      image: "/destinations/london.jpg",
      city: "London",
      country: "UK",
      price: 4200,
      duration: "7 days"
    },
    {
      id: 3,
      image: "/destinations/paris.jpeg",
      city: "Paris",
      country: "France",
      price: 4800,
      duration: "5 days"
    },
    {
      id: 4,
      image: "/destinations/bali.jpg",
      city: "Bali",
      country: "Indonesia",
      price: 6500,
      duration: "12 days"
    }
  ];

  return (
    <section className="py-20">
      <div className="container mx-auto px-4">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <h2 className="text-3xl font-bold mb-4">Top Destinations</h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Explore our selection of the most popular destinations around the world
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {destinations.map((destination) => (
            <motion.div
              key={destination.id}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="bg-white rounded-xl overflow-hidden shadow-lg hover:shadow-xl transition-shadow"
            >
              <div className="relative h-48">
                <Image
                  src={destination.image}
                  alt={`${destination.city}, ${destination.country}`}
                  fill
                  className="object-cover"
                />
              </div>
              <div className="p-4">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="text-lg font-semibold">
                    {destination.city}, {destination.country}
                  </h3>
                  <span className="text-purple-600 font-bold">
                    ${destination.price}
                  </span>
                </div>
                <div className="flex items-center text-gray-500">
                  <MapPin className="w-4 h-4 mr-2" />
                  <span>{destination.duration}</span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}