import { motion } from "framer-motion"

export function StatsSection() {
  const stats = [
    { number: "2K+", label: "Active Travelers" },
    { number: "500+", label: "Destinations" },
    { number: "900+", label: "Hotels" },
    { number: "2M+", label: "Happy Customers" }
  ];

  return (
    <section className="py-20">
      <div className="container mx-auto px-4">
        <h2 className="text-center text-3xl font-bold mb-4">Our Customers Stats</h2>
        <p className="text-center text-gray-600 max-w-2xl mx-auto p-4">
          We are proud to share our achievements with you </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((stat, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-center"
            >
              <h3 className="text-4xl font-bold text-purple-600 mb-2">
                {stat.number}
              </h3>
              <p className="text-gray-600">{stat.label}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}