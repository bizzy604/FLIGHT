export default function AboutPage() {
    return (
      <div className="container mx-auto px-4 py-12">
        <h1 className="text-4xl font-bold mb-8">About Rea Travel</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 mb-16">
          <div>
            <h2 className="text-2xl font-bold mb-4">Our Story</h2>
            <p className="text-gray-600 mb-4">
              Founded in 2020, Reatravel Agancy has grown to become one of the most trusted names
              in online travel booking. Our mission is to make travel accessible,
              affordable, and enjoyable for everyone.
            </p>
            <p className="text-gray-600">
              We partner with over 500 airlines worldwide to bring you the best deals
              and ensure a seamless booking experience.
            </p>
          </div>
          
          <div className="relative h-[400px]">
            <img
              src="https://images.unsplash.com/photo-1436491865332-7a61a109cc05"
              alt="Travel Experience"
              className="w-full h-full object-cover rounded-lg"
            />
          </div>
        </div>
  
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          <div className="text-center">
            <h3 className="text-xl font-bold mb-2">Our Mission</h3>
            <p className="text-gray-600">
              To revolutionize travel booking by providing transparent pricing and
              exceptional service.
            </p>
          </div>
          <div className="text-center">
            <h3 className="text-xl font-bold mb-2">Our Vision</h3>
            <p className="text-gray-600">
              To become the world's most trusted travel companion, making dreams of
              exploration a reality.
            </p>
          </div>
          <div className="text-center">
            <h3 className="text-xl font-bold mb-2">Our Values</h3>
            <p className="text-gray-600">
              Transparency, Customer First, Innovation, and Reliability guide
              everything we do.
            </p>
          </div>
        </div>
      </div>
    );
  }