import { useMemo, useState } from 'react'
import { useTripContext } from '../context/useTripContext'
import TripPage from '../renderers/page/TripPage'
import TripEmail from '../renderers/email/TripEmail'
import TripDocument from '../renderers/document/TripDocument'
import { placeholderTrip } from '../lib/mockTrip'
import { exportTripEmailHtml, exportTripGuidePdf, exportTripWebsiteHtml } from '../utils/export'

const modes = [
  { id: 'website', label: 'Website', component: TripPage },
  { id: 'email', label: 'Email', component: TripEmail },
  { id: 'document', label: 'Travel Guide', component: TripDocument },
] as const

export default function RenderPreviewPage() {
  const { currentTrip, error, loading } = useTripContext()
  const [activeMode, setActiveMode] = useState<(typeof modes)[number]['id']>('website')
  const trip = currentTrip ?? placeholderTrip
  const isDemoMode = !currentTrip
  const travelerLabel = `1 (${trip.traveler.name})`

  const activeModeConfig = useMemo(
    () => modes.find((mode) => mode.id === activeMode) ?? modes[0],
    [activeMode],
  )

  const ActiveComponent = activeModeConfig.component

  const handleExportHtml = () => {
    exportTripWebsiteHtml(trip)
  }

  const handleExportEmail = () => {
    exportTripEmailHtml(trip)
  }

  const handleExportPdf = () => {
    exportTripGuidePdf(trip)
  }

  return (
    <main className="preview-page">
      <div className="preview-shell">
        <section className="preview-hero">
          <div className="preview-header">
            <div>
              <p className="preview-kicker">React Elements Challenge</p>
              <h1 className="preview-title">Build Once. Render Everywhere.</h1>
              <p className="preview-card-copy">
                A single Trip object is transformed into three distinct experiences using React Elements: web page, email layout, and printable travel guide.
              </p>
            </div>
            {isDemoMode ? <span className="preview-mode-button is-active">Demo Mode</span> : null}
          </div>

          <div className="preview-pipeline" aria-label="React Elements pipeline overview">
            <p className="preview-pipeline-top">AI Trip</p>
            <p className="preview-pipeline-arrow">↓</p>
            <p className="preview-pipeline-bottom">Website • Email • Travel Guide</p>
          </div>

          <div className="preview-info-panel">
            <article className="preview-info-item">
              <span>Destination</span>
              <strong>{trip.destination.name}</strong>
            </article>
            <article className="preview-info-item">
              <span>Duration</span>
              <strong>{trip.overview.durationDays} days</strong>
            </article>
            <article className="preview-info-item">
              <span>Budget</span>
              <strong>{trip.budget.currency} {trip.budget.totalBudget.toLocaleString()}</strong>
            </article>
            <article className="preview-info-item">
              <span>Travelers</span>
              <strong>{travelerLabel}</strong>
            </article>
            <article className="preview-info-item">
              <span>Demo Mode</span>
              <strong>{isDemoMode ? 'On' : 'Off'}</strong>
            </article>
          </div>

          <div className="preview-segmented" role="tablist" aria-label="Render targets">
            {modes.map((mode) => {
              const isActive = mode.id === activeMode
              return (
                <button
                  key={mode.id}
                  type="button"
                  role="tab"
                  aria-selected={isActive}
                  onClick={() => setActiveMode(mode.id)}
                  className={`preview-segmented-button${isActive ? ' is-active' : ''}`}
                >
                  {mode.label}
                </button>
              )
            })}
          </div>
        </section>

        <>
          {(loading || error) ? (
            <div className="preview-card">
              <p className="preview-card-heading">Atlas preview</p>
              <h2 className="preview-card-title">{loading ? 'Preparing your generated journey.' : 'Using available trip data.'}</h2>
              <p className="preview-card-copy">{error ? error : 'A trip preview is still shown below using the active shared Trip object.'}</p>
            </div>
          ) : null}

          <section className="preview-card">
            <p className="preview-card-heading">{activeModeConfig.label}</p>
            <div className="preview-card--status">
              <ActiveComponent trip={trip} />
            </div>
          </section>

          <section className="preview-export" aria-label="Export options">
            <p className="preview-card-heading">Export</p>
            <div className="preview-export-actions">
              <button type="button" className="preview-export-button" onClick={handleExportHtml}>Export HTML</button>
              <button type="button" className="preview-export-button" onClick={handleExportEmail}>Export Email</button>
              <button type="button" className="preview-export-button" onClick={handleExportPdf}>Export PDF</button>
            </div>
            <p className="preview-export-note">All three outputs are rendered from the exact same Trip object.</p>
          </section>
        </>
      </div>
    </main>
  )
}
