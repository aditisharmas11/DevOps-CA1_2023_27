import type { Transportation, Trip } from '../../types/trip'
import type { PlannerBudget } from './types'
import { appendNote, createId } from './shared'

interface BudgetProfile {
  multiplier: number
  hotelScale: number
  restaurantPriceBias: 'budget' | 'mid' | 'luxury'
  transportModes: Transportation['mode'][]
  transportNote: string
  hotelNote: string
  restaurantNote: string
  hotelAmenities: string[]
}

const budgetProfiles: Record<PlannerBudget, BudgetProfile> = {
  Budget: {
    multiplier: 0.65,
    hotelScale: 0.6,
    restaurantPriceBias: 'budget',
    transportModes: ['train', 'walking', 'ferry'],
    transportNote: 'Budget mode: prioritize multi-day subway passes, walkable neighborhood routes, and shared transit.',
    hotelNote: 'Budget mode: selected for value, central location efficiency, and practical modern comfort.',
    restaurantNote: 'Budget mode: high-value local eateries and authentic casual dining spots.',
    hotelAmenities: ['Free High-Speed Wi-Fi', 'Express Self Check-in', 'Coffee Maker', 'Luggage Storage', 'Public Transit Access'],
  },
  'Mid-range': {
    multiplier: 1.0,
    hotelScale: 1.0,
    restaurantPriceBias: 'mid',
    transportModes: ['train', 'transfer', 'walking', 'car'],
    transportNote: 'Mid-range mode: balanced between express subway links and convenient taxi transfers.',
    hotelNote: 'Mid-range mode: stylish boutique hotel with balanced comfort and rooftop amenities.',
    restaurantNote: 'Mid-range mode: mix of popular local bistros and signature neighborhood dining.',
    hotelAmenities: ['Free Wi-Fi', 'Breakfast Buffet Included', 'Fitness Center', 'Rooftop Terrace', 'Concierge Desk', 'Cocktail Lounge'],
  },
  Luxury: {
    multiplier: 1.6,
    hotelScale: 1.8,
    restaurantPriceBias: 'luxury',
    transportModes: ['car', 'transfer'],
    transportNote: 'Luxury mode: private dedicated chauffeured luxury sedan service for all transfers.',
    hotelNote: 'Luxury mode: 5-star grand resort with 24/7 private butler and luxury spa suites.',
    restaurantNote: 'Luxury mode: chef table tasting menus with sommelier wine pairing and priority reservation.',
    hotelAmenities: ['24/7 Private Butler Service', 'Infinity Edge Pool', 'Michelin-Starred Dining', 'Full Luxury Spa', 'Private Chauffeured Transfer', 'Executive VIP Lounge'],
  },
}

function adjustPriceLevel(current: Trip['restaurants'][number]['priceLevel'], bias: BudgetProfile['restaurantPriceBias']): Trip['restaurants'][number]['priceLevel'] {
  if (bias === 'budget') {
    if (current === 'luxury') return 'high'
    if (current === 'high') return 'mid'
    return current === 'mid' ? 'budget' : current
  }

  if (bias === 'luxury') {
    if (current === 'budget') return 'mid'
    if (current === 'mid') return 'high'
    return current === 'high' ? 'luxury' : current
  }

  if (current === 'luxury') return 'high'
  if (current === 'budget') return 'mid'
  return current
}

function levelScore(level: Trip['restaurants'][number]['priceLevel']): number {
  if (level === 'budget') return 1
  if (level === 'mid') return 2
  if (level === 'high') return 3
  return 4
}

function createTransportTemplate(mode: Transportation['mode'], destination: string, note: string): Transportation {
  const from = `${destination} Central Hub`
  const to = mode === 'walking' ? `${destination} Historic District` : `${destination} Key Landmarks`

  return {
    id: createId('transport-budget'),
    mode,
    from,
    to,
    notes: note,
  }
}

export function applyBudget(trip: Trip, budget: PlannerBudget): Trip {
  const profile = budgetProfiles[budget]

  trip.budget.estimatedSpend = Math.round(trip.budget.estimatedSpend * profile.multiplier)
  trip.budget.totalBudget = Math.max(
    Math.round(trip.budget.estimatedSpend * 1.15),
    Math.round(trip.budget.totalBudget * profile.multiplier),
  )

  trip.budget.categories = {
    lodging: Math.round(trip.budget.categories.lodging * profile.multiplier),
    food: Math.round(trip.budget.categories.food * profile.multiplier),
    activities: Math.round(trip.budget.categories.activities * profile.multiplier),
    transportation: Math.round(trip.budget.categories.transportation * profile.multiplier),
    misc: Math.round(trip.budget.categories.misc * profile.multiplier),
  }

  trip.hotel = {
    ...trip.hotel,
    name:
      budget === 'Budget'
        ? `${trip.hotel.name} City Select`
        : budget === 'Luxury'
          ? `${trip.hotel.name} Grand Palace & Spa`
          : `${trip.hotel.name} Boutique Hotel`,
    propertyType:
      budget === 'Luxury'
        ? 'resort'
        : budget === 'Budget'
          ? 'hotel'
          : 'boutique',
    rating:
      budget === 'Budget'
        ? Math.max(3.9, Math.min(trip.hotel.rating, 4.3))
        : budget === 'Luxury'
          ? Math.min(5.0, Math.max(trip.hotel.rating, 4.8))
          : Math.max(4.3, Math.min(trip.hotel.rating, 4.7)),
    pricePerNight: Math.max(1, Math.round(trip.hotel.pricePerNight * profile.hotelScale)),
    amenities: profile.hotelAmenities,
  }

  trip.overview.summary = `${trip.overview.summary} Accommodation and dining configured for ${budget.toLowerCase()} budget preference.`

  trip.restaurants = trip.restaurants
    .map((restaurant) => {
      const adjustedPriceLevel = adjustPriceLevel(restaurant.priceLevel, profile.restaurantPriceBias)
      return {
        ...restaurant,
        priceLevel: adjustedPriceLevel,
        reservationRequired: budget === 'Luxury' ? true : restaurant.reservationRequired,
        notes: appendNote(restaurant.notes, profile.restaurantNote),
      }
    })
    .sort((left, right) => {
      const leftScore = levelScore(left.priceLevel)
      const rightScore = levelScore(right.priceLevel)
      return budget === 'Budget' ? leftScore - rightScore : rightScore - leftScore
    })

  const existingByMode = new Map(trip.transportation.map((segment) => [segment.mode, segment]))
  trip.transportation = profile.transportModes.map((mode) => {
    const existing = existingByMode.get(mode)
    if (!existing) {
      return createTransportTemplate(mode, trip.destination.name, profile.transportNote)
    }

    return {
      ...existing,
      notes: appendNote(existing.notes, profile.transportNote),
    }
  })

  trip.traveler.preferences.budgetRange =
    budget === 'Budget' ? 'economy' : budget === 'Luxury' ? 'luxury' : 'mid-range'
  trip.metadata.tags = Array.from(new Set([...trip.metadata.tags, budget.toLowerCase()]))

  return trip
}

