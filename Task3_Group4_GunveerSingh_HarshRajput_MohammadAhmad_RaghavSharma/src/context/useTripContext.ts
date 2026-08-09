import { useContext } from 'react'
import { TripContext } from './tripContext.shared'

export function useTripContext() {
  const context = useContext(TripContext)

  if (!context) {
    throw new Error('useTripContext must be used within a TripProvider')
  }

  return context
}
