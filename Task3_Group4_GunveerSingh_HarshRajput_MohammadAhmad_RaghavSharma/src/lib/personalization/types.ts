export type PlannerTravelerType = 'Solo' | 'Couple' | 'Family' | 'Friends'

export type PlannerTravelStyle =
  | 'Adventure'
  | 'Luxury'
  | 'Food'
  | 'Culture'
  | 'Nature'
  | 'Romantic'
  | 'Business'

export type PlannerBudget = 'Budget' | 'Mid-range' | 'Luxury'

export interface PlannerSelections {
  travelerType: PlannerTravelerType
  travelStyle: PlannerTravelStyle
  budget: PlannerBudget
}
