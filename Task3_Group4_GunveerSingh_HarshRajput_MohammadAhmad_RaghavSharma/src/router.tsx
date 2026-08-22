import { createBrowserRouter } from 'react-router-dom'
import App from './App'
import DashboardPage from './pages/Dashboard'
import RenderPreviewPage from './pages/RenderPreview'
import NotFoundPage from './pages/NotFound'

const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
  },
  {
    path: '/dashboard',
    element: <DashboardPage />,
  },
  {
    path: '/preview',
    element: <RenderPreviewPage />,
  },
  {
    path: '*',
    element: <NotFoundPage />,
  },
])

export default router
