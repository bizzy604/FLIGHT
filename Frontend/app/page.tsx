"use client"

import Image from "next/image"
import Link from "next/link"
import { MainNav, UserNav, FlightSearchForm } from "@/components/organisms"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Star, Plane, Shield, Clock, Award, Users, TrendingUp, MapPin, CheckCircle, Globe, Zap, HeartHandshake } from "lucide-react"
import { useRouter } from "next/navigation"

export default function HomePage() {
  const router = useRouter()

  const handleSearch = (results: any[], meta: any, formData?: any) => {
    console.log('Search completed with results:', results.length, 'offers')
  }

  const handleSearchStart = (formData: any) => {
    if (!formData.origin || !formData.destination || !formData.departDate) {
      return false
    }

    const searchParams = new URLSearchParams({
      origin: formData.origin || '',
      destination: formData.destination || '',
      departDate: formData.departDate ? formData.departDate.toISOString().split('T')[0] : '',
      tripType: formData.tripType === 'round-trip' ? 'round-trip' : 'one-way',
      adults: formData.passengers?.adults?.toString() || '1',
      children: formData.passengers?.children?.toString() || '0',
      infants: formData.passengers?.infants?.toString() || '0',
      cabinClass: formData.cabinType || 'ECONOMY'
    })
    
    if (formData.tripType === 'round-trip' && formData.returnDate) {
      searchParams.set('returnDate', formData.returnDate.toISOString().split('T')[0])
    }
    
    router.push(`/flights?${searchParams.toString()}`)
    return true
  }

  const handleError = (error: string) => {
    console.error('Flight search error:', error)
  }
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-50 w-full border-b bg-white/95 backdrop-blur-md supports-[backdrop-filter]:bg-white/95 shadow-sm">
        <div className="container flex h-16 sm:h-18 items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <Image
              src="/logo1.png"
              alt="Rea Travel Logo"
              width={40}
              height={40}
              className="w-10 h-10 sm:w-12 sm:h-12"
            />
            <span className="text-lg sm:text-xl font-bold text-slate-800">Rea Travel</span>
          </div>
          <div className="flex items-center gap-4">
            <MainNav />
            <UserNav />
          </div>
        </div>
      </header>

      <main className="flex-1">
        {/* Integrated Hero Section with Search Form */}
        <section className="relative min-h-screen flex flex-col">
          {/* Enhanced Background with Gradient Overlay */}
          <div className="absolute inset-0 z-0">
            <Image
              src="https://images.unsplash.com/photo-1544725176-7c40e5a71c5e?w=1920&auto=format&fit=crop&q=90"
              alt="Modern airport terminal with aircraft"
              fill
              className="object-cover"
              priority
            />
            <div className="absolute inset-0 bg-gradient-to-br from-blue-900/70 via-indigo-800/60 to-purple-900/70" />
            <div className="absolute inset-0 bg-gradient-to-t from-black/30 via-transparent to-transparent" />
          </div>

          {/* Floating Elements */}
          <div className="absolute top-20 right-10 opacity-20 animate-float">
            <Plane className="w-16 h-16 text-white/40" />
          </div>
          <div className="absolute bottom-32 left-20 opacity-15 animate-float-delayed">
            <Globe className="w-12 h-12 text-white/30" />
          </div>

          {/* Hero Content */}
          <div className="container relative z-10 flex-1 flex flex-col justify-center py-16 sm:py-20 md:py-24 lg:py-32 px-4 sm:px-6 lg:px-8">
            {/* Flight Search Form - First Priority */}
            <div className="w-full mb-12">
              <div className="bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl border border-white/20 p-4 sm:p-6">
                <FlightSearchForm 
                  onSearch={handleSearch}
                  onError={handleError}
                  onSearchStart={handleSearchStart}
                  className="border-none shadow-none bg-transparent"
                />
              </div>
            </div>

            {/* Hero Content - Below Form */}
            <div className="mx-auto max-w-5xl text-center">
              {/* Trust Badge */}
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-white/10 backdrop-blur-sm rounded-full border border-white/20 mb-6">
                <Award className="w-4 h-4 text-yellow-400" />
                <span className="text-sm font-normal text-white">Award-Winning Flight Platform</span>
              </div>

              {/* Main Headline */}
              <h1 className="mb-5 text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold tracking-[-0.02em] text-white leading-tight">
                Your Journey to{" "}
                <span className="bg-gradient-to-r from-blue-300 via-cyan-200 to-teal-200 bg-clip-text text-transparent font-extrabold">
                  Anywhere
                </span>{" "}
                Starts Here
              </h1>

              {/* Subtitle */}
              <p className="mb-8 text-xl sm:text-2xl text-white/85 max-w-4xl mx-auto font-normal leading-relaxed">
                Experience seamless flight booking with exclusive deals, instant confirmations, and 24/7 support.
              </p>
              <p className="mb-8 text-lg font-medium text-cyan-100 max-w-2xl mx-auto">
                Join over 2M+ happy travelers worldwide.
              </p>

              {/* Key Benefits */}
              <div className="flex flex-wrap justify-center gap-3 sm:gap-4">
                <div className="flex items-center gap-2 px-3 py-2 bg-white/10 backdrop-blur-sm rounded-lg border border-white/20">
                  <CheckCircle className="w-4 h-4 text-green-400" />
                  <span className="text-white text-sm font-normal">Best Prices Guaranteed</span>
                </div>
                <div className="flex items-center gap-2 px-3 py-2 bg-white/10 backdrop-blur-sm rounded-lg border border-white/20">
                  <Zap className="w-4 h-4 text-yellow-400" />
                  <span className="text-white text-sm font-normal">Instant Booking</span>
                </div>
                <div className="flex items-center gap-2 px-3 py-2 bg-white/10 backdrop-blur-sm rounded-lg border border-white/20">
                  <HeartHandshake className="w-4 h-4 text-red-400" />
                  <span className="text-white text-sm font-normal">24/7 Support</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Supporting Sections */}
        <div className="space-y-0">
          {/* Trust Signals & Statistics */}
          <section className="py-16 sm:py-20 bg-gradient-to-b from-slate-50 to-white">
            <div className="container px-4 sm:px-6 lg:px-8">
              <div className="text-center mb-16">
                <h2 className="text-3xl sm:text-4xl lg:text-5xl font-semibold text-slate-800 mb-6 tracking-[-0.01em] leading-tight">
                  Trusted by Millions Worldwide
                </h2>
                <p className="text-xl text-slate-600 max-w-3xl mx-auto leading-relaxed font-light">
                  Our platform has earned the trust of travelers globally with our commitment to excellence and unmatched service quality.
                </p>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
                <div className="group">
                  <div className="flex items-center justify-center w-16 h-16 mx-auto mb-4 bg-blue-100 rounded-full group-hover:bg-blue-200 transition-colors">
                    <Users className="w-8 h-8 text-blue-600" />
                  </div>
                  <div className="text-4xl sm:text-5xl font-semibold text-slate-800 mb-3">2M+</div>
                  <div className="text-base text-slate-600 font-medium">Happy Travelers</div>
                </div>
                <div className="group">
                  <div className="flex items-center justify-center w-16 h-16 mx-auto mb-4 bg-green-100 rounded-full group-hover:bg-green-200 transition-colors">
                    <TrendingUp className="w-8 h-8 text-green-600" />
                  </div>
                  <div className="text-4xl sm:text-5xl font-semibold text-slate-800 mb-3">500+</div>
                  <div className="text-base text-slate-600 font-medium">Airlines Partner</div>
                </div>
                <div className="group">
                  <div className="flex items-center justify-center w-16 h-16 mx-auto mb-4 bg-purple-100 rounded-full group-hover:bg-purple-200 transition-colors">
                    <MapPin className="w-8 h-8 text-purple-600" />
                  </div>
                  <div className="text-4xl sm:text-5xl font-semibold text-slate-800 mb-3">1000+</div>
                  <div className="text-base text-slate-600 font-medium">Destinations</div>
                </div>
                <div className="group">
                  <div className="flex items-center justify-center w-16 h-16 mx-auto mb-4 bg-yellow-100 rounded-full group-hover:bg-yellow-200 transition-colors">
                    <Star className="w-8 h-8 text-yellow-600" />
                  </div>
                  <div className="text-4xl sm:text-5xl font-semibold text-slate-800 mb-3">4.9/5</div>
                  <div className="text-base text-slate-600 font-medium">Customer Rating</div>
                </div>
              </div>
            </div>
          </section>

          {/* Popular Destinations */}
          <section className="py-16 sm:py-20 bg-white">
            <div className="container px-4 sm:px-6 lg:px-8">
              <div className="text-center mb-16">
                <h2 className="text-3xl sm:text-4xl lg:text-5xl font-semibold text-slate-800 mb-6 tracking-[-0.01em] leading-tight">
                  Popular Destinations
                </h2>
                <p className="text-xl text-slate-600 max-w-3xl mx-auto leading-relaxed font-light">
                  Discover amazing places around the world with our curated selection of top destinations that travelers love most.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
                {[
                  { city: "Paris", country: "France", price: "From $599", image: "https://images.unsplash.com/photo-1502602898536-47ad22581b52?w=600&auto=format&fit=crop&q=80", badge: "Most Popular" },
                  { city: "Tokyo", country: "Japan", price: "From $789", image: "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=600&auto=format&fit=crop&q=80", badge: "Trending" },
                  { city: "New York", country: "USA", price: "From $449", image: "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=600&auto=format&fit=crop&q=80", badge: "Best Value" },
                  { city: "London", country: "UK", price: "From $529", image: "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=600&auto=format&fit=crop&q=80" },
                  { city: "Dubai", country: "UAE", price: "From $679", image: "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=600&auto=format&fit=crop&q=80" },
                  { city: "Sydney", country: "Australia", price: "From $899", image: "https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?w=600&auto=format&fit=crop&q=80" }
                ].map((destination, index) => (
                  <Card key={index} className="group overflow-hidden border-0 shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-2">
                    <div className="relative overflow-hidden">
                      <Image
                        src={destination.image}
                        alt={`${destination.city}, ${destination.country}`}
                        width={400}
                        height={250}
                        className="w-full h-48 sm:h-56 object-cover group-hover:scale-110 transition-transform duration-500"
                      />
                      {destination.badge && (
                        <Badge className="absolute top-4 left-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white border-0">
                          {destination.badge}
                        </Badge>
                      )}
                      <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
                      <div className="absolute bottom-4 left-4 text-white">
                        <h3 className="text-xl font-bold">{destination.city}</h3>
                        <p className="text-sm opacity-90">{destination.country}</p>
                      </div>
                    </div>
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <span className="text-2xl font-bold text-blue-600">{destination.price}</span>
                        <Button variant="outline" size="sm" className="group-hover:bg-blue-600 group-hover:text-white transition-colors">
                          View Deals
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </section>

          {/* Features & Benefits */}
          <section className="py-16 sm:py-20 bg-gradient-to-b from-slate-50 to-blue-50">
            <div className="container px-4 sm:px-6 lg:px-8">
              <div className="text-center mb-16">
                <h2 className="text-3xl sm:text-4xl lg:text-5xl font-semibold text-slate-800 mb-6 tracking-[-0.01em] leading-tight">
                  Why Choose Rea Travel?
                </h2>
                <p className="text-xl text-slate-600 max-w-3xl mx-auto leading-relaxed font-light">
                  Experience the difference with our premium features designed specifically for modern travelers who value quality and convenience.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {[
                  {
                    icon: Shield,
                    title: "Secure Booking",
                    description: "Your payments and personal data are protected with bank-level security",
                    color: "text-green-600"
                  },
                  {
                    icon: Clock,
                    title: "24/7 Support",
                    description: "Round-the-clock customer service to assist you whenever you need help",
                    color: "text-blue-600"
                  },
                  {
                    icon: Award,
                    title: "Best Price Guarantee",
                    description: "Find a lower price? We'll match it and give you an additional 10% off",
                    color: "text-purple-600"
                  },
                  {
                    icon: Zap,
                    title: "Instant Confirmation",
                    description: "Get your booking confirmation instantly via email and SMS",
                    color: "text-yellow-600"
                  },
                  {
                    icon: Users,
                    title: "Group Booking",
                    description: "Special discounts and dedicated support for group bookings of 9+ passengers",
                    color: "text-indigo-600"
                  },
                  {
                    icon: Globe,
                    title: "Global Coverage",
                    description: "Access to flights from 500+ airlines to over 1000 destinations worldwide",
                    color: "text-cyan-600"
                  }
                ].map((feature, index) => (
                  <Card key={index} className="group p-6 border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1 bg-white">
                    <div className={`inline-flex items-center justify-center w-14 h-14 mb-4 rounded-lg bg-gradient-to-br from-slate-100 to-slate-200 group-hover:from-blue-50 group-hover:to-blue-100 transition-colors`}>
                      <feature.icon className={`w-7 h-7 ${feature.color}`} />
                    </div>
                    <h3 className="text-lg font-semibold text-slate-800 mb-3">{feature.title}</h3>
                    <p className="text-slate-600 leading-relaxed font-light text-sm">{feature.description}</p>
                  </Card>
                ))}
              </div>
            </div>
          </section>

          {/* Testimonials */}
          <section className="py-16 sm:py-20 bg-white">
            <div className="container px-4 sm:px-6 lg:px-8">
              <div className="text-center mb-16">
                <h2 className="text-3xl sm:text-4xl lg:text-5xl font-semibold text-slate-800 mb-6 tracking-[-0.01em] leading-tight">
                  What Our Customers Say
                </h2>
                <p className="text-xl text-slate-600 max-w-3xl mx-auto leading-relaxed font-light">
                  Don't just take our word for it — hear from thousands of satisfied travelers who've experienced our exceptional service.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {[
                  {
                    name: "Sarah Johnson",
                    location: "New York, USA",
                    rating: 5,
                    comment: "Absolutely fantastic service! Found the perfect flight at an unbeatable price. The booking process was smooth and customer support was exceptional.",
                    avatar: "https://images.unsplash.com/photo-1494790108755-2616b612b786?w=100&auto=format&fit=crop&q=80"
                  },
                  {
                    name: "James Chen",
                    location: "Singapore",
                    rating: 5,
                    comment: "Used Rea Travel for our honeymoon trip to Europe. Everything was perfect from booking to boarding. Highly recommended for stress-free travel planning!",
                    avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&auto=format&fit=crop&q=80"
                  },
                  {
                    name: "Maria Rodriguez",
                    location: "Madrid, Spain",
                    rating: 5,
                    comment: "Best flight booking platform I've ever used. Great prices, instant confirmation, and amazing customer service. My go-to for all my travel needs.",
                    avatar: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&auto=format&fit=crop&q=80"
                  }
                ].map((testimonial, index) => (
                  <Card key={index} className="p-6 border-0 shadow-lg hover:shadow-xl transition-shadow duration-300 bg-gradient-to-br from-white to-slate-50">
                    <div className="flex items-center mb-4">
                      <div className="flex text-yellow-400 mr-2">
                        {[...Array(testimonial.rating)].map((_, i) => (
                          <Star key={i} className="w-5 h-5 fill-current" />
                        ))}
                      </div>
                      <span className="text-sm font-medium text-slate-600">{testimonial.rating}.0</span>
                    </div>
                    <p className="text-slate-700 mb-6 leading-relaxed font-light text-base">"{testimonial.comment}"</p>
                    <div className="flex items-center">
                      <Image
                        src={testimonial.avatar}
                        alt={testimonial.name}
                        width={48}
                        height={48}
                        className="w-12 h-12 rounded-full mr-4 object-cover"
                      />
                      <div>
                        <div className="font-medium text-slate-800">{testimonial.name}</div>
                        <div className="text-sm text-slate-500 font-light">{testimonial.location}</div>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          </section>

          {/* Call to Action */}
          <section className="py-20 sm:py-24 bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-800 text-white">
            <div className="container px-4 sm:px-6 lg:px-8">
              <div className="max-w-4xl mx-auto text-center">
                <h2 className="text-4xl sm:text-5xl lg:text-6xl font-semibold mb-8 tracking-[-0.01em] leading-tight">
                  Ready for Your Next Adventure?
                </h2>
                <p className="text-xl sm:text-2xl mb-12 text-blue-100 max-w-3xl mx-auto font-light leading-relaxed">
                  Join millions of travelers who trust Rea Travel for their journey. Start exploring the world today.
                </p>
                <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                  <Button size="lg" className="bg-white text-blue-600 hover:bg-blue-50 px-8 py-3 text-lg font-semibold">
                    <Plane className="w-5 h-5 mr-2" />
                    Book Your Flight Now
                  </Button>
                  <Button variant="outline" size="lg" className="border-white text-white hover:bg-white hover:text-blue-600 px-8 py-3 text-lg font-semibold">
                    View Special Offers
                  </Button>
                </div>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  )
}

