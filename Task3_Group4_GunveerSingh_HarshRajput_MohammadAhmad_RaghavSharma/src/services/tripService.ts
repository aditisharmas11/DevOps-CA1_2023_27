import type { Trip } from '../types/trip'

export async function generateTrip(prompt: string): Promise<Trip> {
  const response = await fetch('/api/generate-trip', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ prompt }),
  })

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null)
    const message = errorBody?.error ?? 'Unable to create a journey right now.'
    throw new Error(message)
  }

  const trip = (await response.json()) as Trip

  if (!trip || typeof trip !== 'object') {
    throw new Error('The server returned an invalid trip payload.')
  }

  return trip
}
