import { Page } from '@unlayer/react-elements'
import type { Trip } from '../../types/trip'

interface TripPageProps {
  trip: Trip
}

function destinationHero(destination: string): string {
  const map: Record<string, string> = {
    Tokyo: 'https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=1800&q=80',
    Dubai: 'https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=1800&q=80',
    Istanbul: 'https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?auto=format&fit=crop&w=1800&q=80',
  }
  return map[destination] ?? 'https://images.unsplash.com/photo-1467269204594-9661b134dd2b?auto=format&fit=crop&w=1800&q=80'
}

function cleanTitle(title: string | undefined): string {
  if (!title) return 'Planned experience'
  return title.replace(/^(Morning|Afternoon|Evening):\s*/i, '')
}

export default function TripPage({ trip }: TripPageProps) {
  const durationLabel = `${trip.overview.durationDays} days`
  const budgetLabel = `${trip.budget.currency} ${trip.budget.totalBudget.toLocaleString()}`
  const bestSeasonLabel = trip.destination.bestSeason.join(' • ')
  const travelerLabel = `1 traveler · ${trip.traveler.name}`
  const itineraryDays = trip.itinerary.slice(0, trip.overview.durationDays)
  const featuredRestaurants = trip.restaurants.slice(0, 3)
  const localExperiences = trip.localTips.slice(0, 6)
  const packingHighlights = trip.packingList.filter((item) => item.required).slice(0, 5)
  const weatherPreview = trip.weather.slice(0, 3)
  const dailyEstimate = Math.round(trip.budget.estimatedSpend / Math.max(trip.overview.durationDays, 1))

  return (
    <Page>
      <div className="render-surface render-surface--page render-surface--page-premium">
        <section className="webtrip-hero">
          <img className="webtrip-hero-image" src={destinationHero(trip.destination.name)} alt={`${trip.destination.name} skyline`} />
          <div className="webtrip-hero-overlay" />
          <div className="webtrip-hero-content">
            <p className="webtrip-kicker">Atlas Curated Journey</p>
            <h1 className="webtrip-title">{trip.destination.name}, {trip.destination.country}</h1>
            <p className="webtrip-intro">
              {trip.overview.summary}
            </p>
            <p className="webtrip-subintro">
              Crafted as an editorial escape with cinematic pacing, thoughtful hospitality and local character from arrival to return.
            </p>
            <div className="webtrip-hero-tags">
              <span>{trip.traveler.preferences.travelStyle.join(' · ')}</span>
              <span>{durationLabel}</span>
              <span>{budgetLabel}</span>
            </div>
          </div>
        </section>

        <section className="webtrip-facts" aria-label="Trip quick facts">
          <article className="webtrip-fact-card">
            <p>Duration</p>
            <strong>{durationLabel}</strong>
          </article>
          <article className="webtrip-fact-card">
            <p>Budget</p>
            <strong>{budgetLabel}</strong>
          </article>
          <article className="webtrip-fact-card">
            <p>Best season</p>
            <strong>{bestSeasonLabel}</strong>
          </article>
          <article className="webtrip-fact-card">
            <p>Travelers</p>
            <strong>{travelerLabel}</strong>
          </article>
        </section>

        <section className="webtrip-section" aria-label="Daily itinerary">
          <div className="webtrip-section-head">
            <p className="webtrip-section-kicker">Daily Itinerary</p>
            <h2>Day-by-day rhythm</h2>
          </div>
          <div
            className="webtrip-itinerary-grid"
            data-count={itineraryDays.length}
          >
            {itineraryDays.map((day) => (
              <article className="webtrip-itinerary-card" key={day.id}>
                <p className="webtrip-itinerary-day">Day {day.dayNumber}</p>
                <h3>{day.title}</h3>
                <p>{day.summary}</p>
                <div className="webtrip-itinerary-meta">
                  {day.activities[0] && <span><strong>Morning:</strong> {cleanTitle(day.activities[0].title)}</span>}
                  {day.activities[1] && <span><strong>Afternoon:</strong> {cleanTitle(day.activities[1].title)}</span>}
                  {day.activities[2] && <span><strong>Evening:</strong> {cleanTitle(day.activities[2].title)}</span>}
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="webtrip-section" aria-label="Budget and weather overview">
          <div className="webtrip-section-head">
            <p className="webtrip-section-kicker">Journey Planning</p>
            <h2>Budget and weather intelligence</h2>
          </div>
          <div className="webtrip-budget-weather-grid">
            <article className="webtrip-feature-card webtrip-feature-card--budget">
              <div>
                <p className="webtrip-section-kicker">Budget</p>
                <h2>{trip.budget.currency} {trip.budget.estimatedSpend.toLocaleString()}</h2>
                <p>
                  Estimated total spend with a daily planning target of {trip.budget.currency} {dailyEstimate.toLocaleString()}.
                </p>
              </div>
              <div className="webtrip-meta-list">
                <p><strong>Lodging:</strong> {trip.budget.currency} {trip.budget.categories.lodging.toLocaleString()}</p>
                <p><strong>Food:</strong> {trip.budget.currency} {trip.budget.categories.food.toLocaleString()}</p>
                <p><strong>Activities:</strong> {trip.budget.currency} {trip.budget.categories.activities.toLocaleString()}</p>
              </div>
            </article>
            <div className="webtrip-weather-grid">
              {weatherPreview.map((weather) => (
                <article key={weather.id} className="webtrip-weather-card">
                  <p>{weather.date}</p>
                  <h3>{weather.temperatureHigh}° / {weather.temperatureLow}°</h3>
                  <span>{weather.condition}</span>
                  <small>{weather.summary}</small>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="webtrip-section" aria-label="Featured hotel">
          <div className="webtrip-feature-card webtrip-feature-card--hotel">
            <div>
              <p className="webtrip-section-kicker">Featured Hotel</p>
              <h2>{trip.hotel.name}</h2>
              <p>
                {trip.hotel.propertyType} stay in {trip.hotel.neighborhood}, rated {trip.hotel.rating.toFixed(1)}. Designed for calm mornings and unhurried evenings.
              </p>
            </div>
            <div className="webtrip-meta-list">
              <p><strong>Check-in:</strong> {trip.hotel.checkIn}</p>
              <p><strong>Check-out:</strong> {trip.hotel.checkOut}</p>
              <p><strong>Nightly:</strong> {trip.budget.currency} {trip.hotel.pricePerNight.toLocaleString()}</p>
            </div>
          </div>
        </section>

        <section className="webtrip-section" aria-label="Featured restaurants">
          <div className="webtrip-section-head">
            <p className="webtrip-section-kicker">Featured Restaurants</p>
            <h2>Dining worth planning around</h2>
          </div>
          <div className="webtrip-restaurant-grid">
            {featuredRestaurants.map((restaurant) => (
              <article key={restaurant.id} className="webtrip-restaurant-card">
                <h3>{restaurant.name}</h3>
                <p>{restaurant.cuisine} · {restaurant.neighborhood}</p>
                <p>Rating {restaurant.rating.toFixed(1)} · {restaurant.priceLevel}</p>
                {restaurant.notes ? <p>{restaurant.notes}</p> : null}
              </article>
            ))}
          </div>
        </section>

        <section className="webtrip-section" aria-label="Local experiences">
          <div className="webtrip-section-head">
            <p className="webtrip-section-kicker">Local Experiences</p>
            <h2>Culture and practical insights</h2>
          </div>
          <div
            className="webtrip-experience-grid"
            data-count={localExperiences.length}
          >
            {localExperiences.map((tip) => (
              <article key={tip.id} className="webtrip-experience-card">
                <h3>{tip.title}</h3>
                <p>{tip.summary}</p>
                <span>{tip.category} · {tip.priority} priority</span>
              </article>
            ))}
          </div>
        </section>

        <section className="webtrip-section" aria-label="Packing highlights">
          <div className="webtrip-feature-card">
            <div>
              <p className="webtrip-section-kicker">Packing Highlights</p>
              <h2>Essentials to prepare</h2>
            </div>
            <ul className="webtrip-packing-list">
              {packingHighlights.map((item) => (
                <li key={item.id}>{item.name}</li>
              ))}
            </ul>
          </div>
        </section>

        <section className="webtrip-section" aria-label="Emergency information">
          <div className="webtrip-feature-card webtrip-feature-card--emergency">
            <div>
              <p className="webtrip-section-kicker">Emergency Information</p>
              <h2>Safety at a glance</h2>
            </div>
            <div className="webtrip-meta-list">
              <p><strong>Local emergency:</strong> {trip.emergencyInfo.localEmergencyNumber}</p>
              <p><strong>Primary contact:</strong> {trip.emergencyInfo.contactName} ({trip.emergencyInfo.contactPhone})</p>
              {trip.emergencyInfo.embassyContact ? <p><strong>Embassy:</strong> {trip.emergencyInfo.embassyContact}</p> : null}
              {trip.emergencyInfo.medicalNote ? <p><strong>Medical note:</strong> {trip.emergencyInfo.medicalNote}</p> : null}
            </div>
          </div>
        </section>
      </div>
    </Page>
  )
}
