import { NavLink } from 'react-router-dom'
import { useApp } from '../state/AppState.jsx'

const ITEMS = [
  { to: '/app',         label: 'Dashboard',      end: true },
  { to: '/app/brands',  label: 'All brands' },
  { to: '/app/profile', label: 'Brand profile' },
  { to: '/app/clarity', label: 'Clarity Mirror' },
  { to: '/app/studio',  label: 'TPO Studio' },
  { to: '/app/formats', label: 'Format Library' },
  { to: '/app/graphics',label: 'Graphics Studio' },
  { to: '/app/autoblog',label: 'Auto Blog sites' },
  { to: '/app/proof',   label: 'Proof Vault' },
  { to: '/app/tasks',   label: 'Tasks' },
  { to: '/app/portal',  label: 'Client Portal' },
]

export default function Sidebar() {
  const { state } = useApp()
  return (
    <aside className="sidebar">
      <div className="group-label">Workspace</div>
      <nav className="stack" style={{ gap: 2 }}>
        {ITEMS.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <span className="letter">{item.label.charAt(0)}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="mode-box">
        <div className="eyebrow">Mode</div>
        <div style={{ fontSize: 13, marginTop: 4 }}>
          {state.agencyMode ? 'Agency' : 'Solo'} {state.user.trialEnded ? '(trial)' : ''}
        </div>
      </div>
    </aside>
  )
}
