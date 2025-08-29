export function generateBookingPDF(booking: any): Blob {
  // In a real application, this would use a PDF generation library
  // For this example, we'll create a simple HTML string and convert it to a Blob

  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <title>Booking Confirmation - ${booking.id}</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        h1 { color: #333; }
        .booking-info { margin-bottom: 20px; }
        .flight-details { margin-bottom: 15px; border: 1px solid #ddd; padding: 10px; }
        .passenger-info { margin-bottom: 15px; }
        .price-summary { margin-top: 20px; border-top: 1px solid #ddd; padding-top: 10px; }
        .total { font-weight: bold; }
      </style>
    </head>
    <body>
      <h1>Booking Confirmation</h1>
      <div class="booking-info">
        <p><strong>Booking Reference:</strong> ${booking.id}</p>
        <p><strong>Contact:</strong> ${booking.contactInfo.email}, ${booking.contactInfo.phone}</p>
      </div>
      
      <h2>Flight Details</h2>
      <div class="flight-details">
        <h3>Outbound Flight</h3>
        <p><strong>Date:</strong> ${booking.flightDetails.outbound.departure.fullDate}</p>
        <p><strong>Flight:</strong> ${booking.flightDetails.outbound.airline.name} ${booking.flightDetails.outbound.airline.code}${booking.flightDetails.outbound.airline.flightNumber}</p>
        <p><strong>From:</strong> ${booking.flightDetails.outbound.departure.city} (${booking.flightDetails.outbound.departure.airport}), Terminal ${booking.flightDetails.outbound.departure.terminal}</p>
        <p><strong>To:</strong> ${booking.flightDetails.outbound.arrival.city} (${booking.flightDetails.outbound.arrival.airport}), Terminal ${booking.flightDetails.outbound.arrival.terminal}</p>
        <p><strong>Departure Time:</strong> ${booking.flightDetails.outbound.departure.time}</p>
        <p><strong>Arrival Time:</strong> ${booking.flightDetails.outbound.arrival.time}</p>
        <p><strong>Duration:</strong> ${booking.flightDetails.outbound.duration}</p>
      </div>
      
      <div class="flight-details">
        <h3>Return Flight</h3>
        <p><strong>Date:</strong> ${booking.flightDetails.return.departure.fullDate}</p>
        <p><strong>Flight:</strong> ${booking.flightDetails.return.airline.name} ${booking.flightDetails.return.airline.code}${booking.flightDetails.return.airline.flightNumber}</p>
        <p><strong>From:</strong> ${booking.flightDetails.return.departure.city} (${booking.flightDetails.return.departure.airport}), Terminal ${booking.flightDetails.return.departure.terminal}</p>
        <p><strong>To:</strong> ${booking.flightDetails.return.arrival.city} (${booking.flightDetails.return.arrival.airport}), Terminal ${booking.flightDetails.return.arrival.terminal}</p>
        <p><strong>Departure Time:</strong> ${booking.flightDetails.return.departure.time}</p>
        <p><strong>Arrival Time:</strong> ${booking.flightDetails.return.arrival.time}</p>
        <p><strong>Duration:</strong> ${booking.flightDetails.return.duration}</p>
      </div>
      
      <h2>Passenger Information</h2>
      ${booking.passengers && booking.passengers.length > 0 // Check if passengers exist and the array is not empty
        ? booking.passengers.map(
          (passenger: any) => `
        <div class="passenger-info">
          <p><strong>Name:</strong> ${passenger.firstName || 'N/A'} ${passenger.lastName || ''}</p>
          <p><strong>Email:</strong> ${passenger.email || 'N/A'}</p>
          <p><strong>Phone:</strong> ${passenger.phone || 'N/A'}</p>
          <p><strong>Date of Birth:</strong> ${passenger.dob || 'N/A'}</p>
          <p><strong>Nationality:</strong> ${passenger.nationality || 'N/A'}</p>
          <p><strong>Passport/ID:</strong> ${passenger.passportId || 'N/A'}</p>
          <p><strong>Passport Expiry:</strong> ${passenger.passportExpiry || 'N/A'}</p>
          <p><strong>Gender:</strong> ${passenger.gender || 'N/A'}</p>
          <p><strong>Seat Preference:</strong> ${passenger.seatPreference || 'N/A'}</p>
          <p><strong>Meal Preference:</strong> ${passenger.mealPreference || 'N/A'}</p>
          <p><strong>Special Needs:</strong> ${passenger.specialNeeds || 'N/A'}</p>
        </div>
      `
        ).join('')
        : '<p>No passenger information available.</p>' // Display a message if no passengers
      }
      
      <h2>Selected Extras</h2>
      <p><strong>Seats:</strong> Outbound: ${booking.extras.seats.outbound}, Return: ${booking.extras.seats.return}</p>
      <p><strong>Baggage:</strong> ${booking.extras.baggage.included}, ${booking.extras.baggage.additional}</p>
      <p><strong>Meals:</strong> Outbound: ${booking.extras.meals.outbound}, Return: ${booking.extras.meals.return}</p>
      <p><strong>Additional Services:</strong> ${booking.extras.additionalServices.join(", ")}</p>
      
      <div class="price-summary">
        <h2>Price Summary</h2>
        <p>Base fare: $${booking.pricing.baseFare.toFixed(2)}</p>
        <p>Taxes and fees: $${booking.pricing.taxes.toFixed(2)}</p>
        <p>Seat selection: $${booking.pricing.seatSelection.toFixed(2)}</p>
        <p>Extra baggage: $${booking.pricing.extraBaggage.toFixed(2)}</p>
        <p>Priority boarding: $${booking.pricing.priorityBoarding.toFixed(2)}</p>
        <p>Travel insurance: $${booking.pricing.travelInsurance.toFixed(2)}</p>
        <p class="total">Total: $${booking.pricing.total.toFixed(2)}</p>
      </div>
      
      <footer>
        <p>Thank you for choosing SkyWay Airlines. We wish you a pleasant journey!</p>
        <p>For any assistance, please contact our customer support at support@skyway.com or call +1-800-SKY-WAYS.</p>
      </footer>
    </body>
    </html>
  `

  const blob = new Blob([html], { type: "text/html" })
  return blob
}

export function downloadBookingConfirmation(booking: any) {
  const blob = generateBookingPDF(booking)
  const url = URL.createObjectURL(blob)

  const a = document.createElement("a")
  a.href = url
  a.download = `booking-confirmation-${booking.id}.html`
  document.body.appendChild(a)
  a.click()

  // Clean up
  setTimeout(() => {
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }, 100)
}

