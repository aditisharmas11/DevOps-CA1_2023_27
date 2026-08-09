import { Router } from 'express'
import { generateTripFromPrompt } from '../services/openai.js'

const router = Router()

router.post('/generate-trip', async (req, res) => {
  const prompt = typeof req.body?.prompt === 'string' ? req.body.prompt.trim() : ''

  if (!prompt) {
    return res.status(400).json({ error: 'A travel prompt is required.' })
  }

  try {
    const trip = await generateTripFromPrompt(prompt)
    return res.json(trip)
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unable to generate a trip right now.'
    return res.status(500).json({ error: message })
  }
})

export default router
