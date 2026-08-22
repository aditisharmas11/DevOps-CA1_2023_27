import type {
  Activity,
  DailyItinerary,
  LocalTip,
  PackingItem,
  Restaurant,
  Transportation,
  Trip,
  Weather,
} from '../../../src/types/trip.js'
import type {
  SimpleTravelPlan,
  SimpleTravelPlanActivity,
  SimpleTravelPlanBudget,
  SimpleTravelPlanDay,
  SimpleTravelPlanEmergencyInformation,
  SimpleTravelPlanHotel,
  SimpleTravelPlanLocalTip,
  SimpleTravelPlanPackingItem,
  SimpleTravelPlanRestaurant,
  SimpleTravelPlanTransportation,
  SimpleTravelPlanWeather,
} from '../types/simpleTravelPlan.js'

const VALID_ACTIVITY_CATEGORIES = new Set<Activity['category']>([
  'culture',
  'nature',
  'food',
  'wellness',
  'nightlife',
  'shopping',
  'adventure',
])

const VALID_ACTIVITY_PRIORITIES = new Set<Activity['priority']>(['must', 'nice-to-have', 'optional'])

const VALID_PRICE_LEVELS = new Set<Restaurant['priceLevel']>(['budget', 'mid', 'high', 'luxury'])
const VALID_WEATHER_CONDITIONS = new Set<Weather['condition']>(['sunny', 'cloudy', 'rainy', 'stormy', 'windy', 'mild'])
const VALID_PACKING_CATEGORIES = new Set<PackingItem['category']>(['clothing', 'documents', 'tech', 'toiletries', 'health', 'misc'])
const VALID_TRANSPORT_MODES = new Set<Transportation['mode']>(['flight', 'train', 'car', 'ferry', 'transfer', 'walking'])
const VALID_TIP_CATEGORIES = new Set<LocalTip['category']>(['culture', 'practical', 'food', 'safety', 'weather'])
const VALID_TIP_PRIORITIES = new Set<LocalTip['priority']>(['high', 'medium', 'low'])

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' ? (value as Record<string, unknown>) : {}
}

function getString(value: unknown, fallback = ''): string {
  return typeof value === 'string' && value.trim() ? value.trim() : fallback
}

function getNumber(value: unknown, fallback = 0): number {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value
  }

  if (typeof value === 'string') {
    const parsed = Number(value)
    if (Number.isFinite(parsed)) {
      return parsed
    }
  }

  return fallback
}

function getBoolean(value: unknown, fallback = false): boolean {
  return typeof value === 'boolean' ? value : fallback
}

function getStringArray(value: unknown, fallback: string[] = []): string[] {
  if (!Array.isArray(value)) {
    return fallback
  }

  const mapped = value
    .map((entry) => getString(entry))
    .filter((entry) => entry.length > 0)

  return mapped.length > 0 ? mapped : fallback
}

function normalizeSlug(input: string): string {
  const slug = input
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')

  return slug || 'trip'
}

function toIsoDate(date: Date): string {
  return date.toISOString().slice(0, 10)
}

function addDays(baseDate: Date, days: number): Date {
  const copy = new Date(baseDate)
  copy.setUTCDate(copy.getUTCDate() + days)
  return copy
}

function normalizeTravelStyle(value: unknown): string {
  const style = getString(value, 'balanced')
  return style || 'balanced'
}

function normalizeActivityCategory(value: unknown): Activity['category'] {
  const category = getString(value).toLowerCase()
  return VALID_ACTIVITY_CATEGORIES.has(category as Activity['category']) ? (category as Activity['category']) : 'culture'
}

function normalizeActivityPriority(value: unknown): Activity['priority'] {
  const priority = getString(value).toLowerCase()
  return VALID_ACTIVITY_PRIORITIES.has(priority as Activity['priority']) ? (priority as Activity['priority']) : 'must'
}

function normalizePriceLevel(value: unknown): Restaurant['priceLevel'] {
  const priceLevel = getString(value).toLowerCase()
  return VALID_PRICE_LEVELS.has(priceLevel as Restaurant['priceLevel']) ? (priceLevel as Restaurant['priceLevel']) : 'mid'
}

