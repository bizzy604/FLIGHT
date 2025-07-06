"use client"

import Image from "next/image";
import { MainNav } from "@/components/main-nav";
import { UserNav } from "@/components/user-nav";

export default function AboutPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 sm:h-16 items-center justify-between px-3 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2 sm:gap-3">
            <Image
              src="/logo1.png"
              alt="Rea Travel Logo"
              width={32}
              height={32}
              className="w-8 h-8 sm:w-10 sm:h-10 lg:w-12 lg:h-12"
            />
            <span className="text-sm sm:text-base md:text-lg font-semibold">Rea Travel</span>
          </div>
          <div className="flex items-center gap-4">
            <MainNav />
            <UserNav />
          </div>
        </div>
      </header>

      <main className="flex-1">
        <div className="container py-12">
          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold mb-6 sm:mb-8">About Rea Travel</h1>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-12 mb-12 lg:mb-16">
            <div>
              <h2 className="text-xl sm:text-2xl font-bold mb-4">Our Story</h2>
              <p className="text-sm sm:text-base text-gray-600 mb-4 leading-relaxed">
                Founded in 2020, Rea Travel Agency has grown to become one of the most trusted names
                in online travel booking. Our mission is to make travel accessible,
                affordable, and enjoyable for everyone.
              </p>
              <p className="text-sm sm:text-base text-gray-600 leading-relaxed">
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

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8">
            <div className="text-center">
              <h3 className="text-lg sm:text-xl font-semibold mb-3">Our Mission</h3>
              <p className="text-sm sm:text-base text-gray-600 leading-relaxed">
                To revolutionize travel booking by providing transparent pricing and
                exceptional service.
              </p>
            </div>
            <div className="text-center">
              <h3 className="text-lg sm:text-xl font-semibold mb-3">Our Vision</h3>
              <p className="text-sm sm:text-base text-gray-600 leading-relaxed">
                To become the world's most trusted travel companion, making dreams of
                exploration a reality.
              </p>
            </div>
            <div className="text-center">
              <h3 className="text-lg sm:text-xl font-semibold mb-3">Our Values</h3>
              <p className="text-sm sm:text-base text-gray-600 leading-relaxed">
                Transparency, Customer First, Innovation, and Reliability guide
                everything we do.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}