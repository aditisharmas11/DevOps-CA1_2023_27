import type { Trip } from '../../types/trip'
import { placeholderTrip } from '../../lib/mockTrip'

interface CityTripConfig {
  cityKey: string
  destination: {
    id: string
    name: string
    country: string
    region: string
    timezone: string
    climateSummary: string
    bestSeason: string[]
    description: string
  }
  overview: {
    summary: string
    vibe: string
    startDate: string
    endDate: string
  }
}

export function createTripDataset(durationDays: number, config: CityTripConfig): Trip {
  return {
    ...placeholderTrip,
    id: `${config.cityKey}-${durationDays}-day`,
    title: `${config.destination.name} ${durationDays}-Day Journey`,
    slug: `${config.cityKey}-${durationDays}-day-journey`,
    destination: {
      ...placeholderTrip.destination,
      ...config.destination,
    },
    overview: {
      ...placeholderTrip.overview,
      ...config.overview,
      durationDays,
    },
    itinerary: placeholderTrip.itinerary.slice(0, Math.min(durationDays, placeholderTrip.itinerary.length)),
    metadata: {
      ...placeholderTrip.metadata,
      source: 'manual',
      tags: [config.cityKey, 'react-elements', 'local-dataset'],
    },
  }
}
