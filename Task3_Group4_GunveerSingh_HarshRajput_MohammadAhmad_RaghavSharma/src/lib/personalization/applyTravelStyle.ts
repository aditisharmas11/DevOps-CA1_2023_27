import type { Activity, Trip } from '../../types/trip'
import type { PlannerTravelStyle } from './types'
import { createId, prependTips } from './shared'

interface StyleProfile {
  activityCategory: Activity['category']
  titlePrefix: string
  description: string
  note: string
  tip: {
    title: string
    summary: string
    category: 'culture' | 'practical' | 'food' | 'safety' | 'weather'
    priority: 'high' | 'medium' | 'low'
  }
}

const styleProfiles: Record<PlannerTravelStyle, StyleProfile> = {
  Adventure: {
    activityCategory: 'adventure',
    titlePrefix: 'Adventure Trail & Outdoor Excursion',
    description: 'High-energy outdoor exploration featuring scenic hikes, biking, or thrill activities.',
    note: 'Adventure style: Pack flexible layers, check weather forecasts, and maintain active pacing.',
    tip: {
      title: 'Weather & Gear Readiness',
      summary: 'Outdoor adventure activities benefit from flexible layers and hydrated pacing.',
      category: 'weather',
      priority: 'high',
    },
  },
  Luxury: {
    activityCategory: 'wellness',
    titlePrefix: 'Luxury VIP Experience',
    description: 'Private guided access, luxury lounge relaxation, and exclusive concierge service.',
    note: 'Luxury style: Private chauffeur and skip-the-line VIP access arranged.',
    tip: {
      title: 'VIP Concierge Access',
      summary: 'Private transfers and exclusive viewing slots ensure maximum comfort.',
      category: 'practical',
      priority: 'high',
    },
  },
  Food: {
    activityCategory: 'food',
    titlePrefix: 'Gastronomic Culinary Route',
    description: 'Curated food market tour, street food tasting, and local chef masterclass.',
    note: 'Food style: Leave room for afternoon tasting stops and regional culinary pauses.',
    tip: {
      title: 'Culinary Market Hours',
      summary: 'Local food markets are liveliest around morning opening or twilight food stalls.',
      category: 'food',
      priority: 'high',
    },
  },
  Culture: {
    activityCategory: 'culture',
    titlePrefix: 'Cultural Heritage & History Walk',
    description: 'Deep-dive heritage walk through historic landmarks, art museums, and temples.',
    note: 'Culture style: Early morning visits provide quiet reflection and artifact viewing.',
    tip: {
      title: 'Museum & Heritage Passes',
      summary: 'Advance digital museum passes bypass general queues during peak hours.',
      category: 'culture',
      priority: 'high',
    },
  },
  Nature: {
    activityCategory: 'nature',
    titlePrefix: 'Scenic Nature & Garden Retreat',
    description: 'Peaceful breathing space in botanical gardens, coastal paths, or panoramic parks.',
    note: 'Nature style: Best experienced during soft early morning light or sunset.',
    tip: {
      title: 'Scenic Outdoor Golden Hour',
      summary: 'Parks and natural viewpoints offer peak colors during sunrise or sunset.',
      category: 'weather',
      priority: 'medium',
    },
  },
  Romantic: {
    activityCategory: 'wellness',
    titlePrefix: 'Romantic Atmospheric Chapter',
    description: 'Intimate couples experience with romantic views, ambient lighting, and serene pacing.',
    note: 'Romantic style: Reserved twilight timing for optimal couples ambiance.',
    tip: {
      title: 'Atmospheric Evening Spots',
      summary: 'Illuminated bridges and rooftop terraces deliver memorable romantic views.',
      category: 'practical',
      priority: 'medium',
    },
  },
  Business: {
    activityCategory: 'culture',
    titlePrefix: 'Business Executive Discovery',
    description: 'Efficient city overview combined with quiet executive lounge work windows.',
    note: 'Business style: Fast Wi-Fi available; 45-minute structured duration with schedule buffers.',
    tip: {
      title: 'Executive Work & Transit Buffers',
      summary: 'Allow 30-minute buffers between meetings for express transit and calls.',
      category: 'practical',
      priority: 'high',
    },
  },
}

export function applyTravelStyle(trip: Trip, travelStyle: PlannerTravelStyle): Trip {
  const profile = styleProfiles[travelStyle]

  trip.traveler.preferences.travelStyle = [travelStyle.toLowerCase()]
  trip.overview.vibe = `${travelStyle} style with curated ${travelStyle.toLowerCase()} pacing`

  trip.itinerary = trip.itinerary.map((day, index) => {
    const styleActivity: Activity = {
      id: createId('activity-style'),
      title: `${profile.titlePrefix}: ${trip.destination.name}`,
      description: profile.description,
      category: profile.activityCategory,
      location: day.activities[0]?.location ?? trip.destination.name,
      notes: profile.note,
      startTime: index % 3 === 0 ? '11:30' : index % 3 === 1 ? '15:30' : '18:30',
      endTime: index % 3 === 0 ? '12:30' : index % 3 === 1 ? '16:30' : '19:30',
      priority: 'nice-to-have',
    }

    const optionalIndex = day.activities.findIndex((activity) => activity.priority === 'optional')

    if (optionalIndex >= 0) {
      const activities = [...day.activities]
      activities[optionalIndex] = styleActivity

      return {
        ...day,
        summary: `${day.summary} Focus on ${travelStyle.toLowerCase()} experiences.`,
        activities,
      }
    }

    return {
      ...day,
      summary: `${day.summary} Focus on ${travelStyle.toLowerCase()} experiences.`,
      activities: [...day.activities, styleActivity],
    }
  })

  trip.localTips = prependTips(trip.localTips, [profile.tip])
  trip.metadata.tags = Array.from(new Set([...trip.metadata.tags, travelStyle.toLowerCase()]))

  return trip
}

