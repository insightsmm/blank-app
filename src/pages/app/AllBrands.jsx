import { Link } from 'react-router-dom'
import { useApp } from '../../state/AppState.jsx'

export default function AllBrands() {
  const { state, activeBrand, setActiveBrand, addBrand } = useApp()

  return (
    <>
      <div className="row between" style={{ alignItems: 'flex-end' }}>
        <div>
          <h1 className="page-h1">All <em>brands</em></h1>
          <p className="page-sub">Switch between brand profiles. Each one has its own dashboard, scripts, and scheduler.</p>
        </div>
        <button className="btn-tp primary" onClick={() => {
          const n = prompt('Brand name?')
          if (n) addBrand({ name: n })
        }}>+ Add brand</button>
      </div>

      <div className="grid cols-3">
        {state.brands.map(b => {
          const active = b.id === activeBrand?.id
          return (
            <div key={b.id} className="card-tp" style={{ padding: 24 }}>
              {active && <div className="eyebrow eyebrow-accent">Active</div>}
              <div className="row" style={{ gap: 12, marginTop: 6, marginBottom: 4 }}>
                <div style={{ width: 44, height: 44, borderRadius: 8, background: b.primary || 'var(--ink)', color: 'var(--paper)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'Fraunces, serif', fontSize: 20 }}>
                  {b.name.charAt(0).toUpperCase()}
                </div>
                <h3 style={{ fontSize: 22 }}>{b.name}</h3>
              </div>
              <div className="muted small">{b.niche || 'No niche set'}</div>
              <div className="row" style={{ gap: 8, marginTop: 20 }}>
                <button className="btn-tp ghost" onClick={() => setActiveBrand(b.id)}>Set active</button>
                <Link to={`/brands/${b.id}`} className="btn-tp dark">Open workspace →</Link>
              </div>
            </div>
          )
        })}
      </div>
    </>
  )
}
