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
    <section className="py-16 bg-white">
      <div className="container mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <h2 className="text-3xl font-bold mb-4">Our Trusted Partners</h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            We work with the best companies in the travel industry to ensure quality service
          </p>
        </motion.div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-8 items-center">
          {partners.map((partner) => (
            <motion.div
              key={partner.id}
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              whileHover={{ scale: 1.05 }}
              viewport={{ once: true }}
              className="flex items-center justify-center p-4"
            >
              <div className="relative w-32 h-16">
                <Image
                  src={partner.logo}
                  alt={partner.name}
                  fill
                  className="object-contain filter grayscale hover:grayscale-0 transition-all"
                />
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}