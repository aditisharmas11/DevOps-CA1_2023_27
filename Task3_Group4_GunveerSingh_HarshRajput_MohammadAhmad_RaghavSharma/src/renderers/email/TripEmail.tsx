import { Email } from '@unlayer/react-elements'
import type { Trip } from '../../types/trip'

interface TripEmailProps {
  trip: Trip
}

export default function TripEmail({ trip }: TripEmailProps) {
  const itineraryDays = trip.itinerary.slice(0, 6)
  const restaurants = trip.restaurants.slice(0, 3)
  const packingItems = trip.packingList.filter((item) => item.required).slice(0, 6)
  const weatherPreview = trip.weather.slice(0, 2)
  const bookingReference = `ATL-${trip.id.slice(0, 8).toUpperCase()}`
  const generationDate = new Date(trip.updatedAt).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })

  return (
    <Email>
      <div className="render-surface render-surface--email render-surface--email-premium">
        <section className="emailtrip-shell">
          <header className="emailtrip-header" aria-label="Atlas email header">
            <p className="emailtrip-logo">ATLAS</p>
            <p className="emailtrip-logo-sub">Travel Concierge</p>
            <p className="emailtrip-confirm-badge">Booking Confirmed</p>
          </header>

          <section className="emailtrip-hero" aria-label="Trip hero banner">
            <p className="emailtrip-kicker">Booking Confirmation</p>
            <h1>{trip.destination.name} · {trip.destination.country}</h1>
            <p>{trip.overview.vibe}</p>
            <div className="emailtrip-hero-meta">
              <span>Reference {bookingReference}</span>
              <span>Generated {generationDate}</span>
            </div>
          </section>

          <section className="emailtrip-section" aria-label="Greeting">
            <h2>Hello {trip.traveler.name}, your journey is confirmed.</h2>
            <p>
              Your itinerary has been curated and reserved. Below is your complete travel brief, designed for elegant reading across desktop and mobile inboxes.
            </p>
          </section>

          <section className="emailtrip-section" aria-label="Trip summary">
            <p className="emailtrip-label">Trip Summary</p>
            <div className="emailtrip-summary-grid">
              <article>
                <span>Duration</span>
                <strong>{trip.overview.durationDays} days</strong>
              </article>
              <article>
                <span>Budget</span>
                <strong>{trip.budget.currency} {trip.budget.totalBudget.toLocaleString()}</strong>
              </article>
              <article>
                <span>Best season</span>
                <strong>{trip.destination.bestSeason.join(' • ')}</strong>
              </article>
              <article>
                <span>Travelers</span>
                <strong>1 ({trip.traveler.name})</strong>
              </article>
              <article>
                <span>Timezone</span>
                <strong>{trip.destination.timezone}</strong>
              </article>
              <article>
                <span>Currency</span>
                <strong>{trip.budget.currency}</strong>
              </article>
            </div>
          </section>

          <section className="emailtrip-section" aria-label="Hotel">
            <p className="emailtrip-label">Hotel</p>
            <h3>{trip.hotel.name}</h3>
            <p>
              {trip.hotel.propertyType} in {trip.hotel.neighborhood} · rated {trip.hotel.rating.toFixed(1)}
            </p>
            <p>
              Check-in {trip.hotel.checkIn} · Check-out {trip.hotel.checkOut}
            </p>
          </section>

          <section className="emailtrip-section" aria-label="Day-by-day itinerary">
            <p className="emailtrip-label">Day-by-day itinerary</p>
            <div className="emailtrip-day-list">
              {itineraryDays.map((day) => (
                <article key={day.id} className="emailtrip-day-item">
                  <p className="emailtrip-day-title">Day {day.dayNumber} · {day.title}</p>
                  <p>{day.summary}</p>
                  <ul>
                    {day.activities.slice(0, 3).map((activity) => (
                      <li key={activity.id}>{activity.title}</li>
                    ))}
                  </ul>
                </article>
              ))}
            </div>
          </section>

          <section className="emailtrip-section" aria-label="Restaurant recommendations">
            <p className="emailtrip-label">Restaurant recommendations</p>
            <div className="emailtrip-inline-list">
              {restaurants.map((restaurant) => (
                <article key={restaurant.id}>
                  <p className="emailtrip-inline-title">{restaurant.name}</p>
                  <p>{restaurant.cuisine} · {restaurant.neighborhood} · {restaurant.priceLevel}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="emailtrip-section" aria-label="Budget and weather">
            <p className="emailtrip-label">Budget and weather</p>
            <p><strong>Estimated spend:</strong> {trip.budget.currency} {trip.budget.estimatedSpend.toLocaleString()}</p>
            <p><strong>Planned budget:</strong> {trip.budget.currency} {trip.budget.totalBudget.toLocaleString()}</p>
            {weatherPreview.map((weather) => (
              <p key={weather.id}>
                <strong>{weather.date}:</strong> {weather.temperatureHigh}° / {weather.temperatureLow}° · {weather.summary}
              </p>
            ))}
          </section>

          <section className="emailtrip-section" aria-label="Transportation">
            <p className="emailtrip-label">Transportation</p>
            <div className="emailtrip-inline-list">
              {trip.transportation.map((segment) => (
                <article key={segment.id}>
                  <p className="emailtrip-inline-title">{segment.mode.toUpperCase()}</p>
                  <p>{segment.from} → {segment.to}</p>
                  <p>{segment.departureTime ?? 'TBD'} {segment.arrivalTime ? `to ${segment.arrivalTime}` : ''}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="emailtrip-section" aria-label="Packing checklist">
            <p className="emailtrip-label">Packing checklist</p>
            <ul className="emailtrip-packing-list">
              {packingItems.map((item) => (
                <li key={item.id}>{item.name}</li>
              ))}
            </ul>
          </section>

          <section className="emailtrip-section" aria-label="Emergency contacts">
            <p className="emailtrip-label">Emergency contacts</p>
            <p><strong>Local emergency:</strong> {trip.emergencyInfo.localEmergencyNumber}</p>
            <p><strong>Primary contact:</strong> {trip.emergencyInfo.contactName} · {trip.emergencyInfo.contactPhone}</p>
            {trip.emergencyInfo.embassyContact ? <p><strong>Embassy:</strong> {trip.emergencyInfo.embassyContact}</p> : null}
          </section>

          <section className="emailtrip-cta" aria-label="Primary action">
            <button type="button">View Interactive Guide</button>
          </section>

          <footer className="emailtrip-footer" aria-label="Email footer">
            <p>Atlas Concierge · Booking reference {bookingReference}</p>
            <p>This itinerary is generated from your confirmed Trip record on {generationDate}.</p>
          </footer>
        </section>
      </div>
    </Email>
  )
}
