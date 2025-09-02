import Link from "next/link";
import { Plane, Mail, Phone, MapPin } from "lucide-react";

export function Footer() {
  return (
    <footer className="bg-gray-900 text-white">
      <div className="container py-12 sm:py-16">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 lg:gap-8">
          {/* Company Info */}
          <div className="space-y-3 lg:space-y-4">
            <div className="flex items-center space-x-2">
              {/* <Plane className="h-6 w-6 text-blue-400" /> */}
              <img src="/logo1.png" alt="Rea Travel Logo" className="h-10 w-8" />
              <span className="text-lg font-semibold">Rea Travel</span>
            </div>
            <p className="text-sm text-gray-400 leading-relaxed">
              Your trusted partner for discovering and booking amazing flight deals worldwide.
            </p>
            <div className="space-y-2">
              <div className="flex items-center space-x-2 text-gray-400">
                <Mail className="h-4 w-4 flex-shrink-0" />
                <span className="text-sm">contact@reatravel.com</span>
              </div>
              <div className="flex items-center space-x-2 text-gray-400">
                <Phone className="h-4 w-4 flex-shrink-0" />
                <span className="text-sm">+254 (729) 582-121</span>
              </div>
              <div className="flex items-center space-x-2 text-gray-400">
                <MapPin className="h-4 w-4 flex-shrink-0" />
                <span className="text-sm">Eastleigh 12 Street 00610, Nairobi Kenya</span>
              </div>
            </div>
          </div>

          {/* Quick Links */}
          <div className="space-y-3 lg:space-y-4">
            <h3 className="text-base font-semibold">Quick Links</h3>
            <ul className="space-y-2">
              <li><Link href="/about" className="text-sm text-gray-400 hover:text-white transition-colors">About Us</Link></li>
              <li><Link href="/flights" className="text-sm text-gray-400 hover:text-white transition-colors">Find Flights</Link></li>
              <li><Link href="/destinations" className="text-sm text-gray-400 hover:text-white transition-colors">Destinations</Link></li>
              <li><Link href="/contact" className="text-sm text-gray-400 hover:text-white transition-colors">Contact</Link></li>
              <li><Link href="/terms_conditions" className="text-sm text-gray-400 hover:text-white transition-colors">Terms and Conditions</Link></li>
            </ul>
          </div>

          {/* Support */}
          <div className="space-y-3 lg:space-y-4">
            <h3 className="text-base font-semibold">Support</h3>
            <ul className="space-y-2">
              <li><Link href="/faq" className="text-sm text-gray-400 hover:text-white transition-colors">FAQ</Link></li>
              <li><Link href="/privacy-policy" className="text-sm text-gray-400 hover:text-white transition-colors">Privacy Policy</Link></li>
              <li><Link href="/terms_conditions" className="text-sm text-gray-400 hover:text-white transition-colors">Terms of Service</Link></li>
              <li><Link href="/contact" className="text-sm text-gray-400 hover:text-white transition-colors">Customer Support</Link></li>
            </ul>
          </div>

          {/* Newsletter */}
          {/* <div>
            <h3 className="text-lg font-semibold mb-4">Newsletter</h3>
            <p className="text-gray-400 mb-4">
              Subscribe to our newsletter for the latest travel deals and updates.
            </p>
            <form className="space-y-2">
              <input
                type="email"
                placeholder="Enter your email"
                className="w-full px-4 py-2 rounded-md bg-gray-800 text-white placeholder-gray-400 border border-gray-700 focus:outline-none focus:border-blue-500"
              />
              <button
                type="submit"
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Subscribe
              </button>
            </form>
          </div> */}
        </div>

        {/* Bottom Bar */}
        <div className="border-t border-gray-800 mt-8 pt-6">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <p className="text-sm text-gray-400">
              © {new Date().getFullYear()} Rea Travel Agency. All rights reserved.
            </p>
            <div className="flex space-x-4 mt-4 md:mt-0">
              <Link href="#" className="text-sm text-gray-400 hover:text-white transition-colors">
                Facebook
              </Link>
              <Link href="#" className="text-sm text-gray-400 hover:text-white transition-colors">
                Twitter
              </Link>
              <Link href="#" className="text-sm text-gray-400 hover:text-white transition-colors">
                Instagram
              </Link>
              <Link href="#" className="text-sm text-gray-400 hover:text-white transition-colors">
                LinkedIn
              </Link>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}