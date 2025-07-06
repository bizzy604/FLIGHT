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
    className="p-4 sm:p-6 lg:p-8 rounded-xl bg-card shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105"
  >
    <div className={`w-10 h-10 sm:w-12 sm:h-12 lg:w-14 lg:h-14 rounded-full bg-gradient-to-r ${color} flex items-center justify-center mb-3 sm:mb-4`}>
      {icon}
    </div>
    <h3 className="text-base sm:text-lg lg:text-xl font-semibold mb-2 sm:mb-3">{title}</h3>
    <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">{description}</p>
  </motion.div>
)

export function ServicesSection() {
  const services = [
    {
      icon: <MapPin className="h-6 w-6 text-white" />,
      title: "Calculated Weather",
      description: "Get accurate and up-to-date weather forecasts to plan your trips effectively.",
      color: "from-purple-500 to-blue-500"
    },
    {
      icon: <Plane className="h-6 w-6 text-white" />,
      title: "Best Flights",
      description: "Find the best flight deals and enjoy a comfortable journey to your destination.",
      color: "from-orange-500 to-red-500"
    },
    {
      icon: <Headphones className="h-6 w-6 text-white" />,
      title: "Local Events",
      description: "Discover exciting local events and activities to enhance your travel experience.",
      color: "from-green-500 to-teal-500"
    },
    {
      icon: <Shield className="h-6 w-6 text-white" />,
      title: "Customization",
      description: "Tailor your travel plans with our customizable packages to suit your preferences.",
      color: "from-pink-500 to-rose-500"
    }
  ]

  return (
    <section className="py-12 sm:py-16 lg:py-20 xl:py-24 bg-muted/30 px-4 sm:px-6 lg:px-8">
      <div className="container mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-8 sm:mb-12 lg:mb-16"
        >
          <h2 className="text-xl sm:text-2xl lg:text-3xl font-bold mb-3 sm:mb-4 pt-6 sm:pt-8">Our Services</h2>
          <p className="text-sm sm:text-base text-muted-foreground max-w-2xl mx-auto leading-relaxed">
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