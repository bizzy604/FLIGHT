import { motion } from "framer-motion"

export function StatsSection() {
  const stats = [
    { number: "2K+", label: "Active Travelers" },
    { number: "500+", label: "Destinations" },
    { number: "900+", label: "Hotels" },
    { number: "2M+", label: "Happy Customers" }
  ];

  return (
    <section className="py-12 sm:py-16 lg:py-20">
      <div className="container">
        <h2 className="text-center text-xl sm:text-2xl lg:text-3xl font-bold mb-3 sm:mb-4">Our Customer Stats</h2>
        <p className="text-center text-sm sm:text-base text-muted-foreground max-w-2xl mx-auto mb-8 sm:mb-12 leading-relaxed">
          We are proud to share our achievements with you</p>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 lg:gap-8">
          {stats.map((stat, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-center p-4 sm:p-6 bg-card rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105"
            >
              <h3 className="text-xl sm:text-2xl lg:text-3xl font-bold text-purple-600 mb-2">
                {stat.number}
              </h3>
              <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">{stat.label}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}