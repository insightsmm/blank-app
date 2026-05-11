import { Navigate } from 'react-router-dom'
import { useApp } from '../../state/AppState.jsx'

export default function AutoBlogSites() {
  const { activeBrand } = useApp()
  if (!activeBrand) return <Navigate to="/app/brands" replace />
  return <Navigate to={`/brands/${activeBrand.id}/auto-blog`} replace />
}
