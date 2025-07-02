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
    <section className="py-12 sm:py-16 lg:py-20 xl:py-24">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-8 sm:mb-12 lg:mb-16"
        >
          <h2 className="text-2xl sm:text-3xl lg:text-4xl xl:text-5xl font-bold mb-3 sm:mb-4 lg:mb-6">Top Destinations</h2>
          <p className="text-sm sm:text-base lg:text-lg xl:text-xl text-gray-600 max-w-2xl lg:max-w-3xl xl:max-w-4xl mx-auto leading-relaxed">
            Explore our selection of the most popular destinations around the world
          </p>
        </motion.div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 lg:gap-8 xl:gap-10">
          {destinations.map((destination) => (
            <motion.div
              key={destination.id}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="bg-white rounded-xl overflow-hidden shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105"
            >
              <div className="relative h-40 sm:h-48 lg:h-56 xl:h-64">
                <Image
                  src={destination.image}
                  alt={`${destination.city}, ${destination.country}`}
                  fill
                  className="object-cover hover:scale-110 transition-transform duration-300"
                />
              </div>
              <div className="p-3 sm:p-4 lg:p-6">
                <div className="flex justify-between items-start mb-2 sm:mb-3">
                  <h3 className="text-base sm:text-lg lg:text-xl font-semibold leading-tight">
                    {destination.city}, {destination.country}
                  </h3>
                  <span className="text-purple-600 font-bold text-sm sm:text-base lg:text-lg whitespace-nowrap ml-2">
                    ${destination.price}
                  </span>
                </div>
                <div className="flex items-center text-gray-500">
                  <MapPin className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2 flex-shrink-0" />
                  <span className="text-xs sm:text-sm lg:text-base">{destination.duration}</span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}