import { useEffect, useMemo, useRef, useState } from 'react'
import { ConversationProvider, useConversation } from '@elevenlabs/react'
import './App.css'
import { getTripData } from './data'
import { buildPersonalizedTrip } from './lib/personalization'
import { LivePreviewCard } from './elements/LivePreviewCard'
import TripPage from './renderers/page/TripPage'
import TripEmail from './renderers/email/TripEmail'
import TripDocument from './renderers/document/TripDocument'
import type { Trip } from './types/trip'
import { exportTripEmailHtml, exportTripGuidePdf, exportTripWebsiteHtml } from './utils/export'

const destinationOptions = ['Tokyo', 'Dubai', 'Istanbul'] as const
const durationOptions = ['3 Days', '5 Days', '7 Days'] as const
const travelStyleOptions = ['Adventure', 'Luxury', 'Food', 'Culture', 'Nature', 'Romantic', 'Business'] as const
const budgetOptions = ['Budget', 'Mid-range', 'Luxury'] as const
const travelerOptions = ['Solo', 'Couple', 'Friends', 'Family'] as const
const renderModes = ['Website', 'Email', 'Travel Guide'] as const
const loadingTips = [
  'Scanning seasonal highlights and local pacing...',
  'Balancing culture, food, and comfort moments...',
  'Sequencing mornings, afternoons, and evenings...',
  'Refining stays, dining, and transport details...',
] as const

const destinationVisuals: Record<string, { image: string; language: string }> = {
  Tokyo: {
    image: 'https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=1800&q=80',
    language: 'Japanese',
  },
  Dubai: {
    image: 'https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=1800&q=80',
    language: 'Arabic',
  },
  Istanbul: {
    image: 'https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?auto=format&fit=crop&w=1800&q=80',
    language: 'Turkish',
  },
}

const conciergeAgentId = 'agent_7201ky9sns2jegxtrys4fxhz3kpd'

function AtlasConciergeSection() {
  const conversation = useConversation()
  const [isOpen, setIsOpen] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [lastSignal, setLastSignal] = useState('Ready to assist with your journey.')

  const isConnected = conversation.status === 'connected'

  const handleStartConversation = async () => {
    try {
      setErrorMessage(null)
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      stream.getTracks().forEach((track) => track.stop())

      conversation.startSession({
        agentId: conciergeAgentId,
        connectionType: 'webrtc',
        onConnect: () => {
          setLastSignal('Connected to Atlas Concierge.')
        },
        onDisconnect: () => {
          setLastSignal('Session ended. You can start a new conversation anytime.')
        },
        onMessage: () => {
          setLastSignal('Atlas exchanged a message in this conversation.')
        },
        onError: (error) => {
          const message = typeof error === 'string'
            ? error
            : 'An unexpected voice connection issue occurred.'
          setErrorMessage(message)
        },
        onModeChange: (mode) => {
          setLastSignal(mode.mode === 'speaking' ? 'Atlas is speaking.' : 'Atlas is listening.')
        },
      })
    } catch {
      setErrorMessage('Microphone access is required to start the voice assistant.')
    }
  }

  const handleEndConversation = () => {
    conversation.endSession()
  }

  return (
    <aside className="atlas-floating-assistant" aria-label="Atlas AI Assistant">
      {isOpen && (
        <div className="atlas-assistant-panel" aria-live="polite">
          <div className="atlas-assistant-header">
            <div className="atlas-assistant-title-group">
              <span className="atlas-assistant-sparkle">✨</span>
              <div>
                <h4>Atlas AI Concierge</h4>
                <p className="atlas-assistant-status">
                  <span className={`atlas-status-dot${isConnected ? ' is-connected' : ''}`} />
                  {conversation.status}
                </p>
              </div>
            </div>
            <button
              type="button"
              className="atlas-assistant-close"
              onClick={() => setIsOpen(false)}
              aria-label="Close assistant panel"
            >
              ✕
            </button>
          </div>

          <div className="atlas-assistant-body">
            <div className={`atlas-concierge-mic-wrap${isConnected ? ' is-connected' : ''}${conversation.isListening ? ' is-listening' : ''}${conversation.isSpeaking ? ' is-speaking' : ''}`}>
              <div className="atlas-concierge-ring" aria-hidden="true" />
              <div className="atlas-concierge-icon" aria-hidden="true">🎙</div>
              <div className="atlas-concierge-bars" aria-hidden="true">
                <span />
                <span />
                <span />
                <span />
              </div>
            </div>

            <p className="atlas-assistant-prompt">
              Speak naturally to ask about destinations, itineraries, budgets, and travel styles.
            </p>

            <div className="atlas-assistant-signal">
              {errorMessage ?? lastSignal}
            </div>

            <div className="atlas-assistant-meta-grid">
              <div><span>Listening</span><strong>{conversation.isListening ? 'Yes' : 'No'}</strong></div>
              <div><span>Speaking</span><strong>{conversation.isSpeaking ? 'Yes' : 'No'}</strong></div>
            </div>
          </div>

          <div className="atlas-assistant-footer">
            <button
              type="button"
              className="atlas-concierge-button"
              onClick={handleStartConversation}
              disabled={isConnected || conversation.status === 'connecting'}
            >
              Start Conversation
            </button>
            <button
              type="button"
              className="atlas-concierge-button atlas-concierge-button--ghost"
              onClick={handleEndConversation}
              disabled={!isConnected && conversation.status !== 'connecting'}
            >
              End Session
            </button>
          </div>
        </div>
      )}

      {/* Floating Trigger Button */}
      <button
        type="button"
        className={`atlas-assistant-trigger${isOpen ? ' is-active' : ''}${isConnected ? ' is-connected' : ''}`}
        onClick={() => setIsOpen((prev) => !prev)}
        aria-label="Toggle Atlas AI Concierge"
      >
        <span className="atlas-trigger-glow" />
        <span className="atlas-trigger-icon">🎙</span>
        <span className="atlas-trigger-label">Atlas AI</span>
      </button>
    </aside>
  )
}

