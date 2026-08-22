import { Document } from '@unlayer/react-elements'
import type { Trip } from '../../types/trip'

interface TripDocumentProps {
  trip: Trip
}

type DayPart = 'Morning' | 'Afternoon' | 'Evening'

const dayParts: DayPart[] = ['Morning', 'Afternoon', 'Evening']

function formatDateLabel(value: string): string {
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value
  return parsed.toLocaleDateString(undefined, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  })
}

function formatMoney(value: number, currency: string): string {
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(value)
}

function titleCase(value: string): string {
  return value
    .replace(/-/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())
}

function getDayActivities(trip: Trip, dayIndex: number, part: DayPart) {
  const activities = trip.itinerary[dayIndex]?.activities ?? []
  const activityFromLabel = activities.find((activity) => activity.title.toLowerCase().includes(part.toLowerCase()))
  if (activityFromLabel) return activityFromLabel
  if (part === 'Morning') return activities[0]
  if (part === 'Afternoon') return activities[1] ?? activities[0]
  return activities[2] ?? activities[activities.length - 1]
}

function groupPackingItemsByCategory(trip: Trip) {
  return trip.packingList.reduce<Record<string, typeof trip.packingList>>((groups, item) => {
    const key = titleCase(item.category)
    if (!groups[key]) groups[key] = []
    groups[key].push(item)
    return groups
  }, {})
}

function destinationHero(destination: string) {
  const map: Record<string, string> = {
    Tokyo:
      'https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=1800&q=80',
    Dubai:
      'https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=1800&q=80',
    Istanbul:
      'https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?auto=format&fit=crop&w=1800&q=80',
  }
  return map[destination] ?? 'https://images.unsplash.com/photo-1467269204594-9661b134dd2b?auto=format&fit=crop&w=1800&q=80'
}

