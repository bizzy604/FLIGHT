import { motion } from "framer-motion"

export function StatsSection() {
  const stats = [
    { number: "2K+", label: "Active Travelers" },
    { number: "500+", label: "Destinations" },
    { number: "900+", label: "Hotels" },
    { number: "2M+", label: "Happy Customers" }
  ];

  return (
    <section className="py-12 sm:py-16 lg:py-20 xl:py-24">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="text-center text-2xl sm:text-3xl lg:text-4xl xl:text-5xl font-bold mb-3 sm:mb-4 lg:mb-6">Our Customers Stats</h2>
        <p className="text-center text-sm sm:text-base lg:text-lg xl:text-xl text-gray-600 max-w-2xl lg:max-w-3xl xl:max-w-4xl mx-auto p-3 sm:p-4 lg:p-6 leading-relaxed">
          We are proud to share our achievements with you </p>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 lg:gap-8 xl:gap-12">
          {stats.map((stat, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-center p-4 sm:p-6 lg:p-8 bg-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105"
            >
              <h3 className="text-2xl sm:text-3xl lg:text-4xl xl:text-5xl font-bold text-purple-600 mb-2 sm:mb-3 lg:mb-4">
                {stat.number}
              </h3>
              <p className="text-sm sm:text-base lg:text-lg text-gray-600 leading-relaxed">{stat.label}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}