function normalizeWeatherCondition(value: unknown): Weather['condition'] {
  const condition = getString(value).toLowerCase()
  return VALID_WEATHER_CONDITIONS.has(condition as Weather['condition']) ? (condition as Weather['condition']) : 'mild'
}

function normalizePackingCategory(value: unknown): PackingItem['category'] {
  const category = getString(value).toLowerCase()
  return VALID_PACKING_CATEGORIES.has(category as PackingItem['category']) ? (category as PackingItem['category']) : 'misc'
}

function normalizeTransportMode(value: unknown): Transportation['mode'] {
  const mode = getString(value).toLowerCase()
  return VALID_TRANSPORT_MODES.has(mode as Transportation['mode']) ? (mode as Transportation['mode']) : 'transfer'
}

function normalizeTipCategory(value: unknown): LocalTip['category'] {
  const category = getString(value).toLowerCase()
  return VALID_TIP_CATEGORIES.has(category as LocalTip['category']) ? (category as LocalTip['category']) : 'practical'
}

function normalizeTipPriority(value: unknown): LocalTip['priority'] {
  const priority = getString(value).toLowerCase()
  return VALID_TIP_PRIORITIES.has(priority as LocalTip['priority']) ? (priority as LocalTip['priority']) : 'medium'
}

function normalizePropertyType(value: unknown): Trip['hotel']['propertyType'] {
  const propertyType = getString(value).toLowerCase()

  if (propertyType === 'resort' || propertyType === 'apartment' || propertyType === 'boutique') {
    return propertyType
  }

  return 'hotel'
}

function normalizePace(style: string): Trip['traveler']['preferences']['pace'] {
  const lower = style.toLowerCase()

  if (lower.includes('relax') || lower.includes('slow')) {
    return 'relaxed'
  }

  if (lower.includes('adventure') || lower.includes('active') || lower.includes('fast')) {
    return 'active'
  }

  return 'balanced'
}

function normalizeBudgetRange(style: string, totalBudget: number, durationDays: number): Trip['traveler']['preferences']['budgetRange'] {
  const lower = style.toLowerCase()
  const perDay = durationDays > 0 ? totalBudget / durationDays : totalBudget

  if (lower.includes('luxury') || perDay >= 500) {
    return 'luxury'
  }

  if (lower.includes('budget') || perDay <= 150) {
    return 'economy'
  }

  return 'mid-range'
}

function normalizeSimplePlan(raw: unknown): SimpleTravelPlan {
  const record = asRecord(raw)

  const emergencyInfo = asRecord(record.emergencyInfo ?? record['emergency information'])

  return {
    destination: getString(record.destination),
    country: getString(record.country),
    durationDays: getNumber(record.durationDays, 7),
    travelStyle: getString(record.travelStyle),
    summary: getString(record.summary),
    hotel: asRecord(record.hotel) as SimpleTravelPlanHotel,
    restaurants: Array.isArray(record.restaurants) ? (record.restaurants as SimpleTravelPlanRestaurant[]) : [],
    itinerary: Array.isArray(record.itinerary) ? (record.itinerary as SimpleTravelPlanDay[]) : [],
    budget: asRecord(record.budget) as SimpleTravelPlanBudget,
    weather: Array.isArray(record.weather) ? (record.weather as SimpleTravelPlanWeather[]) : [],
    packingList: Array.isArray(record.packingList)
      ? (record.packingList as SimpleTravelPlanPackingItem[])
      : Array.isArray(record['packing list'])
        ? (record['packing list'] as SimpleTravelPlanPackingItem[])
        : [],
    transportation: Array.isArray(record.transportation)
      ? (record.transportation as SimpleTravelPlanTransportation[])
      : [],
    localTips: Array.isArray(record.localTips)
      ? (record.localTips as SimpleTravelPlanLocalTip[])
      : Array.isArray(record['local tips'])
        ? (record['local tips'] as SimpleTravelPlanLocalTip[])
        : [],
    emergencyInfo: emergencyInfo as SimpleTravelPlanEmergencyInformation,
  }
}