export default function TripDocument({ trip }: TripDocumentProps) {
  const packingGroups = groupPackingItemsByCategory(trip)
  const packingCategories = Object.keys(packingGroups)
  const weatherPreview = trip.weather.slice(0, 3)
  const dayEstimate = Math.round(trip.budget.estimatedSpend / Math.max(trip.overview.durationDays, 1))

  return (
    <Document>
      <div className="tg-doc">
        <section className="tg-page tg-page-cover">
          <p className="tg-cover-edition">Atlas Edition 01</p>
          <div className="tg-cover-topline">Atlas</div>
          <div className="tg-cover-title-wrap">
            <h1 className="tg-cover-title">Travel Guide</h1>
            <p className="tg-cover-subtitle">A private itinerary edition</p>
          </div>
          <div className="tg-cover-meta">
            <div>
              <span>Destination</span>
              <strong>{trip.destination.name}, {trip.destination.country}</strong>
            </div>
            <div>
              <span>Duration</span>
              <strong>{trip.overview.durationDays} days</strong>
            </div>
            <div>
              <span>Travel Style</span>
              <strong>{trip.traveler.preferences.travelStyle.join(' · ')}</strong>
            </div>
            <div>
              <span>Traveler</span>
              <strong>{trip.traveler.name}</strong>
            </div>
          </div>
          <figure className="tg-cover-image">
            <img src={destinationHero(trip.destination.name)} alt={`${trip.destination.name} city view`} />
          </figure>
        </section>

        <section className="tg-page tg-page-about">
          <header className="tg-section-header">
            <p className="tg-chapter-label">Chapter One</p>
            <p className="tg-kicker">Page 2</p>
            <h2>About This Journey</h2>
          </header>
          <p className="tg-lead">{trip.overview.summary}</p>
          <div className="tg-about-grid">
            <article>
              <h3>Destination Overview</h3>
              <p>{trip.destination.description}</p>
            </article>
            <article>
              <h3>Best Season</h3>
              <p>{trip.destination.bestSeason.join(', ')}</p>
            </article>
            <article>
              <h3>Weather Snapshot</h3>
              <ul>
                {weatherPreview.map((entry) => (
                  <li key={entry.id}>
                    <strong>{formatDateLabel(entry.date)}</strong>
                    <span>{entry.temperatureHigh}° / {entry.temperatureLow}° · {titleCase(entry.condition)}</span>
                  </li>
                ))}
              </ul>
            </article>
            <article>
              <h3>Budget</h3>
              <p className="tg-budget-number">{formatMoney(trip.budget.estimatedSpend, trip.budget.currency)}</p>
              <p>Estimated total spend, with a planned ceiling of {formatMoney(trip.budget.totalBudget, trip.budget.currency)}.</p>
            </article>
            <article>
              <h3>Travel Tips</h3>
              <ul>
                {trip.localTips.slice(0, 3).map((tip) => (
                  <li key={tip.id}>{tip.title}</li>
                ))}
              </ul>
            </article>
            <article>
              <h3>Quick Facts</h3>
              <ul>
                <li>Timezone: {trip.destination.timezone}</li>
                <li>Travel pace: {titleCase(trip.traveler.preferences.pace)}</li>
                <li>Budget range: {titleCase(trip.traveler.preferences.budgetRange)}</li>
              </ul>
            </article>
          </div>
        </section>

        {trip.itinerary.map((day, dayIndex) => {
          const dayRestaurants = trip.restaurants.slice((dayIndex * 2) % trip.restaurants.length, ((dayIndex * 2) % trip.restaurants.length) + 2)
          const dayTransport = trip.transportation.slice(dayIndex % trip.transportation.length, (dayIndex % trip.transportation.length) + 2)
          return (
            <section className="tg-page tg-page-day" key={day.id}>
              <header className="tg-section-header">
                <p className="tg-chapter-label">Chapter {day.dayNumber + 1}</p>
                <p className="tg-kicker">Day by Day Itinerary</p>
                <h2>Day {day.dayNumber}</h2>
                <p className="tg-day-date">{formatDateLabel(day.date)}</p>
                <p className="tg-day-summary">{day.summary}</p>
                <p className="tg-day-estimate">Estimated spend: {formatMoney(dayEstimate, trip.budget.currency)}</p>
              </header>

              <div className="tg-day-timeline">
                {dayParts.map((part) => {
                  const activity = getDayActivities(trip, dayIndex, part)
                  if (!activity) return null
                  return (
                    <article key={`${day.id}-${part}`} className="tg-day-slot">
                      <p className="tg-label">{part}</p>
                      <h3>{activity.title}</h3>
                      <p>{activity.description}</p>
                      <p className="tg-meta-line">{activity.location}{activity.startTime ? ` · ${activity.startTime}` : ''}{activity.endTime ? `-${activity.endTime}` : ''}</p>
                      {activity.notes && <p className="tg-note">{activity.notes}</p>}
                    </article>
                  )
                })}
              </div>

              <div className="tg-day-bottom-grid">
                <article>
                  <p className="tg-label">Restaurants</p>
                  <ul>
                    {dayRestaurants.map((restaurant) => (
                      <li key={restaurant.id}>
                        <strong>{restaurant.name}</strong>
                        <span>{restaurant.cuisine} · {titleCase(restaurant.priceLevel)}</span>
                      </li>
                    ))}
                  </ul>
                </article>
                <article>
                  <p className="tg-label">Transportation</p>
                  <ul>
                    {dayTransport.map((transport) => (
                      <li key={transport.id}>
                        <strong>{titleCase(transport.mode)}</strong>
                        <span>{transport.from} → {transport.to}</span>
                      </li>
                    ))}
                  </ul>
                </article>
                <article>
                  <p className="tg-label">Highlights</p>
                  <ul>
                    {day.activities.slice(0, 3).map((activity) => (
                      <li key={`highlight-${activity.id}`}>{activity.title}</li>
                    ))}
                  </ul>
                </article>
                <article>
                  <p className="tg-label">Notes</p>
                  <p>{day.title}</p>
                  <p>{trip.overview.vibe}</p>
                </article>
              </div>
            </section>
          )
        })}

        <section className="tg-page tg-page-hotel">
          <header className="tg-section-header">
            <p className="tg-chapter-label">Stay Chapter</p>
            <p className="tg-kicker">Stay</p>
            <h2>Hotel</h2>
          </header>
          <article className="tg-hotel-card">
            <div>
              <p className="tg-label">Property</p>
              <h3>{trip.hotel.name}</h3>
              <p>{titleCase(trip.hotel.propertyType)} · {trip.hotel.neighborhood}</p>
            </div>
            <div className="tg-hotel-meta">
              <p><span>Check in</span><strong>{formatDateLabel(trip.hotel.checkIn)}</strong></p>
              <p><span>Check out</span><strong>{formatDateLabel(trip.hotel.checkOut)}</strong></p>
              <p><span>Rating</span><strong>{trip.hotel.rating.toFixed(1)} / 5</strong></p>
              <p><span>Price</span><strong>{formatMoney(trip.hotel.pricePerNight, trip.budget.currency)} per night</strong></p>
            </div>
            <div>
              <p className="tg-label">Amenities</p>
              <ul>
                {trip.hotel.amenities.map((amenity) => (
                  <li key={amenity}>{amenity}</li>
                ))}
              </ul>
            </div>
          </article>
        </section>

        <section className="tg-page tg-page-restaurants">
          <header className="tg-section-header">
            <p className="tg-chapter-label">Dining Chapter</p>
            <p className="tg-kicker">Dining</p>
            <h2>Restaurants</h2>
          </header>
          <div className="tg-restaurant-grid">
            {trip.restaurants.map((restaurant) => (
              <article key={restaurant.id} className="tg-restaurant-card">
                <p className="tg-label">{restaurant.cuisine}</p>
                <h3>{restaurant.name}</h3>
                <p>{restaurant.neighborhood}</p>
                <p>Rating {restaurant.rating.toFixed(1)} · {titleCase(restaurant.priceLevel)}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="tg-page tg-page-packing">
          <header className="tg-section-header">
            <p className="tg-chapter-label">Preparation Chapter</p>
            <p className="tg-kicker">Preparation</p>
            <h2>Packing Checklist</h2>
          </header>
          <div className="tg-packing-grid">
            {packingCategories.map((category) => (
              <article key={category}>
                <p className="tg-label">{category}</p>
                <ul>
                  {packingGroups[category].map((item) => (
                    <li key={item.id}>
                      <span className="tg-check" aria-hidden="true" />
                      <span>{item.name}</span>
                    </li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        </section>

        <section className="tg-page tg-page-tips">
          <header className="tg-section-header">
            <p className="tg-chapter-label">Local Wisdom</p>
            <p className="tg-kicker">On the Ground</p>
            <h2>Local Tips</h2>
          </header>
          <div className="tg-tip-grid">
            {trip.localTips.map((tip) => (
              <article key={tip.id} className="tg-tip-card">
                <p className="tg-label">{titleCase(tip.category)} · {titleCase(tip.priority)}</p>
                <h3>{tip.title}</h3>
                <p>{tip.summary}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="tg-page tg-page-emergency">
          <header className="tg-section-header">
            <p className="tg-chapter-label">Safety Chapter</p>
            <p className="tg-kicker">Essential</p>
            <h2>Emergency</h2>
          </header>
          <div className="tg-emergency-card">
            <p className="tg-label">Emergency Numbers</p>
            <h3>{trip.emergencyInfo.localEmergencyNumber}</h3>
            <p>{trip.emergencyInfo.contactPhone}</p>
            <p><strong>Primary Contact:</strong> {trip.emergencyInfo.contactName}</p>
            {trip.emergencyInfo.embassyContact && <p><strong>Embassy:</strong> {trip.emergencyInfo.embassyContact}</p>}
            {trip.emergencyInfo.medicalNote && <p><strong>Medical Notes:</strong> {trip.emergencyInfo.medicalNote}</p>}
          </div>
          <div className="tg-final-inner">
            <p className="tg-kicker">Atlas</p>
            <h2>Thank you for travelling with Atlas</h2>
            <p>Generated using React Elements</p>
          </div>
        </section>
      </div>
    </Document>
  )
}
