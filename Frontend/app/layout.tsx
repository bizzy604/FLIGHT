import type React from "react"
import type { Metadata } from "next"
import { Poppins } from "next/font/google"
import { ConditionalFooter } from "@/components/organisms"
import { Providers } from "@/components/atoms"
import "./globals.css"

const poppins = Poppins({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-poppins"
})

export const metadata: Metadata = {
  title: "Rea Travel - Flight Booking Portal",
  description: "Book your flights with ease and find the best deals",
    generator: 'Amoni Kevin'
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning className={poppins.variable}>
      <head>
        <link rel="icon" href="/logo1.png" sizes="any" type="image/png" />
      </head>
      <body className={poppins.className}>
        <Providers>
          {children}
          <ConditionalFooter />
        </Providers>
      </body>
    </html>
  )
}