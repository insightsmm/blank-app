import { Link, useParams } from 'react-router-dom'
import { useApp } from '../../state/AppState.jsx'

export default function BrandDashboard() {
  const { id } = useParams()
  const { state } = useApp()
  const brand = state.brands.find(b => b.id === id) || state.brands[0]
  const autoBlog = state.autoBlog[id] || {}

  return (
    <>
      <h1 className="page-h1">{brand?.name} <em>workspace</em></h1>
      <p className="page-sub">Dedicated tools for this brand: blog automation, analytics, and settings.</p>

      <div className="grid cols-3">
        <Link to={`/brands/${id}/auto-blog`} className="card-tp" style={{ textDecoration: 'none', color: 'inherit' }}>
          <div className="eyebrow eyebrow-accent">Auto Blog</div>
          <h3 style={{ fontSize: 20, marginTop: 6 }}>{autoBlog.activated ? 'Active' : 'Set up daily blog'}</h3>
          <p className="muted small">Connect WordPress, generate posts daily, queue with approval flow.</p>
        </Link>
        <Link to={`/brands/${id}/analytics`} className="card-tp" style={{ textDecoration: 'none', color: 'inherit' }}>
          <div className="eyebrow eyebrow-accent">Analytics</div>
          <h3 style={{ fontSize: 20, marginTop: 6 }}>Performance</h3>
          <p className="muted small">Track impressions, indexed pages, and content velocity.</p>
        </Link>
        <Link to={`/brands/${id}/settings`} className="card-tp" style={{ textDecoration: 'none', color: 'inherit' }}>
          <div className="eyebrow eyebrow-accent">Settings</div>
          <h3 style={{ fontSize: 20, marginTop: 6 }}>Brand setup</h3>
          <p className="muted small">Identity, integrations, team access, and notifications.</p>
        </Link>
      </div>
    </>
  )
}
