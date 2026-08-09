export interface SimpleTravelPlanActivity {
  title?: string
  description?: string
  startTime?: string
  endTime?: string
  category?: string
  location?: string
  notes?: string
  priority?: string
  imageUrl?: string
}

export interface SimpleTravelPlanDay {
  dayNumber?: number
  date?: string
  title?: string
  summary?: string
  activities?: SimpleTravelPlanActivity[]
}

export interface SimpleTravelPlanRestaurant {
  name?: string
  cuisine?: string
  neighborhood?: string
  rating?: number
  priceLevel?: string
  reservationRequired?: boolean
  notes?: string
  websiteUrl?: string
}

export interface SimpleTravelPlanHotel {
  name?: string
  propertyType?: string
  neighborhood?: string
  checkIn?: string
  checkOut?: string
  rating?: number
  pricePerNight?: number
  amenities?: string[]
  bookingUrl?: string
}

export interface SimpleTravelPlanBudget {
  currency?: string
  totalBudget?: number
  estimatedSpend?: number
  categories?: {
    lodging?: number
    food?: number
    activities?: number
    transportation?: number
    misc?: number
  }
}

export interface SimpleTravelPlanWeather {
  date?: string
  summary?: string
  temperatureHigh?: number
  temperatureLow?: number
  precipitationChance?: number
  condition?: string
}

export interface SimpleTravelPlanPackingItem {
  name?: string
  category?: string
  packed?: boolean
  required?: boolean
  notes?: string
}

export interface SimpleTravelPlanTransportation {
  mode?: string
  from?: string
  to?: string
  departureTime?: string
  arrivalTime?: string
  bookingReference?: string
  notes?: string
}

export interface SimpleTravelPlanLocalTip {
  title?: string
  summary?: string
  category?: string
  priority?: string
}

export interface SimpleTravelPlanEmergencyInformation {
  contactName?: string
  contactPhone?: string
  embassyContact?: string
  medicalNote?: string
  localEmergencyNumber?: string
}

export interface SimpleTravelPlan {
  destination: string
  country: string
  durationDays: number
  travelStyle: string
  summary: string
  hotel?: SimpleTravelPlanHotel
  restaurants?: SimpleTravelPlanRestaurant[]
  itinerary?: SimpleTravelPlanDay[]
  budget?: SimpleTravelPlanBudget
  weather?: SimpleTravelPlanWeather[]
  packingList?: SimpleTravelPlanPackingItem[]
  transportation?: SimpleTravelPlanTransportation[]
  localTips?: SimpleTravelPlanLocalTip[]
  emergencyInfo?: SimpleTravelPlanEmergencyInformation
}
