import type { Activity, Restaurant, Trip } from '../../types/trip'
import type { PlannerTravelerType } from './types'
import { appendNote, createId, prependTips } from './shared'

interface TravelerProfile {
  travelerName: string
  itineraryLabel: string
  restaurantNote: string
  tipSet: Array<{
    title: string
    summary: string
    category: 'culture' | 'practical' | 'food' | 'safety' | 'weather'
    priority: 'high' | 'medium' | 'low'
  }>
  restaurantScoring: (restaurant: Restaurant) => number
  getDayActivity: (dayIndex: number, destinationName: string) => Partial<Activity>
}

const travelerProfiles: Record<PlannerTravelerType, TravelerProfile> = {
  Solo: {
    travelerName: 'Solo Explorer',
    itineraryLabel: 'Solo Discovery',
    restaurantNote: 'Solo dining: Welcoming counter seating, quick walk-ins, and relaxed single-diner atmosphere.',
    tipSet: [
      {
        title: 'Solo Photography & Scenic Spots',
        summary: 'Early morning visits to major spots yield clean photos without crowds.',
        category: 'practical',
        priority: 'high',
      },
      {
        title: 'Best Work & Coffee Cafés',
        summary: 'Look for quiet local cafés with free Wi-Fi and power outlets for casual pauses.',
        category: 'food',
        priority: 'medium',
      },
      {
        title: 'Solo Navigation & Safety',
        summary: 'Keep offline maps downloaded and stick to well-lit main corridors during late evening returns.',
        category: 'safety',
        priority: 'high',
      },
    ],
    restaurantScoring: (restaurant) => {
      let score = 0
      if (restaurant.priceLevel === 'budget' || restaurant.priceLevel === 'mid') score += 3
      if (!restaurant.reservationRequired) score += 2
      return score
    },
    getDayActivity: (dayIndex, destinationName) => {
      const activities: Array<Partial<Activity>> = [
        {
          title: `Solo Specialty Café & Coffee Tasting: ${destinationName}`,
          description: 'A cozy artisan coffee pause tuned for relaxed reading, journaling, and solo people-watching.',
          category: 'food',
          notes: 'Solo tip: Excellent single-counter seating with quiet ambiance and friendly baristas.',
          startTime: '10:00',
          endTime: '11:00',
        },
        {
          title: `Self-Guided Neighborhood Photography Walk`,
          description: 'A curated walking route through scenic alleyways and hidden street art spots.',
          category: 'culture',
          notes: 'Solo tip: Prime photo vantage points identified for hands-free framing.',
          startTime: '15:00',
          endTime: '16:30',
        },
        {
          title: `Historic District Solo Walking Tour`,
          description: 'A flexible, self-paced exploration of historic landmarks and quiet courtyard gardens.',
          category: 'culture',
          notes: 'Solo tip: Take audio guides at your own pace without group rush.',
          startTime: '11:30',
          endTime: '13:00',
        },
        {
          title: `Artisan Bookstore & Tea House Pause`,
          description: 'A quiet afternoon sanctuary featuring local literature and single-diner tea service.',
          category: 'wellness',
          notes: 'Solo tip: Peaceful spot to rest your feet between sightseeing legs.',
          startTime: '16:00',
          endTime: '17:00',
        },
      ]
      return activities[dayIndex % activities.length]
    },
  },
  Couple: {
    travelerName: 'Couples Getaway',
    itineraryLabel: 'Couple Moment',
    restaurantNote: 'Romantic dining: Candlelit table seating, panoramic views, and couple reservation priority.',
    tipSet: [
      {
        title: 'Golden Hour Sunset Dining',
        summary: 'Book sunset-facing tables at least 48 hours ahead for prime romantic views.',
        category: 'food',
        priority: 'high',
      },
      {
        title: 'Couple Spa & Relaxation',
        summary: 'Schedule a late afternoon spa or bathhouse session between major sightseeing days.',
        category: 'practical',
        priority: 'medium',
      },
      {
        title: 'Romantic Evening Promenades',
        summary: 'Waterfront paths and historic bridges offer illuminated evening strolls.',
        category: 'culture',
        priority: 'high',
      },
    ],
    restaurantScoring: (restaurant) => {
      let score = 0
      if (restaurant.priceLevel === 'high' || restaurant.priceLevel === 'luxury') score += 3
      if (restaurant.reservationRequired) score += 2
      return score
    },
    getDayActivity: (dayIndex, destinationName) => {
      const activities: Array<Partial<Activity>> = [
        {
          title: `Golden Hour Sunset Viewpoint & Cocktails: ${destinationName}`,
          description: 'An intimate sunset experience overlooking the city skyline with signature drinks.',
          category: 'wellness',
          notes: 'Romantic note: Reserve window seat for couples and enjoy sunset vistas.',
          startTime: '17:30',
          endTime: '19:00',
        },
        {
          title: `Couples Luxury Spa & Wellness Session`,
          description: 'A soothing relaxation treatment in a private dual suite with herbal teas.',
          category: 'wellness',
          notes: 'Romantic note: Includes private hydrotherapy pool and essential oil massage.',
          startTime: '14:30',
          endTime: '16:00',
        },
        {
          title: `Atmospheric Waterfront Evening Stroll`,
          description: 'A romantic evening walk along illuminated waterfront boardwalks and garden bridges.',
          category: 'nightlife',
          notes: 'Romantic note: Golden hour photography spot with quiet couples benches.',
          startTime: '19:30',
          endTime: '20:30',
        },
        {
          title: `Intimate Wine Tasting & Artisan Lounge`,
          description: 'A sommelier-guided tasting of regional wines in a historic vaulted cellar.',
          category: 'food',
          notes: 'Romantic note: Private alcove seating reserved for two.',
          startTime: '16:30',
          endTime: '18:00',
        },
      ]
      return activities[dayIndex % activities.length]
    },
  },
  Friends: {
    travelerName: 'Friends Adventure',
    itineraryLabel: 'Friends Social Stop',
    restaurantNote: 'Friends group dining: Lively atmosphere, shared tapas/platter menus, and large table seating.',
    tipSet: [
      {
        title: 'Nightlife & Rooftop Bar Hotspots',
        summary: 'Popular group rooftop lounges require group table bookings on weekend nights.',
        category: 'food',
        priority: 'high',
      },
      {
        title: 'Group Transport & Split Expenses',
        summary: 'Using group rideshares or multi-day transit passes keeps group travel smooth and budget-friendly.',
        category: 'practical',
        priority: 'high',
      },
      {
        title: 'High-Energy Group Activities',
        summary: 'Combine morning sightseeing with afternoon thrill or social food tours.',
        category: 'culture',
        priority: 'medium',
      },
    ],
    restaurantScoring: (restaurant) => {
      let score = 0
      if (restaurant.priceLevel === 'mid' || restaurant.priceLevel === 'high') score += 3
      if (restaurant.rating >= 4.4) score += 2
      return score
    },
    getDayActivity: (dayIndex, destinationName) => {
      const activities: Array<Partial<Activity>> = [
        {
          title: `Skyline Rooftop Bar & Social Lounge: ${destinationName}`,
          description: 'A high-energy rooftop lounge with DJ beats, panoramic city views, and craft cocktails.',
          category: 'nightlife',
          notes: 'Friends note: High energy rooftop venue with shared platters and lively vibe.',
          startTime: '20:00',
          endTime: '22:00',
        },
        {
          title: `Group Urban Adventure & Outdoor Challenge`,
          description: 'An exhilarating group activity featuring zip-lining, e-bike trails, or water sports.',
          category: 'adventure',
          notes: 'Friends note: Action-packed group challenge with great group photo opportunities.',
          startTime: '14:00',
          endTime: '16:30',
        },
        {
          title: `Street Food Crawl & Craft Beer Tasting`,
          description: 'A vibrant social food tour exploring bustling night markets and local microbreweries.',
          category: 'food',
          notes: 'Friends note: Sample 6+ local dishes and craft brews with group sharing tables.',
          startTime: '18:00',
          endTime: '20:00',
        },
        {
          title: `Late-Night Music Venue & Social Hub`,
          description: 'An iconic local music club featuring live acoustic sessions and craft drinks.',
          category: 'nightlife',
          notes: 'Friends note: Pre-book group booth for uninterrupted evening entertainment.',
          startTime: '21:30',
          endTime: '23:30',
        },
      ]
      return activities[dayIndex % activities.length]
    },
  },
  Family: {
    travelerName: 'Family Vacation',
    itineraryLabel: 'Family Highlight',
    restaurantNote: 'Family dining: Kid-friendly menus, high chairs, spacious seating, and fast service.',
    tipSet: [
      {
        title: 'Family Pacing & Rest Breaks',
        summary: 'Schedule 45-minute rest breaks after morning museum walks to keep kids energized.',
        category: 'practical',
        priority: 'high',
      },
      {
        title: 'Stroller & Accessibility Routes',
        summary: 'Check subway station elevator locations beforehand for easy stroller transfers.',
        category: 'practical',
        priority: 'high',
      },
      {
        title: 'Parks & Outdoor Play Areas',
        summary: 'Combine cultural visits with nearby park stops for open play and snack breaks.',
        category: 'culture',
        priority: 'medium',
      },
    ],
    restaurantScoring: (restaurant) => {
      let score = 0
      if (restaurant.priceLevel === 'budget' || restaurant.priceLevel === 'mid') score += 2
      if (!restaurant.reservationRequired) score += 2
      if (restaurant.rating >= 4.5) score += 1
      return score
    },
    getDayActivity: (dayIndex, destinationName) => {
      const activities: Array<Partial<Activity>> = [
        {
          title: `Spacious Central Park & Playground Pause: ${destinationName}`,
          description: 'A relaxed outdoor window featuring manicured lawns, playgrounds, and shaded picnic spots.',
          category: 'nature',
          notes: 'Family note: Stroller accessible, restrooms nearby, and open green space for kids.',
          startTime: '10:30',
          endTime: '12:00',
        },
        {
          title: `Interactive Science & Cultural Museum`,
          description: 'A hands-on discovery museum with interactive exhibits designed for all age groups.',
          category: 'culture',
          notes: 'Family note: Family pass available; includes interactive kids discovery zone.',
          startTime: '14:00',
          endTime: '16:00',
        },
        {
          title: `Scenic Waterfront Recreation & Ice Cream Walk`,
          description: 'A easy family stroll along car-free promenades with street performers and snack kiosks.',
          category: 'wellness',
          notes: 'Family note: Easy paved walkways with frequent seating and refreshment stops.',
          startTime: '16:30',
          endTime: '17:45',
        },
        {
          title: `Family Entertainment & Cultural Puppet/Light Show`,
          description: 'An enchanting evening performance showcasing local folklore through music and lights.',
          category: 'culture',
          notes: 'Family note: All-ages friendly with early evening showtimes.',
          startTime: '18:30',
          endTime: '19:30',
        },
      ]
      return activities[dayIndex % activities.length]
    },
  },
}

