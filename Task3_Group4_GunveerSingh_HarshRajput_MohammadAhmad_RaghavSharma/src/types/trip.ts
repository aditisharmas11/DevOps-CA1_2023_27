export interface Traveler {
  id: string
  name: string
  email: string
  avatarUrl?: string
  preferences: {
    travelStyle: string[]
    pace: 'relaxed' | 'balanced' | 'active'
    budgetRange: 'economy' | 'mid-range' | 'luxury'
    interests: string[]
  }
}

export interface Destination {
  id: string
  name: string
  country: string
  region?: string
  latitude: number
  longitude: number
  timezone: string
  climateSummary: string
  bestSeason: string[]
  description: string
}

export interface Activity {
  id: string
  title: string
  description: string
  startTime?: string
  endTime?: string
  category: 'culture' | 'nature' | 'food' | 'wellness' | 'nightlife' | 'shopping' | 'adventure'
  location: string
  notes?: string
  imageUrl?: string
  priority: 'must' | 'nice-to-have' | 'optional'
}

export interface DailyItinerary {
  id: string
  dayNumber: number
  date: string
  title: string
  summary: string
  activities: Activity[]
}

export interface Restaurant {
  id: string
  name: string
  cuisine: string
  neighborhood: string
  rating: number
  priceLevel: 'budget' | 'mid' | 'high' | 'luxury'
  reservationRequired: boolean
  notes?: string
  websiteUrl?: string
}

export interface Hotel {
  id: string
  name: string
  propertyType: 'hotel' | 'resort' | 'apartment' | 'boutique'
  neighborhood: string
  checkIn: string
  checkOut: string
  rating: number
  pricePerNight: number
  amenities: string[]
  bookingUrl?: string
}

export interface Budget {
  id: string
  currency: string
  totalBudget: number
  estimatedSpend: number
  categories: {
    lodging: number
    food: number
    activities: number
    transportation: number
    misc: number
  }
}

export interface Weather {
  id: string
  destinationId: string
  date: string
  summary: string
  temperatureHigh: number
  temperatureLow: number
  precipitationChance: number
  condition: 'sunny' | 'cloudy' | 'rainy' | 'stormy' | 'windy' | 'mild'
}

export interface PackingItem {
  id: string
  name: string
  category: 'clothing' | 'documents' | 'tech' | 'toiletries' | 'health' | 'misc'
  packed: boolean
  required: boolean
  notes?: string
}

export interface EmergencyInfo {
  id: string
  contactName: string
  contactPhone: string
  embassyContact?: string
  medicalNote?: string
  localEmergencyNumber: string
}

export interface Transportation {
  id: string
  mode: 'flight' | 'train' | 'car' | 'ferry' | 'transfer' | 'walking'
  from: string
  to: string
  departureTime?: string
  arrivalTime?: string
  bookingReference?: string
  notes?: string
}

export interface LocalTip {
  id: string
  title: string
  summary: string
  category: 'culture' | 'practical' | 'food' | 'safety' | 'weather'
  priority: 'high' | 'medium' | 'low'
}

export interface Trip {
  id: string
  title: string
  slug: string
  travelerId: string
  createdAt: string
  updatedAt: string
  status: 'draft' | 'generated' | 'confirmed' | 'completed'
  destination: Destination
  traveler: Traveler
  overview: {
    summary: string
    vibe: string
    durationDays: number
    startDate: string
    endDate: string
  }
  itinerary: DailyItinerary[]
  hotel: Hotel
  restaurants: Restaurant[]
  budget: Budget
  weather: Weather[]
  packingList: PackingItem[]
  emergencyInfo: EmergencyInfo
  transportation: Transportation[]
  localTips: LocalTip[]
  metadata: {
    generatedFromPrompt: string
    source: 'ai' | 'manual' | 'imported'
    tags: string[]
  }
}
