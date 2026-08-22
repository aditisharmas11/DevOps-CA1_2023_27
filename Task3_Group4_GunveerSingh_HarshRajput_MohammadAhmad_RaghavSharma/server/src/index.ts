import express from 'express'
import dotenv from 'dotenv'
import tripRoutes from './routes/trip.js'

dotenv.config()

const app = express()
const port = Number(process.env.PORT ?? 3001)

app.use(express.json())
app.use('/api', tripRoutes)

app.get('/health', (_req, res) => {
  res.json({ status: 'ok' })
})

app.listen(port, () => {
  console.log(`Atlas backend listening on port ${port}`)
})
