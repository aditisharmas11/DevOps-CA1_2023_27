import { createContext } from 'react'
import type { Trip } from '../types/trip'

export interface TripContextValue {
  currentTrip: Trip | null
  loading: boolean
  error: string | null
  generateTrip: (prompt: string) => Promise<void>
  clearTrip: () => void
}

export const TripContext = createContext<TripContextValue | undefined>(undefined)