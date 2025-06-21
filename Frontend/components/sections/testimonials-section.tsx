import { motion } from "framer-motion"
import Image from "next/image"
import { Star } from "lucide-react"

interface Testimonial {
  id: number;
  name: string;
  location: string;
  comment: string;
  rating: number;
  image: string;
}

export function TestimonialsSection() {
  const testimonials: Testimonial[] = [
    {
      id: 1,
      name: "Mike Taylor",
      location: "Paris, France",
      comment: "The best travel experience I've ever had. The service was exceptional!",
      rating: 5,
      image: "/testimonials/user1.jpg"
    },
    {
      id: 2,
      name: "Sarah Johnson",
      location: "New York, USA",
      comment: "Everything was perfectly organized. I'll definitely book again!",
      rating: 5,
      image: "/testimonials/user2.jpg"
    }
  ];

  return (
    <section className="py-20 bg-gray-50">
      <div className="container mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <h2 className="text-3xl font-bold mb-4">What Our Customers Say</h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Real experiences from our satisfied customers
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {testimonials.map((testimonial) => (
            <motion.div
              key={testimonial.id}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="bg-white p-6 rounded-xl shadow-lg"
            >
              <div className="flex items-center gap-4 mb-4">
                <div className="relative w-16 h-16 rounded-full overflow-hidden">
                  <Image
                    src={testimonial.image}
                    alt={testimonial.name}
                    fill
                    className="object-cover"
                  />
                </div>
                <div>
                  <h3 className="font-semibold">{testimonial.name}</h3>
                  <p className="text-gray-600">{testimonial.location}</p>
                </div>
              </div>
              <p className="text-gray-700 mb-4">{testimonial.comment}</p>
              <div className="flex gap-1">
                {[...Array(testimonial.rating)].map((_, i) => (
                  <Star key={i} className="w-5 h-5 text-yellow-400 fill-current" />
                ))}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}