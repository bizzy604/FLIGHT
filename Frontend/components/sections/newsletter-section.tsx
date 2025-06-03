import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

export function NewsletterSection() {
  return (
    <section className="container mx-auto px-4 py-20">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="relative rounded-3xl bg-gradient-to-r from-purple-100 to-blue-100 p-12 overflow-hidden"
      >
        <div className="absolute inset-0 bg-grid-pattern opacity-10" />
        <div className="relative z-10 text-center max-w-2xl mx-auto">
          <h3 className="text-2xl md:text-3xl font-bold mb-6 bg-gradient-to-r from-gray-900 to-purple-900 bg-clip-text text-transparent">
            Subscribe to get information, latest news and other interesting offers about Rea Travels
          </h3>
          <div className="flex flex-col sm:flex-row items-center gap-4 justify-center">
            <div className="relative w-full max-w-md">
              <Input
                type="email"
                placeholder="Your email"
                className="pl-12 h-12 bg-white/80 backdrop-blur-sm w-full"
              />
              <div className="absolute left-4 top-1/2 transform -translate-y-1/2">📧</div>
            </div>
            <Button className="bg-purple-600 hover:bg-purple-700 transition-colors w-full sm:w-auto h-12 px-8">
              Subscribe
            </Button>
          </div>
        </div>
      </motion.div>
    </section>
  )
}