function mapActivities(rawActivities: SimpleTravelPlanActivity[] | undefined): Activity[] {
  if (!Array.isArray(rawActivities)) {
    return []
  }

  return rawActivities.map((activity, index) => {
    const item = asRecord(activity)

    return {
      id: `activity-${index + 1}-${crypto.randomUUID().slice(0, 8)}`,
      title: getString(item.title, `Activity ${index + 1}`),
      description: getString(item.description, ''),
      startTime: getString(item.startTime),
      endTime: getString(item.endTime),
      category: normalizeActivityCategory(item.category),
      location: getString(item.location, ''),
      notes: getString(item.notes),
      imageUrl: getString(item.imageUrl),
      priority: normalizeActivityPriority(item.priority),
    }
  })
}

function mapItinerary(
  itinerary: SimpleTravelPlanDay[] | undefined,
  destinationName: string,
  tripSummary: string,
  startDate: Date,
  durationDays: number,
): DailyItinerary[] {
  const source = Array.isArray(itinerary) ? itinerary : []

  if (source.length === 0) {
    return Array.from({ length: durationDays }).map((_, index) => {
      const dayNumber = index + 1
      return {
        id: `day-${dayNumber}-${crypto.randomUUID().slice(0, 8)}`,
        dayNumber,
        date: toIsoDate(addDays(startDate, index)),
        title: `Day ${dayNumber} in ${destinationName}`,
        summary: tripSummary,
        activities: [],
      }
    })
  }

  return source.map((rawDay, index) => {
    const day = asRecord(rawDay)
    const dayNumber = Math.max(1, Math.floor(getNumber(day.dayNumber, index + 1)))

    return {
      id: `day-${dayNumber}-${crypto.randomUUID().slice(0, 8)}`,
      dayNumber,
      date: getString(day.date, toIsoDate(addDays(startDate, index))),
      title: getString(day.title, `Day ${dayNumber} in ${destinationName}`),
      summary: getString(day.summary, tripSummary),
      activities: mapActivities(Array.isArray(day.activities) ? (day.activities as SimpleTravelPlanActivity[]) : []),
    }
  })
}

function mapBudget(rawBudget: SimpleTravelPlanBudget | undefined, durationDays: number) {
  const budget = asRecord(rawBudget)
  const categories = asRecord(budget.categories)

  const estimatedSpend = Math.max(0, getNumber(budget.estimatedSpend, durationDays * 220))
  const totalBudget = Math.max(estimatedSpend, getNumber(budget.totalBudget, durationDays * 260))

  const defaultLodging = Math.round(totalBudget * 0.4)
  const defaultFood = Math.round(totalBudget * 0.22)
  const defaultActivities = Math.round(totalBudget * 0.18)
  const defaultTransportation = Math.round(totalBudget * 0.14)
  const used = defaultLodging + defaultFood + defaultActivities + defaultTransportation
  const defaultMisc = Math.max(0, totalBudget - used)

  return {
    id: `budget-${crypto.randomUUID().slice(0, 8)}`,
    currency: getString(budget.currency, 'USD'),
    totalBudget,
    estimatedSpend,
    categories: {
      lodging: Math.max(0, getNumber(categories.lodging, defaultLodging)),
      food: Math.max(0, getNumber(categories.food, defaultFood)),
      activities: Math.max(0, getNumber(categories.activities, defaultActivities)),
      transportation: Math.max(0, getNumber(categories.transportation, defaultTransportation)),
      misc: Math.max(0, getNumber(categories.misc, defaultMisc)),
    },
  }
}

