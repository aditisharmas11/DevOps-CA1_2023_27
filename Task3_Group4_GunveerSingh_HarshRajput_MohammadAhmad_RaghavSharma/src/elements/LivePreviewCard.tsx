import type { Trip } from '../types/trip'

interface LivePreviewCardProps {
  trip: Trip | null
  destinationImage?: string
  destination: string
  duration: string
  travelStyle: string
  travelerType: string
  budget: string
}

export function LivePreviewCard({
  trip,
  destinationImage,
  destination,
  duration,
  travelStyle,
  travelerType,
  budget,
}: LivePreviewCardProps) {
  if (!trip) return null

  // Highlighted Activity
  const highlightedActivity =
    trip.itinerary[0]?.activities.find((a) => a.id.includes('activity-traveler') || a.id.includes('activity-style')) ??
    trip.itinerary[0]?.activities[0]

  // Primary Restaurant
  const primaryRestaurant = trip.restaurants[0]

  // Highlighted Local Tip
  const primaryTip = trip.localTips[0]

  return (
    <aside className="atlas-live-preview-card" aria-label="Live journey preview">
      {/* Header Badge */}
      <div className="atlas-preview-badge">
        <span className="atlas-pulse-dot" />
        Live Personalization Preview
      </div>

      {/* Destination Image & Hero */}
      <div className="atlas-preview-hero">
        {destinationImage ? (
          <img src={destinationImage} alt={`${destination} skyline`} className="atlas-preview-image" />
        ) : null}
        <div className="atlas-preview-hero-overlay" />
        <div className="atlas-preview-hero-text">
          <h3 className="atlas-preview-title">
            {destination}, <span className="atlas-preview-country">{trip.destination.country}</span>
          </h3>
          <p className="atlas-preview-kicker">{duration} • {travelerType} • {travelStyle}</p>
        </div>
      </div>

      {/* Compact Travel Tags */}
      <div className="atlas-preview-tags">
        <span className="atlas-tag">📍 {destination}</span>
        <span className="atlas-tag">⏱ {duration}</span>
        <span className="atlas-tag">👥 {travelerType}</span>
        <span className="atlas-tag">✨ {travelStyle}</span>
        <span className="atlas-tag">💰 {budget}</span>
      </div>

      {/* Main Content List */}
      <div className="atlas-preview-list">
        {/* Hotel Stay */}
        <div className="atlas-preview-row">
          <div className="atlas-row-header">
            <span className="atlas-row-icon">🏨</span>
            <span className="atlas-row-label">Hotel Stay</span>
          </div>
          <div className="atlas-row-body">
            <strong className="atlas-row-title">{trip.hotel.name}</strong>
            <p className="atlas-row-sub">
              {trip.hotel.propertyType.toUpperCase()} • Rating {trip.hotel.rating}⭐ • {trip.budget.currency} {trip.hotel.pricePerNight}/night
            </p>
          </div>
        </div>

        {/* Featured Restaurant */}
        {primaryRestaurant ? (
          <div className="atlas-preview-row">
            <div className="atlas-row-header">
              <span className="atlas-row-icon">🍽</span>
              <span className="atlas-row-label">Restaurant</span>
            </div>
            <div className="atlas-row-body">
              <strong className="atlas-row-title">{primaryRestaurant.name}</strong>
              <p className="atlas-row-sub">
                {primaryRestaurant.cuisine} • <span className="atlas-price-highlight">{primaryRestaurant.priceLevel.toUpperCase()}</span>
              </p>
            </div>
          </div>
        ) : null}

        {/* Highlighted Activity */}
        {highlightedActivity ? (
          <div className="atlas-preview-row">
            <div className="atlas-row-header">
              <span className="atlas-row-icon">🎯</span>
              <span className="atlas-row-label">Activity</span>
            </div>
            <div className="atlas-row-body">
              <strong className="atlas-row-title">{highlightedActivity.title}</strong>
              <p className="atlas-row-sub">{highlightedActivity.description}</p>
            </div>
          </div>
        ) : null}

        {/* Local Tip */}
        {primaryTip ? (
          <div className="atlas-preview-row atlas-preview-row-tip">
            <div className="atlas-row-header">
              <span className="atlas-row-icon">💡</span>
              <span className="atlas-row-label">Personalized Tip</span>
            </div>
            <div className="atlas-row-body">
              <strong className="atlas-row-title">{primaryTip.title}</strong>
              <p className="atlas-row-sub">{primaryTip.summary}</p>
            </div>
          </div>
        ) : null}
      </div>

      {/* Footer Budget Summary */}
      <div className="atlas-preview-footer">
        <div className="atlas-budget-summary">
          <span className="atlas-budget-label">Estimated Total Budget</span>
          <strong className="atlas-budget-value">{trip.budget.currency} {trip.budget.totalBudget.toLocaleString()}</strong>
        </div>
        <span className="atlas-preview-hint">Updates live</span>
      </div>
    </aside>
  )
}
