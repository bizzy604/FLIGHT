import { motion } from "framer-motion"
import { MapPin, Plane, Shield, Headphones } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"

interface ServiceCardProps {
  icon: React.ReactNode
  title: string
  description: string
  color: string
}

const ServiceCard = ({ icon, title, description, color }: ServiceCardProps) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true }}
    className="p-4 sm:p-6 lg:p-8 rounded-xl bg-white shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105"
  >
    <div className={`w-12 h-12 sm:w-16 sm:h-16 lg:w-20 lg:h-20 rounded-full bg-gradient-to-r ${color} flex items-center justify-center mb-3 sm:mb-4 lg:mb-6`}>
      {icon}
    </div>
    <h3 className="text-lg sm:text-xl lg:text-2xl font-semibold mb-2 sm:mb-3 lg:mb-4">{title}</h3>
    <p className="text-sm sm:text-base lg:text-lg text-gray-600 leading-relaxed">{description}</p>
  </motion.div>
)

export function ServicesSection() {
  const services = [
    {
      icon: <MapPin className="h-8 w-8 text-white" />,
      title: "Calculated Weather",
      description: "Get accurate and up-to-date weather forecasts to plan your trips effectively.",
      color: "from-purple-500 to-blue-500"
    },
    {
      icon: <Plane className="h-8 w-8 text-white" />,
      title: "Best Flights",
      description: "Find the best flight deals and enjoy a comfortable journey to your destination.",
      color: "from-orange-500 to-red-500"
    },
    {
      icon: <Headphones className="h-8 w-8 text-white" />,
      title: "Local Events",
      description: "Discover exciting local events and activities to enhance your travel experience.",
      color: "from-green-500 to-teal-500"
    },
    {
      icon: <Shield className="h-8 w-8 text-white" />,
      title: "Customization",
      description: "Tailor your travel plans with our customizable packages to suit your preferences.",
      color: "from-pink-500 to-rose-500"
    }
  ]

  return (
    <section className="py-12 sm:py-16 lg:py-20 xl:py-24 bg-gray-50 px-4 sm:px-6 lg:px-8">
      <div className="container mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-8 sm:mb-12 lg:mb-16"
        >
          <h2 className="text-2xl sm:text-3xl lg:text-4xl xl:text-5xl font-bold mb-3 sm:mb-4 lg:mb-6 pt-6 sm:pt-8 lg:pt-10">Our Services</h2>
          <p className="text-sm sm:text-base lg:text-lg xl:text-xl text-gray-600 max-w-2xl lg:max-w-3xl xl:max-w-4xl mx-auto leading-relaxed">
            We offer the best services in the travel industry to make your journey memorable and hassle-free.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 lg:gap-8 xl:gap-10">
          {services.map((service, index) => (
            <ServiceCard key={index} {...service} />
          ))}
        </div>
      </div>
    </section>
  )
}