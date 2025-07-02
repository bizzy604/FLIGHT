import { motion } from "framer-motion"
import Image from "next/image"

interface Partner {
  id: number;
  name: string;
  logo: string;
}

export function PartnersSection() {
  const partners: Partner[] = [
    {
      id: 1,
      name: "Booking.com",
      logo: "/partners/bookingcom-logo.png"
    },
    {
      id: 2,
      name: "Ethopian Airlines",
      logo: "/partners/ethopia.png"
    },
    {
      id: 3,
      name: "Kenya Airways",
      logo: "/partners/kenya-airways.png"
    },
    {
      id: 4,
      name: "Airbnb",
      logo: "/partners/Airbnb.svg"
    },
    {
      id: 5,
      name: "Hotels.com",
      logo: "/partners/hotels.png"
    },
    {
      id: 6,
      name: "Qatar Airways",
      logo: "/partners/qatar.png"
    },
    {
      id: 7,
      name: "Rwandair",
      logo: "/partners/rwanda.png"
    },
    {
      id: 8,
      name: "Air Arabia",
      logo: "/partners/airarabia.png"
    },
    {
      id: 9,
      name: "Emirates",
      logo: "/partners/emirates.png"
    },
    {
      id: 10,
      name: "IATA",
      logo: "/partners/iata.png"
    }
  ];

  return (
    <section className="py-12 sm:py-16 lg:py-20 xl:py-24 bg-white">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-8 sm:mb-12 lg:mb-16"
        >
          <h2 className="text-2xl sm:text-3xl lg:text-4xl xl:text-5xl font-bold mb-3 sm:mb-4 lg:mb-6">Our Trusted Partners</h2>
          <p className="text-sm sm:text-base lg:text-lg xl:text-xl text-gray-600 max-w-2xl lg:max-w-3xl xl:max-w-4xl mx-auto leading-relaxed">
            We work with the best companies in the travel industry to ensure quality service
          </p>
        </motion.div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 sm:gap-6 lg:gap-8 xl:gap-10 items-center">
          {partners.map((partner) => (
            <motion.div
              key={partner.id}
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              whileHover={{ scale: 1.05 }}
              viewport={{ once: true }}
              className="flex items-center justify-center p-3 sm:p-4 lg:p-6 bg-gray-50 rounded-lg hover:bg-white hover:shadow-lg transition-all duration-300"
            >
              <div className="relative w-20 h-12 sm:w-28 sm:h-14 lg:w-32 lg:h-16 xl:w-36 xl:h-18">
                <Image
                  src={partner.logo}
                  alt={partner.name}
                  fill
                  className="object-contain filter grayscale hover:grayscale-0 transition-all duration-300"
                />
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}