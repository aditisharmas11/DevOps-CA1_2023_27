import type { Trip } from '../../types/trip'
import { applyBudget } from './applyBudget'
import { applyTravelStyle } from './applyTravelStyle'
import { applyTravelerType } from './applyTravelerType'
import { cloneTrip } from './shared'
import type { PlannerSelections } from './types'

export function buildPersonalizedTrip(baseTrip: Trip, selections: PlannerSelections): Trip {
  const personalized = cloneTrip(baseTrip)

  applyTravelerType(personalized, selections.travelerType)
  applyTravelStyle(personalized, selections.travelStyle)
  applyBudget(personalized, selections.budget)

  personalized.updatedAt = new Date().toISOString()

  return personalized
}
