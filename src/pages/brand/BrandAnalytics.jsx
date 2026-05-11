import { useParams } from 'react-router-dom'
import { useApp } from '../../state/AppState.jsx'

const STATS = [
  { eb: 'Traffic vs baseline', n: '+3.5×', s: 'Trailing 90 days' },
  { eb: 'Indexed pages',       n: '+434%', s: 'New URLs ranked' },
  { eb: 'Backlinks',           n: '+97%',  s: 'Organic referrals' },
  { eb: 'Leads',               n: '+67%',  s: 'Form / email opt-ins' },
]

export default function BrandAnalytics() {
  const { id } = useParams()
  const { state } = useApp()
  const brand = state.brands.find(b => b.id === id) || state.brands[0]

  return (
    <>
      <h1 className="page-h1">Analytics · <em>{brand?.name}</em></h1>
      <p className="page-sub">Traffic, indexing, and lead generation for this brand workspace.</p>

      <div className="grid cols-4">
        {STATS.map(s => (
          <div key={s.eb} className="card-tp stat-card">
            <div className="eyebrow">{s.eb}</div>
            <div className="num">{s.n}</div>
            <div className="subtxt">{s.s}</div>
          </div>
        ))}
      </div>

      <div className="card-tp" style={{ marginTop: 24 }}>
        <h3 style={{ fontSize: 20, marginBottom: 8 }}>Traffic over time</h3>
        <div style={{ height: 220, background: 'var(--paper-2)', borderRadius: 8, display: 'flex', alignItems: 'flex-end', padding: 16, gap: 6 }}>
          {[40, 52, 48, 64, 70, 81, 92, 88, 96, 110, 124, 138].map((h, i) => (
            <div key={i} style={{ flex: 1, height: `${h}%`, background: 'var(--accent)', opacity: .55 + (i / 24), borderRadius: 4 }} />
          ))}
        </div>
        <div className="row between" style={{ marginTop: 8 }}>
          <span className="muted tiny">12 weeks ago</span>
          <span className="muted tiny">Today</span>
        </div>
      </div>
    </>
  )
}