export default function App() {
  const [destination, setDestination] = useState<(typeof destinationOptions)[number]>('Tokyo')
  const [duration, setDuration] = useState<(typeof durationOptions)[number]>('7 Days')
  const [travelStyle, setTravelStyle] = useState<(typeof travelStyleOptions)[number]>('Luxury')
  const [budget, setBudget] = useState<(typeof budgetOptions)[number]>('Mid-range')
  const [travelers, setTravelers] = useState<(typeof travelerOptions)[number]>('Couple')
  const [activeRenderMode, setActiveRenderMode] = useState<(typeof renderModes)[number]>('Website')
  const [generatedTrip, setGeneratedTrip] = useState<Trip | null>(null)
  const [hasDataset, setHasDataset] = useState(false)
  const [isDesigning, setIsDesigning] = useState(false)
  const [showResult, setShowResult] = useState(false)
  const [loadingTipIndex, setLoadingTipIndex] = useState(0)
  const [generatedAt, setGeneratedAt] = useState<Date | null>(null)
  const resultSectionRef = useRef<HTMLElement | null>(null)

  const livePreviewTrip = useMemo(() => {
    const baseTrip = getTripData(destination, duration)
    if (!baseTrip) return null
    return buildPersonalizedTrip(baseTrip, {
      travelerType: travelers,
      travelStyle,
      budget,
    })
  }, [destination, duration, travelers, travelStyle, budget])

  useEffect(() => {
    if (!isDesigning) {
      return
    }

    const timeout = window.setTimeout(() => {
      setIsDesigning(false)
      setShowResult(true)
    }, 1500)

    return () => {
      window.clearTimeout(timeout)
    }
  }, [isDesigning])

  useEffect(() => {
    if (!isDesigning) {
      setLoadingTipIndex(0)
      return
    }

    const interval = window.setInterval(() => {
      setLoadingTipIndex((current) => (current + 1) % loadingTips.length)
    }, 1150)

    return () => {
      window.clearInterval(interval)
    }
  }, [isDesigning])

  useEffect(() => {
    if (!showResult) return
    resultSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [showResult])

  const handleDesignJourney = () => {
    const baseTrip = getTripData(destination, duration)
    const trip = baseTrip
      ? buildPersonalizedTrip(baseTrip, {
        travelerType: travelers,
        travelStyle,
        budget,
      })
      : null

    setShowResult(false)
    setActiveRenderMode('Website')
    setGeneratedTrip(trip)
    setGeneratedAt(new Date())
    setHasDataset(Boolean(trip))
    setIsDesigning(true)
    // Local trip JSON injection point for the challenge data set.
  }

  const activeRenderer = () => {
    if (!generatedTrip) {
      return null
    }

    if (activeRenderMode === 'Email') {
      return <TripEmail trip={generatedTrip} />
    }

    if (activeRenderMode === 'Travel Guide') {
      return <TripDocument trip={generatedTrip} />
    }

    return <TripPage trip={generatedTrip} />
  }

  const bestSeason = generatedTrip?.destination.bestSeason.slice(0, 3).join(' • ') ?? 'TBD'
  const destinationVisual = generatedTrip ? destinationVisuals[generatedTrip.destination.name] : null
  const generationTimestamp = generatedAt
    ? generatedAt.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    })
    : 'Pending generation'
  const weatherNow = generatedTrip?.weather[0] ?? null
  const perDayEstimate = generatedTrip
    ? Math.round(generatedTrip.budget.estimatedSpend / Math.max(generatedTrip.overview.durationDays, 1))
    : 0

  const summaryCards = generatedTrip
    ? [
      {
        icon: '🗓',
        title: 'Duration',
        value: `${generatedTrip.overview.durationDays} days`,
        description: 'Balanced across morning, afternoon, and evening pacing.',
      },
      {
        icon: '💳',
        title: 'Budget',
        value: `${generatedTrip.budget.currency} ${generatedTrip.budget.totalBudget.toLocaleString()}`,
        description: `Estimated spend ${generatedTrip.budget.currency} ${generatedTrip.budget.estimatedSpend.toLocaleString()}.`,
      },
      {
        icon: '🧭',
        title: 'Travel Style',
        value: travelStyle,
        description: 'Curated to match your selected journey mood and cadence.',
      },
      {
        icon: '☀️',
        title: 'Best Season',
        value: bestSeason,
        description: 'Top seasonal windows for weather and city atmosphere.',
      },
      {
        icon: '💱',
        title: 'Currency',
        value: generatedTrip.budget.currency,
        description: 'Primary planning currency used across this itinerary.',
      },
      {
        icon: '🗣',
        title: 'Language',
        value: destinationVisual?.language ?? 'Local language',
        description: 'Helpful for signs, restaurants, and local interactions.',
      },
      {
        icon: '🌤',
        title: 'Weather',
        value: weatherNow
          ? `${weatherNow.temperatureHigh}° / ${weatherNow.temperatureLow}°`
          : 'Weather unavailable',
        description: weatherNow?.summary ?? 'Forecast updates will appear when available.',
      },
      {
        icon: '🕒',
        title: 'Timezone',
        value: generatedTrip.destination.timezone,
        description: 'Aligned for transfers, reservations, and schedule comfort.',
      },
    ]
    : []

  const itineraryDays = generatedTrip?.itinerary ?? []

  const handleExportHtml = () => {
    if (!generatedTrip) return
    exportTripWebsiteHtml(generatedTrip)
  }

  const handleExportEmail = () => {
    if (!generatedTrip) return
    exportTripEmailHtml(generatedTrip)
  }

  const handleExportPdf = () => {
    if (!generatedTrip) return
    exportTripGuidePdf(generatedTrip)
  }

  return (
    <main className={`atlas-onepage${isDesigning ? ' is-designing' : ''}`}>
      <section className="atlas-onepage-hero">
        <div className="atlas-onepage-hero-overlay" />
        <div className="atlas-onepage-content">
          <p className="atlas-onepage-kicker">Atlas React Elements Challenge</p>
          <h1 className="atlas-onepage-title">Design Your Next Journey</h1>
          <p className="atlas-onepage-subtitle">One trip. Three beautiful render targets.</p>

          <div className="atlas-hero-planner-layout">
            <form
              className={`atlas-planner-card${isDesigning ? ' is-loading' : ''}`}
              onSubmit={(event) => {
                event.preventDefault()
                handleDesignJourney()
              }}
            >
              {/* ── Card Header ── */}
              <div className="atlas-planner-header">
                <div className="atlas-planner-header-top">
                  <span className="atlas-planner-compass" aria-hidden="true">🧭</span>
                  <span className="atlas-planner-label">Plan Your Journey</span>
                </div>
                <div className="atlas-planner-divider" aria-hidden="true" />
              </div>

              {/* ── Form Fields ── */}
              <div className="atlas-planner-fields">
                {/* Destination – full width */}
                <label className="atlas-field atlas-field-wide">
                  <span><span className="atlas-field-icon">📍</span> Destination</span>
                  <select value={destination} onChange={(event) => setDestination(event.target.value as (typeof destinationOptions)[number])}>
                    {destinationOptions.map((option) => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                </label>

                {/* Row 2: Duration | Travel Style */}
                <label className="atlas-field">
                  <span><span className="atlas-field-icon">📅</span> Duration</span>
                  <select value={duration} onChange={(event) => setDuration(event.target.value as (typeof durationOptions)[number])}>
                    {durationOptions.map((option) => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                </label>

                <label className="atlas-field">
                  <span><span className="atlas-field-icon">✨</span> Travel Style</span>
                  <select value={travelStyle} onChange={(event) => setTravelStyle(event.target.value as (typeof travelStyleOptions)[number])}>
                    {travelStyleOptions.map((option) => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                </label>

                {/* Row 3: Budget | Travellers */}
                <label className="atlas-field">
                  <span><span className="atlas-field-icon">💰</span> Budget</span>
                  <select value={budget} onChange={(event) => setBudget(event.target.value as (typeof budgetOptions)[number])}>
                    {budgetOptions.map((option) => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                </label>

                <label className="atlas-field">
                  <span><span className="atlas-field-icon">👥</span> Travellers</span>
                  <select value={travelers} onChange={(event) => setTravelers(event.target.value as (typeof travelerOptions)[number])}>
                    {travelerOptions.map((option) => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                </label>
              </div>

              {/* ── Live Selection Summary ── */}
              <div className="atlas-planner-summary" aria-label="Your current selections">
                <p className="atlas-planner-summary-label">Your Selections</p>
                <div className="atlas-planner-chips">
                  <span className="atlas-tag">📍 {destination}</span>
                  <span className="atlas-tag">📅 {duration}</span>
                  <span className="atlas-tag">👥 {travelers}</span>
                  <span className="atlas-tag">✨ {travelStyle}</span>
                  <span className="atlas-tag">💰 {budget}</span>
                </div>
              </div>

              {/* ── CTA ── */}
              <div className="atlas-planner-cta-wrap">
                <button type="submit" className="atlas-design-button" disabled={isDesigning}>
                  {isDesigning ? (
                    <>
                      <span className="atlas-btn-icon">⏳</span>
                      Designing your journey...
                    </>
                  ) : (
                    <>
                      <span className="atlas-btn-icon">✦</span>
                      Design My Journey
                      <span className="atlas-btn-arrow">→</span>
                    </>
                  )}
                </button>
                <p className="atlas-planner-footer-note">🔒 No sign up required · Free to create</p>
              </div>
            </form>


            <LivePreviewCard
              trip={livePreviewTrip}
              destinationImage={destinationVisuals[destination]?.image}
              destination={destination}
              duration={duration}
              travelStyle={travelStyle}
              travelerType={travelers}
              budget={budget}
            />
          </div>

          {isDesigning ? (
            <div className="atlas-loading" aria-live="polite">
              <div className="atlas-loading-line" aria-hidden="true">
                <span className="atlas-loading-line-fill" />
              </div>
              <div className="atlas-loading-message">
                <span className="atlas-loading-dot" />
                <span className="atlas-loading-dot" />
                <span className="atlas-loading-dot" />
                <p>{loadingTips[loadingTipIndex]}</p>
              </div>
            </div>
          ) : null}
        </div>
      </section>

      <section ref={resultSectionRef} className={`atlas-result ${showResult ? 'is-visible' : ''}`}>
        <div className="atlas-result-content">
          {!hasDataset ? (
            <section className="atlas-dataset-placeholder" aria-live="polite">
              <p className="atlas-result-kicker">Atlas Local Data</p>
              <h2>Destination dataset coming soon.</h2>
              <p>
                We only support Tokyo, Dubai, and Istanbul in local dataset mode.
              </p>
            </section>
          ) : (
            <>
              <section className="atlas-generated-hero">
                <div className="atlas-generated-hero-media" aria-hidden="true">
                  {destinationVisual ? <img src={destinationVisual.image} alt={`${generatedTrip?.destination.name} destination view`} /> : null}
                  <div className="atlas-generated-hero-glow" />
                </div>
                <div className="atlas-generated-hero-content">
                  <p className="atlas-result-kicker">Generated by Atlas</p>
                  <h2>{generatedTrip?.destination.name}, {generatedTrip?.destination.country}</h2>
                  <p>{generatedTrip?.overview.summary}</p>
                  <div className="atlas-generated-meta">
                    <span>{duration}</span>
                    <span>{travelStyle}</span>
                    <span>{budget}</span>
                    <span>{travelers}</span>
                    <span>{generationTimestamp}</span>
                  </div>
                </div>
              </section>

              <section className="atlas-section-divider" aria-label="Journey overview">
                <p className="atlas-result-kicker">Journey Overview</p>
                <h3>{generatedTrip?.overview.vibe}</h3>
              </section>

              <section className="atlas-result-facts" aria-label="Journey summary cards">
                {summaryCards.map((card) => (
                  <article key={card.title}>
                    <p className="atlas-fact-icon" aria-hidden="true">{card.icon}</p>
                    <span>{card.title}</span>
                    <strong>{card.value}</strong>
                    <small>{card.description}</small>
                  </article>
                ))}
              </section>

              <section className="atlas-section-divider" aria-label="Daily itinerary">
                <p className="atlas-result-kicker">Daily Itinerary</p>
                <h3>Day-by-day generated timeline</h3>
              </section>

              <section className="atlas-itinerary" aria-label="Generated itinerary timeline">
                {itineraryDays.length ? itineraryDays.map((day, index) => {
                  const morning = day.activities[0]
                  const afternoon = day.activities[1]
                  const evening = day.activities[2]
                  const restaurant = generatedTrip?.restaurants[index % (generatedTrip?.restaurants.length || 1)]
                  const transport = generatedTrip?.transportation[index % (generatedTrip?.transportation.length || 1)]
                  return (
                    <article key={day.id} className="atlas-day-card">
                      <div className="atlas-day-card-head">
                        <p className="atlas-result-kicker">Day {day.dayNumber}</p>
                        <h4>{day.title}</h4>
                        <p>{day.summary}</p>
                      </div>
                      <div className="atlas-day-card-grid">
                        <section>
                          <span>Morning</span>
                          <p>{morning?.title ?? 'Morning details coming soon.'}</p>
                        </section>
                        <section>
                          <span>Afternoon</span>
                          <p>{afternoon?.title ?? 'Afternoon details coming soon.'}</p>
                        </section>
                        <section>
                          <span>Evening</span>
                          <p>{evening?.title ?? 'Evening details coming soon.'}</p>
                        </section>
                        <section>
                          <span>Restaurant</span>
                          <p>{restaurant?.name ?? 'Restaurant recommendation coming soon.'}</p>
                        </section>
                        <section>
                          <span>Transportation</span>
                          <p>{transport ? `${transport.mode.toUpperCase()} · ${transport.from} to ${transport.to}` : 'Transport details coming soon.'}</p>
                        </section>
                        <section>
                          <span>Estimated Spend</span>
                          <p>{generatedTrip?.budget.currency} {perDayEstimate.toLocaleString()}</p>
                        </section>
                        <section>
                          <span>Highlights</span>
                          <p>{day.activities.slice(0, 2).map((activity) => activity.title).join(' · ') || 'Highlights coming soon.'}</p>
                        </section>
                        <section>
                          <span>Notes</span>
                          <p>{day.activities.find((activity) => activity.notes)?.notes ?? 'Local notes and practical guidance will appear here.'}</p>
                        </section>
                      </div>
                    </article>
                  )
                }) : (
                  <article className="atlas-day-card atlas-day-card-placeholder">
                    <p>Itinerary is being prepared. Day cards will appear here when journey data is ready.</p>
                  </article>
                )}
              </section>

              <section className="atlas-section-divider" aria-label="Accommodation and dining">
                <p className="atlas-result-kicker">Accommodation and Dining</p>
                <h3>Stay and food recommendations</h3>
              </section>

              <section className="atlas-secondary-grid" aria-label="Accommodation and dining cards">
                <article className="atlas-secondary-card">
                  <p className="atlas-result-kicker">Accommodation</p>
                  <h4>{generatedTrip?.hotel.name ?? 'Hotel details pending'}</h4>
                  <p>{generatedTrip ? `${generatedTrip.hotel.propertyType} in ${generatedTrip.hotel.neighborhood}` : 'Your stay details will appear here.'}</p>
                </article>
                <article className="atlas-secondary-card">
                  <p className="atlas-result-kicker">Dining</p>
                  <h4>{generatedTrip?.restaurants[0]?.name ?? 'Restaurant details pending'}</h4>
                  <p>{generatedTrip?.restaurants[0] ? `${generatedTrip.restaurants[0].cuisine} · ${generatedTrip.restaurants[0].neighborhood}` : 'Dining highlights will appear here.'}</p>
                </article>
                <article className="atlas-secondary-card">
                  <p className="atlas-result-kicker">Budget</p>
                  <h4>{generatedTrip ? `${generatedTrip.budget.currency} ${generatedTrip.budget.estimatedSpend.toLocaleString()}` : 'Budget details pending'}</h4>
                  <p>{generatedTrip ? 'Estimated journey spend across stays, dining, and activities.' : 'Budget guidance will appear here.'}</p>
                </article>
                <article className="atlas-secondary-card">
                  <p className="atlas-result-kicker">Emergency</p>
                  <h4>{generatedTrip?.emergencyInfo.localEmergencyNumber ?? 'Emergency details pending'}</h4>
                  <p>{generatedTrip?.emergencyInfo.contactName ?? 'Safety contacts and local support information will appear here.'}</p>
                </article>
              </section>

              <section className="atlas-render-panel" aria-label="Render target preview">
                <div className="atlas-render-tabs" role="tablist" aria-label="Render target">
                  {renderModes.map((mode) => {
                    const isActive = mode === activeRenderMode
                    return (
                      <button
                        key={mode}
                        type="button"
                        role="tab"
                        aria-selected={isActive}
                        className={`atlas-render-tab${isActive ? ' is-active' : ''}`}
                        onClick={() => setActiveRenderMode(mode)}
                      >
                        {mode}
                      </button>
                    )
                  })}
                </div>

                <div className="preview-export-actions" aria-label="Export current trip">
                  <button
                    type="button"
                    className="preview-export-button"
                    onClick={handleExportHtml}
                    disabled={!generatedTrip}
                  >
                    Export HTML
                  </button>
                  <button
                    type="button"
                    className="preview-export-button"
                    onClick={handleExportEmail}
                    disabled={!generatedTrip}
                  >
                    Export Email
                  </button>
                  <button
                    type="button"
                    className="preview-export-button"
                    onClick={handleExportPdf}
                    disabled={!generatedTrip}
                  >
                    Export PDF
                  </button>
                </div>

                <div className="atlas-render-surface">
                  {activeRenderer()}
                </div>
              </section>
            </>
          )}
        </div>
      </section>

      <ConversationProvider agentId={conciergeAgentId}>
        <AtlasConciergeSection />
      </ConversationProvider>
    </main>
  )
}