function mapHotel(
  rawHotel: SimpleTravelPlanHotel | undefined,
  destinationName: string,
  startDate: string,
  endDate: string,
  nightlyBudget: number,
) {
  const hotel = asRecord(rawHotel)

  return {
    id: `hotel-${crypto.randomUUID().slice(0, 8)}`,
    name: getString(hotel.name, `${destinationName} Central Hotel`),
    propertyType: normalizePropertyType(hotel.propertyType),
    neighborhood: getString(hotel.neighborhood, ''),
    checkIn: getString(hotel.checkIn, startDate),
    checkOut: getString(hotel.checkOut, endDate),
    rating: Math.max(1, Math.min(5, getNumber(hotel.rating, 4.4))),
    pricePerNight: Math.max(0, getNumber(hotel.pricePerNight, nightlyBudget)),
    amenities: getStringArray(hotel.amenities, []),
    bookingUrl: getString(hotel.bookingUrl),
  }
}

function mapRestaurants(restaurants: SimpleTravelPlanRestaurant[] | undefined): Restaurant[] {
  if (!Array.isArray(restaurants)) {
    return []
  }

  return restaurants.map((rawRestaurant, index) => {
    const restaurant = asRecord(rawRestaurant)

    return {
      id: `restaurant-${index + 1}-${crypto.randomUUID().slice(0, 8)}`,
      name: getString(restaurant.name, `Restaurant ${index + 1}`),
      cuisine: getString(restaurant.cuisine, 'Local'),
      neighborhood: getString(restaurant.neighborhood, ''),
      rating: Math.max(1, Math.min(5, getNumber(restaurant.rating, 4.3))),
      priceLevel: normalizePriceLevel(restaurant.priceLevel),
      reservationRequired: getBoolean(restaurant.reservationRequired, false),
      notes: getString(restaurant.notes),
      websiteUrl: getString(restaurant.websiteUrl),
    }
  })
}

function mapWeather(weather: SimpleTravelPlanWeather[] | undefined, destinationId: string, startDate: Date): Weather[] {
  if (!Array.isArray(weather) || weather.length === 0) {
    return [
      {
        id: `weather-1-${crypto.randomUUID().slice(0, 8)}`,
        destinationId,
        date: toIsoDate(startDate),
        summary: 'Seasonal conditions expected.',
        temperatureHigh: 25,
        temperatureLow: 17,
        precipitationChance: 20,
        condition: 'mild',
      },
    ]
  }

  return weather.map((rawWeather, index) => {
    const day = asRecord(rawWeather)

    return {
      id: `weather-${index + 1}-${crypto.randomUUID().slice(0, 8)}`,
      destinationId,
      date: getString(day.date, toIsoDate(addDays(startDate, index))),
      summary: getString(day.summary, 'Seasonal conditions expected.'),
      temperatureHigh: getNumber(day.temperatureHigh, 25),
      temperatureLow: getNumber(day.temperatureLow, 17),
      precipitationChance: Math.max(0, Math.min(100, getNumber(day.precipitationChance, 20))),
      condition: normalizeWeatherCondition(day.condition),
    }
  })
}

function mapPackingList(packingList: SimpleTravelPlanPackingItem[] | undefined): PackingItem[] {
  if (!Array.isArray(packingList)) {
    return []
  }

  return packingList.map((rawItem, index) => {
    const item = asRecord(rawItem)

    return {
      id: `packing-${index + 1}-${crypto.randomUUID().slice(0, 8)}`,
      name: getString(item.name, `Packing item ${index + 1}`),
      category: normalizePackingCategory(item.category),
      packed: getBoolean(item.packed, false),
      required: getBoolean(item.required, true),
      notes: getString(item.notes),
    }
  })
}

function mapTransportation(transportation: SimpleTravelPlanTransportation[] | undefined): Transportation[] {
  if (!Array.isArray(transportation)) {
    return []
  }

  return transportation.map((rawLeg, index) => {
    const leg = asRecord(rawLeg)

    return {
      id: `transport-${index + 1}-${crypto.randomUUID().slice(0, 8)}`,
      mode: normalizeTransportMode(leg.mode),
      from: getString(leg.from, ''),
      to: getString(leg.to, ''),
      departureTime: getString(leg.departureTime),
      arrivalTime: getString(leg.arrivalTime),
      bookingReference: getString(leg.bookingReference),
      notes: getString(leg.notes),
    }
  })
}

