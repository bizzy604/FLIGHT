import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

export function NewsletterSection() {
  return (
    <section className="container mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16 lg:py-20 xl:py-24">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="relative rounded-2xl sm:rounded-3xl bg-gradient-to-r from-purple-100 to-blue-100 p-6 sm:p-8 lg:p-12 xl:p-16 overflow-hidden"
      >
        <div className="absolute inset-0 bg-grid-pattern opacity-10" />
        <div className="relative z-10 text-center max-w-2xl lg:max-w-3xl xl:max-w-4xl mx-auto">
          <h3 className="text-lg sm:text-xl md:text-2xl lg:text-3xl xl:text-4xl font-bold mb-4 sm:mb-6 lg:mb-8 bg-gradient-to-r from-gray-900 to-purple-900 bg-clip-text text-transparent leading-tight">
            Subscribe to get information, latest news and other interesting offers about Rea Travels
          </h3>
          <div className="flex flex-col sm:flex-row items-center gap-3 sm:gap-4 lg:gap-6 justify-center">
            <div className="relative w-full max-w-sm sm:max-w-md lg:max-w-lg">
              <Input
                type="email"
                placeholder="Your email"
                className="pl-10 sm:pl-12 h-10 sm:h-12 lg:h-14 bg-white/80 backdrop-blur-sm w-full text-sm sm:text-base"
              />
              <div className="absolute left-3 sm:left-4 top-1/2 transform -translate-y-1/2 text-sm sm:text-base">📧</div>
            </div>
            <Button className="bg-purple-600 hover:bg-purple-700 transition-colors w-full sm:w-auto h-10 sm:h-12 lg:h-14 px-6 sm:px-8 lg:px-10 text-sm sm:text-base lg:text-lg font-semibold">
              Subscribe
            </Button>
          </div>
        </div>
      </motion.div>
    </section>
  )
}