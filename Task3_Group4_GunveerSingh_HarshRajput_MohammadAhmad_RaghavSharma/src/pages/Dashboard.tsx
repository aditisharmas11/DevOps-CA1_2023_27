import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTripContext } from '../context/useTripContext'

function getHourFromTime(value?: string) {
  if (!value) {
    return null
  }

  const match = value.match(/^(\d{1,2})/)
  if (!match) {
    return null
  }

  const hour = Number(match[1])
  if (!Number.isFinite(hour) || hour < 0 || hour > 23) {
    return null
  }

  return hour
}

function splitActivitiesByDayPart<T extends { startTime?: string }>(activities: T[]) {
  const withTime = activities.filter((activity) => getHourFromTime(activity.startTime) !== null)

  if (withTime.length > 0) {
    return {
      morning: withTime.filter((activity) => {
        const hour = getHourFromTime(activity.startTime)
        return hour !== null && hour < 12
      }),
      afternoon: withTime.filter((activity) => {
        const hour = getHourFromTime(activity.startTime)
        return hour !== null && hour >= 12 && hour < 18
      }),
      evening: withTime.filter((activity) => {
        const hour = getHourFromTime(activity.startTime)
        return hour !== null && hour >= 18
      }),
    }
  }

  const chunkSize = Math.max(1, Math.ceil(activities.length / 3))

  return {
    morning: activities.slice(0, chunkSize),
    afternoon: activities.slice(chunkSize, chunkSize * 2),
    evening: activities.slice(chunkSize * 2),
  }
}

