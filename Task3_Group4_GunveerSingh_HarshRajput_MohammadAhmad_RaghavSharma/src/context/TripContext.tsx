import { useCallback, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { generateTrip as generateTripService } from '../services/tripService'
import { TripContext, type TripContextValue } from './tripContext.shared'
import type { Trip } from '../types/trip'

export function TripProvider({ children }: { children: ReactNode }) {
  const [currentTrip, setCurrentTrip] = useState<Trip | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const generateTrip = useCallback(async (prompt: string) => {
    const trimmedPrompt = prompt.trim()

    if (!trimmedPrompt) {
      setError('Please describe the kind of journey you want to create.')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const trip = await generateTripService(trimmedPrompt)
      setCurrentTrip(trip)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create a journey right now.')
      setCurrentTrip(null)
    } finally {
      setLoading(false)
    }
  }, [])

  const clearTrip = useCallback(() => {
    setCurrentTrip(null)
    setError(null)
  }, [])

  const value = useMemo<TripContextValue>(
    () => ({ currentTrip, loading, error, generateTrip, clearTrip }),
    [currentTrip, loading, error, generateTrip, clearTrip],
  )

  return <TripContext.Provider value={value}>{children}</TripContext.Provider>
}