export function applyTravelerType(trip: Trip, travelerType: PlannerTravelerType): Trip {
  const profile = travelerProfiles[travelerType]

  trip.traveler.name = profile.travelerName

  trip.itinerary = trip.itinerary.map((day, index) => {
    const customActivity = profile.getDayActivity(index, trip.destination.name)

    const travelerActivity: Activity = {
      id: createId('activity-traveler'),
      title: customActivity.title ?? `${profile.itineraryLabel}: ${day.title}`,
      description: customActivity.description ?? 'Personalized activity curated for your travel group.',
      category: customActivity.category ?? 'culture',
      location: day.activities[0]?.location ?? trip.destination.name,
      notes: customActivity.notes ?? profile.restaurantNote,
      priority: 'nice-to-have',
      startTime: customActivity.startTime ?? '16:30',
      endTime: customActivity.endTime ?? '17:30',
    }

    const activities = day.activities.map((activity, activityIndex) => {
      if (activityIndex !== 0) {
        return activity
      }
      return {
        ...activity,
        notes: appendNote(activity.notes, `${travelerType} note: Tuned for ${travelerType.toLowerCase()} travel pacing.`),
      }
    })

    return {
      ...day,
      summary: `${day.summary} (Tailored for ${travelerType.toLowerCase()} travelers).`,
      activities: [...activities, travelerActivity],
    }
  })

  trip.restaurants = [...trip.restaurants]
    .sort((left, right) => profile.restaurantScoring(right) - profile.restaurantScoring(left))
    .map((restaurant, index) => {
      if (index > 3) {
        return restaurant
      }
      return {
        ...restaurant,
        notes: appendNote(restaurant.notes, profile.restaurantNote),
      }
    })

  trip.localTips = prependTips(trip.localTips, profile.tipSet)
  trip.overview.summary = `${trip.overview.summary} Personalized for ${travelerType.toLowerCase()} travelers.`
  trip.metadata.tags = Array.from(new Set([...trip.metadata.tags, travelerType.toLowerCase()]))

  return trip
}

