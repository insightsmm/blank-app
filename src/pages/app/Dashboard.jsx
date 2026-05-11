import { Link } from 'react-router-dom'
import { useApp } from '../../state/AppState.jsx'

export default function Dashboard() {
  const { state, activeBrand } = useApp()

  const stats = [
    { eb: 'Scripts',        n: state.scripts.length, s: 'In Clarity Mirror' },
    { eb: 'Calendar posts', n: Object.keys(state.calendar || {}).length, s: 'Planned + scheduled' },
    { eb: 'Open tasks',     n: state.tasks.filter(t => t.column !== 'done').length, s: 'Pending' },
    { eb: 'Proof assets',   n: state.proof.length, s: 'In vault' },
  ]

  return (
    <>
      <h1 className="page-h1">Welcome back, <em>{activeBrand?.name}</em>.</h1>
      <p className="page-sub">Working on {activeBrand?.name}. {state.agencyMode ? 'Agency mode active.' : 'Solo mode.'}</p>

      <div className="grid cols-4">
        {stats.map(s => (
          <div key={s.eb} className="card-tp stat-card">
            <div className="eyebrow">{s.eb}</div>
            <div className="num">{s.n}</div>
            <div className="subtxt">{s.s}</div>
          </div>
        ))}
      </div>

      <div style={{ marginTop: 32 }} className="grid cols-2">
        <div className="card-tp">
          <h3 style={{ fontSize: 22, marginBottom: 4 }}>Quick actions</h3>
          <p className="muted small" style={{ marginBottom: 16 }}>Jump into the work.</p>
          <div className="stack" style={{ gap: 10 }}>
            <Link to="/app/clarity" className="btn-tp primary">Write a script →</Link>
            <Link to="/app/studio" className="btn-tp ghost">Generate 30-day plan</Link>
            <Link to="/app/tasks" className="btn-tp ghost">Open tasks</Link>
            <Link to="/app/proof" className="btn-tp ghost">Add proof asset</Link>
          </div>
        </div>

        <div className="card-tp">
          <h3 style={{ fontSize: 22, marginBottom: 4 }}>What's next</h3>
          <p className="muted small" style={{ marginBottom: 16 }}>
            {state.scripts.length === 0
              ? 'Start by writing your first script in the Clarity Mirror — your TPO plan and post calendar build from there.'
              : `You've written ${state.scripts.length} script${state.scripts.length === 1 ? '' : 's'}. Time to schedule them in TPO Studio.`
            }
          </p>
          <Link to="/app/clarity" className="btn-tp dark">Open Clarity Mirror</Link>
        </div>
      </div>

      <div style={{ marginTop: 32 }} className="card-tp">
        <div className="eyebrow eyebrow-accent">Recent scripts</div>
        <h3 style={{ fontSize: 22, marginTop: 4, marginBottom: 12 }}>Latest from the Mirror</h3>
        {state.scripts.length === 0 ? (
          <p className="muted small">No scripts yet — your generated reels will appear here.</p>
        ) : (
          <div className="stack" style={{ gap: 10 }}>
            {state.scripts.slice(0, 4).map(s => (
              <div key={s.id} className="row between" style={{ padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
                <div>
                  <div className="row" style={{ gap: 8 }}>
                    <span className={`pill ${s.pillar || 'teach'}`}>{s.pillar || 'teach'}</span>
                    <strong style={{ fontSize: 14 }}>{s.analogy || 'Untitled'}</strong>
                  </div>
                  <div className="muted tiny" style={{ marginTop: 4 }}>{new Date(s.createdAt).toLocaleString()}</div>
                </div>
                <span className="muted tiny">{(s.output || '').length} chars</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  )
}
