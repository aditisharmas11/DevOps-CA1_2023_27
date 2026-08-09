import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider } from 'react-router-dom'
import './index.css'
import { TripProvider } from './context/TripContext'
import router from './router'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <TripProvider>
      <RouterProvider router={router} />
    </TripProvider>
  </StrictMode>,
)
