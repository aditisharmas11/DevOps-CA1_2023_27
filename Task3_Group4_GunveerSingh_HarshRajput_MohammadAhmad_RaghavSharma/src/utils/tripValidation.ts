export function validateTripPrompt(prompt: string) {
  const trimmed = prompt.trim()

  if (!trimmed) {
    return 'Please describe the kind of journey you want to create.'
  }

  if (trimmed.length < 6) {
    return 'Please share a bit more detail so Atlas can shape a stronger itinerary.'
  }

  return null
}
