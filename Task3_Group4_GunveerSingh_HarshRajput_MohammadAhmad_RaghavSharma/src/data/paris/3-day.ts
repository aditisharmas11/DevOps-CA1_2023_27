import { createTripDataset } from '../shared/createTripDataset'

export const Paris3Day = createTripDataset(3, {
  cityKey: 'paris',
  destination: {
    id: 'dest-paris',
    name: 'Paris',
    country: 'France',
    region: 'Ile-de-France',
    timezone: 'CET',
    climateSummary: 'Mild seasons with golden evenings and elegant boulevards.',
    bestSeason: ['April', 'May', 'September'],
    description: 'A polished city escape where art, architecture, and dining set the rhythm.',
  },
  overview: {
    summary: 'A curated 3-day Paris journey featuring landmark culture, neighborhood walks, and classic bistro evenings.',
    vibe: 'Editorial romance with cultural highlights',
    startDate: '2026-10-04',
    endDate: '2026-10-06',
  },
})
