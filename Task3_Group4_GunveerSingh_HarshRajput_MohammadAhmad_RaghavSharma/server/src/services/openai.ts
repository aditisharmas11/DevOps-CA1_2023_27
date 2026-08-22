import OpenAI from 'openai'
import type { Trip } from '../../../src/types/trip.js'
import { mapSimpleTripToTrip } from '../mappers/tripMapper.js'
import { systemPrompt } from '../prompts/systemPrompt.js'

function cleanJsonResponse(raw: string): string {
  return raw
    .trim()
    .replace(/^```json\s*/i, '')
    .replace(/^```\s*/i, '')
    .replace(/\s*```$/i, '')
    .trim()
}

export async function generateTripFromPrompt(prompt: string): Promise<Trip> {
  if (!process.env.OPENAI_API_KEY) {
    throw new Error('Missing OpenAI API key')
  }

  const client = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
  })

  const completion = await client.chat.completions.create({
    model: 'gpt-4o-mini',
    temperature: 0.7,
    response_format: {
      type: 'json_object',
    },
    messages: [
      {
        role: 'system',
        content: systemPrompt,
      },
      {
        role: 'user',
        content: prompt,
      },
    ],
  })

  const content = completion.choices[0]?.message?.content

  if (!content) {
    throw new Error('OpenAI returned an empty response.')
  }

  try {
    const parsed = JSON.parse(cleanJsonResponse(content))

    return mapSimpleTripToTrip(parsed, prompt)
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(`Unable to parse OpenAI response: ${error.message}`)
    }

    throw new Error('Unable to parse OpenAI response.')
  }
}