function mapLocalTips(localTips: SimpleTravelPlanLocalTip[] | undefined): LocalTip[] {
  if (!Array.isArray(localTips)) {
    return []
  }

  return localTips.map((rawTip, index) => {
    const tip = asRecord(rawTip)

    return {
      id: `tip-${index + 1}-${crypto.randomUUID().slice(0, 8)}`,
      title: getString(tip.title, `Tip ${index + 1}`),
      summary: getString(tip.summary, ''),
      category: normalizeTipCategory(tip.category),
      priority: normalizeTipPriority(tip.priority),
    }
  })
}

function mapEmergencyInfo(emergencyInfo: SimpleTravelPlanEmergencyInformation | undefined) {
  const info = asRecord(emergencyInfo)

  return {
    id: `emergency-${crypto.randomUUID().slice(0, 8)}`,
    contactName: getString(info.contactName, ''),
    contactPhone: getString(info.contactPhone, ''),
    embassyContact: getString(info.embassyContact),
    medicalNote: getString(info.medicalNote),
    localEmergencyNumber: getString(info.localEmergencyNumber, ''),
  }
}

export function mapSimpleTripToTrip(rawPlan: unknown, prompt: string): Trip {
  const plan = normalizeSimplePlan(rawPlan)
  const now = new Date()
  const createdAt = now.toISOString()

  const durationDays = Math.max(1, Math.floor(getNumber(plan.durationDays, 7)))
  const destinationName = getString(plan.destination, 'Unknown Destination')
  const country = getString(plan.country, 'Unknown Country')
  const summary = getString(plan.summary, `A ${durationDays}-day itinerary for ${destinationName}.`)
  const travelStyle = normalizeTravelStyle(plan.travelStyle)

  const startDate = now
  const endDate = addDays(startDate, durationDays - 1)
  const startDateString = toIsoDate(startDate)
  const endDateString = toIsoDate(endDate)

  const budget = mapBudget(plan.budget, durationDays)
  const hotel = mapHotel(
    plan.hotel,
    destinationName,
    startDateString,
    endDateString,
    Math.round(budget.categories.lodging / durationDays),
  )

  const travelerId = `traveler-${crypto.randomUUID().slice(0, 8)}`
  const destinationId = `destination-${crypto.randomUUID().slice(0, 8)}`

  const itinerary = mapItinerary(plan.itinerary, destinationName, summary, startDate, durationDays)

  return {
    id: `trip-${crypto.randomUUID().slice(0, 8)}`,
    title: `${destinationName} ${durationDays}-Day Journey`,
    slug: normalizeSlug(`${destinationName}-${country}-${durationDays}-days`),
    travelerId,
    createdAt,
    updatedAt: createdAt,
    status: 'generated',

    destination: {
      id: destinationId,
      name: destinationName,
      country,
      region: '',
      latitude: 0,
      longitude: 0,
      timezone: 'UTC',
      climateSummary: plan.weather?.[0]?.summary ? getString(plan.weather[0].summary) : '',
      bestSeason: ['Year-round'],
      description: summary,
    },

    traveler: {
      id: travelerId,
      name: 'Traveler',
      email: 'traveler@example.com',
      avatarUrl: '',
      preferences: {
        travelStyle: [travelStyle],
        pace: normalizePace(travelStyle),
        budgetRange: normalizeBudgetRange(travelStyle, budget.totalBudget, durationDays),
        interests: [],
      },
    },

    overview: {
      summary,
      vibe: travelStyle,
      durationDays,
      startDate: startDateString,
      endDate: endDateString,
    },

    itinerary,
    hotel,
    restaurants: mapRestaurants(plan.restaurants),
    budget,
    weather: mapWeather(plan.weather, destinationId, startDate),
    packingList: mapPackingList(plan.packingList),
    emergencyInfo: mapEmergencyInfo(plan.emergencyInfo),
    transportation: mapTransportation(plan.transportation),
    localTips: mapLocalTips(plan.localTips),

    metadata: {
      generatedFromPrompt: prompt,
      source: 'ai',
      tags: [country, destinationName, travelStyle].filter((tag) => tag.length > 0),
    },
  }
}
