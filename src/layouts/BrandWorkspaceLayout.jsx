import { Outlet, NavLink, useParams, Link } from 'react-router-dom'
import TopNav from '../components/TopNav.jsx'
import TrialBanner from '../components/TrialBanner.jsx'
import { useApp } from '../state/AppState.jsx'

export default function BrandWorkspaceLayout() {
  const { id } = useParams()
  const { state } = useApp()
  const brand = state.brands.find(b => b.id === id) || state.brands[0]

  return (
    <>
      <TopNav />
      <TrialBanner />
      <div className="brand-bar">
        <div className="left">
          <Link to="/app/brands" style={{ color: 'var(--paper)', opacity: .7, fontSize: 12 }}>← All workspaces</Link>
          <div className="row" style={{ gap: 12 }}>
            <span className="brand-avatar">{brand?.name?.charAt(0).toUpperCase()}</span>
            <div>
              <div style={{ fontSize: 15, fontFamily: 'Fraunces, Georgia, serif' }}>{brand?.name}</div>
              <div className="label-eb" style={{ fontSize: 10 }}>{brand?.niche}</div>
            </div>
          </div>
        </div>
      </div>
      <div className="app-grid">
        <aside className="sidebar">
          <div className="group-label">Workspace</div>
          <nav className="stack" style={{ gap: 2 }}>
            <NavLink end to={`/brands/${id}`} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <span className="letter">D</span><span>Dashboard</span>
            </NavLink>
            <NavLink to={`/brands/${id}/auto-blog`} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <span className="letter">A</span><span>Auto Blog</span>
            </NavLink>
            <NavLink to={`/brands/${id}/analytics`} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <span className="letter">A</span><span>Analytics</span>
            </NavLink>
            <NavLink to={`/brands/${id}/settings`} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <span className="letter">S</span><span>Settings</span>
            </NavLink>
          </nav>
        </aside>
        <main className="main-area">
          <Outlet />
        </main>
      </div>
    </>
  )
}