export default function DashboardPage() {
  const navigate = useNavigate()
  const { currentTrip, error, loading } = useTripContext()
  const [selectedChapterId, setSelectedChapterId] = useState<string | null>(null)

  const trip = currentTrip

  const selectedChapter = useMemo(() => {
    if (!trip?.itinerary.length) {
      return null
    }

    const fallbackId = selectedChapterId ?? trip.itinerary[0].id
    return trip.itinerary.find((chapter) => chapter.id === fallbackId) ?? trip.itinerary[0]
  }, [selectedChapterId, trip])

  const chapterIndex = trip?.itinerary.findIndex((chapter) => chapter.id === selectedChapter?.id) ?? -1

  if (loading) {
    return (
      <div className="dashboard-page">
        <section className="dashboard-cover-section">
          <div className="dashboard-cover-card">
            <div className="dashboard-cover-visual" aria-hidden="true" />
            <div className="dashboard-cover-copy">
              <p className="dashboard-kicker">atlas • travel book</p>
              <h1>Assembling your journey.</h1>
              <p className="dashboard-summary">Atlas is shaping your itinerary and preparing the first draft of your travel book.</p>
              <button type="button" className="dashboard-cta" onClick={() => navigate('/')}>Return Home</button>
            </div>
          </div>
        </section>
      </div>
    )
  }

  if (!trip) {
    return (
      <div className="dashboard-page">
        <section className="dashboard-cover-section">
          <div className="dashboard-cover-card">
            <div className="dashboard-cover-visual" aria-hidden="true" />
            <div className="dashboard-cover-copy">
              <p className="dashboard-kicker">atlas • travel book</p>
              <h1>No journey has been created yet.</h1>
              <p className="dashboard-summary">Create a first journey from the landing page to start shaping your Atlas experience.</p>
              <button type="button" className="dashboard-cta" onClick={() => navigate('/')}>Create Journey</button>
            </div>
          </div>
        </section>
      </div>
    )
  }

  if (error) {
    return (
      <div className="dashboard-page">
        <section className="dashboard-cover-section">
          <div className="dashboard-cover-card">
            <div className="dashboard-cover-visual" aria-hidden="true" />
            <div className="dashboard-cover-copy">
              <p className="dashboard-kicker">atlas • travel book</p>
              <h1>We could not assemble the journey.</h1>
              <p className="dashboard-summary">{error}</p>
              <button type="button" className="dashboard-cta" onClick={() => navigate('/')}>Try Again</button>
            </div>
          </div>
        </section>
      </div>
    )
  }

  const destinationImageUrl = `https://source.unsplash.com/1800x1100/?${encodeURIComponent(`${trip.destination.name} ${trip.destination.country} travel landscape`)}`
  const weatherForDay = trip.weather.find((entry) => entry.date === selectedChapter?.date) ?? trip.weather[0]
  const dayActivities = selectedChapter?.activities ?? []
  const dayMoments = splitActivitiesByDayPart(dayActivities)
  const dayTransportation = trip.transportation.slice(0, 4)
  const chapterRestaurants = trip.restaurants.slice(0, 3)
  const travelStyle = trip.traveler.preferences.travelStyle.length > 0
    ? trip.traveler.preferences.travelStyle.join(' • ')
    : trip.overview.vibe
  const bestSeason = trip.destination.bestSeason.length > 0
    ? trip.destination.bestSeason.join(' • ')
    : 'Year-round'

  return (
    <div className="dashboard-page">
      <section className="dashboard-hero">
        <div className="dashboard-hero-image-wrap">
          <img className="dashboard-hero-image" src={destinationImageUrl} alt={`${trip.destination.name} travel mood`} />
          <div className="dashboard-hero-gradient" />
        </div>
        <div className="dashboard-hero-copy">
          <p className="dashboard-kicker">atlas • editorial travel guide</p>
          <h1>{trip.destination.name}</h1>
          <p className="dashboard-summary">{trip.overview.summary}</p>
          <div className="dashboard-facts-grid">
            <article className="dashboard-fact">
              <span>Duration</span>
              <strong>{trip.overview.durationDays} days</strong>
            </article>
            <article className="dashboard-fact">
              <span>Budget</span>
              <strong>{trip.budget.currency} {trip.budget.totalBudget.toLocaleString()}</strong>
            </article>
            <article className="dashboard-fact">
              <span>Weather</span>
              <strong>{weatherForDay?.summary ?? 'Seasonal conditions expected'}</strong>
            </article>
            <article className="dashboard-fact">
              <span>Travel Style</span>
              <strong>{travelStyle}</strong>
            </article>
            <article className="dashboard-fact">
              <span>Best Season</span>
              <strong>{bestSeason}</strong>
            </article>
          </div>
          <button type="button" className="dashboard-cta">Continue Reading</button>
        </div>
      </section>

      <section className="dashboard-layout">
        <aside className="dashboard-timeline" aria-label="Journey timeline">
          <p className="dashboard-label">Journey Timeline</p>
          <div className="timeline-list">
            {trip.itinerary.map((chapter, index) => (
              <button
                key={chapter.id}
                type="button"
                className={`timeline-item ${selectedChapter?.id === chapter.id ? 'is-active' : ''}`}
                onClick={() => setSelectedChapterId(chapter.id)}
              >
                <div className="timeline-marker" aria-hidden="true">
                  <span className="timeline-dot" />
                  {index < trip.itinerary.length - 1 ? <span className="timeline-line" /> : null}
                </div>
                <div className="timeline-copy">
                  <span className="timeline-day">Day {chapter.dayNumber}</span>
                  <span className="timeline-title">{chapter.title}</span>
                  <span className="timeline-date">{chapter.date}</span>
                </div>
              </button>
            ))}
          </div>
        </aside>

        <article className="dashboard-reader">
          <header className="reader-intro">
            <p className="dashboard-label">Chapter {Math.max(1, chapterIndex + 1)}</p>
            <h3>{selectedChapter?.title}</h3>
            <p>{selectedChapter?.summary}</p>
          </header>

          <div className="reader-grid">
            <section className="reader-card reader-card-morning">
              <h4>Morning</h4>
              <ul>
                {dayMoments.morning.map((activity) => (
                  <li key={activity.id}>{activity.title}</li>
                ))}
              </ul>
            </section>

            <section className="reader-card reader-card-afternoon">
              <h4>Afternoon</h4>
              <ul>
                {dayMoments.afternoon.map((activity) => (
                  <li key={activity.id}>{activity.title}</li>
                ))}
              </ul>
            </section>

            <section className="reader-card reader-card-evening">
              <h4>Evening</h4>
              <ul>
                {dayMoments.evening.map((activity) => (
                  <li key={activity.id}>{activity.title}</li>
                ))}
              </ul>
            </section>

            <section className="reader-card reader-card-restaurants">
              <h4>Restaurants</h4>
              <ul>
                {chapterRestaurants.map((restaurant) => (
                  <li key={restaurant.id}>{restaurant.name} • {restaurant.cuisine}</li>
                ))}
              </ul>
            </section>

            <section className="reader-card reader-card-activities">
              <h4>Activities</h4>
              <ul>
                {dayActivities.map((activity) => (
                  <li key={activity.id}>{activity.title} • {activity.location}</li>
                ))}
              </ul>
            </section>

            <section className="reader-card reader-card-transport">
              <h4>Transport</h4>
              <ul>
                {dayTransportation.map((leg) => (
                  <li key={leg.id}>{leg.mode} • {leg.from} to {leg.to}</li>
                ))}
              </ul>
            </section>

            <section className="reader-card reader-card-notes reader-card-wide">
              <h4>Notes</h4>
              <p>{selectedChapter?.summary}</p>
              {dayActivities.filter((activity) => activity.notes).map((activity) => (
                <p key={activity.id}>{activity.notes}</p>
              ))}
            </section>
          </div>
        </article>
      </section>

      <section className="dashboard-reference-grid">
        <article className="reference-card reference-card-hotel">
          <p className="reference-label">Hotel</p>
          <h4>{trip.hotel.name}</h4>
          <p>{trip.hotel.propertyType} • {trip.hotel.neighborhood}</p>
          <p>{trip.hotel.checkIn} to {trip.hotel.checkOut}</p>
          <p>{trip.hotel.rating} stars • {trip.budget.currency} {trip.hotel.pricePerNight.toLocaleString()} per night</p>
        </article>

        <article className="reference-card reference-card-restaurants">
          <p className="reference-label">Restaurants</p>
          <h4>Curated dining list</h4>
          <ul>
            {trip.restaurants.slice(0, 5).map((restaurant) => (
              <li key={restaurant.id}>{restaurant.name} • {restaurant.priceLevel}</li>
            ))}
          </ul>
        </article>

        <article className="reference-card reference-card-budget">
          <p className="reference-label">Budget</p>
          <h4>{trip.budget.currency} {trip.budget.estimatedSpend.toLocaleString()} estimated</h4>
          <p>Total: {trip.budget.currency} {trip.budget.totalBudget.toLocaleString()}</p>
          <p>Lodging {trip.budget.categories.lodging.toLocaleString()} • Food {trip.budget.categories.food.toLocaleString()}</p>
        </article>

        <article className="reference-card reference-card-packing">
          <p className="reference-label">Packing</p>
          <h4>Essentials</h4>
          <ul>
            {trip.packingList.slice(0, 6).map((item) => (
              <li key={item.id}>{item.name}{item.required ? ' • essential' : ''}</li>
            ))}
          </ul>
        </article>

        <article className="reference-card reference-card-weather">
          <p className="reference-label">Weather</p>
          <h4>{weatherForDay?.summary ?? 'Seasonal conditions expected'}</h4>
          <p>{weatherForDay?.temperatureHigh ?? '-'}°C / {weatherForDay?.temperatureLow ?? '-'}°C</p>
          <p>Precipitation chance: {weatherForDay?.precipitationChance ?? 0}%</p>
        </article>

        <article className="reference-card reference-card-tips">
          <p className="reference-label">Local Tips</p>
          <h4>Know before you go</h4>
          <ul>
            {trip.localTips.slice(0, 4).map((tip) => (
              <li key={tip.id}>{tip.title} • {tip.summary}</li>
            ))}
          </ul>
        </article>

        <article className="reference-card reference-card-emergency">
          <p className="reference-label">Emergency</p>
          <h4>{trip.emergencyInfo.contactName || 'Primary contact'}</h4>
          <p>{trip.emergencyInfo.contactPhone || 'Contact number unavailable'}</p>
          <p>Local emergency: {trip.emergencyInfo.localEmergencyNumber || 'Unavailable'}</p>
          {trip.emergencyInfo.medicalNote ? <p>{trip.emergencyInfo.medicalNote}</p> : null}
        </article>
      </section>
    </div>
  )
}
