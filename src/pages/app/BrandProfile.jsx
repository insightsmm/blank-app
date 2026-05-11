import { useState, useEffect } from 'react'
import { useApp } from '../../state/AppState.jsx'

export default function BrandProfile() {
  const { state, activeBrand, addBrand, updateBrand, deleteBrand, setActiveBrand } = useApp()
  const [form, setForm] = useState(activeBrand || {})

  useEffect(() => { setForm(activeBrand || {}) }, [activeBrand?.id])

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))
  const save = (e) => { e.preventDefault(); updateBrand(activeBrand.id, form) }

  return (
    <>
      <h1 className="page-h1">Brand <em>profile</em></h1>
      <p className="page-sub">The foundation every script, plan, and post is built on.</p>

      <div className="card-tp">
        <div className="row between" style={{ marginBottom: 16 }}>
          <h3 style={{ fontSize: 18 }}>Your brands</h3>
          <button className="btn-tp ghost" onClick={() => {
            const n = prompt('Brand name?')
            if (n) addBrand({ name: n })
          }}>+ Add another brand</button>
        </div>
        <div className="row wrap" style={{ gap: 8 }}>
          {state.brands.map(b => {
            const active = b.id === activeBrand?.id
            return (
              <button
                key={b.id}
                onClick={() => setActiveBrand(b.id)}
                className={`btn-tp ${active ? 'primary' : 'ghost'}`}
                style={{ borderRadius: 999 }}
              >
                {active && '★ '}{b.name}
              </button>
            )
          })}
        </div>
      </div>

      {activeBrand && (
        <form onSubmit={save} className="card-tp" style={{ marginTop: 20 }}>
          <div className="eyebrow eyebrow-accent" style={{ marginBottom: 4 }}>Editing</div>
          <h3 style={{ fontSize: 22, marginBottom: 4 }}>{activeBrand.name}</h3>
          <p className="muted small" style={{ marginBottom: 24 }}>Update this brand's identity.</p>

          <div className="grid cols-2">
            <div>
              <div className="eyebrow" style={{ marginBottom: 6 }}>Brand name</div>
              <input value={form.name || ''} onChange={e => set('name', e.target.value)} />
            </div>
            <div>
              <div className="eyebrow" style={{ marginBottom: 6 }}>Niche / industry</div>
              <input value={form.niche || ''} onChange={e => set('niche', e.target.value)} placeholder="e.g. social media management for service businesses" />
            </div>
          </div>

          <div style={{ marginTop: 16 }}>
            <div className="eyebrow" style={{ marginBottom: 6 }}>Target audience</div>
            <input value={form.audience || ''} onChange={e => set('audience', e.target.value)} placeholder="e.g. agency owners doing $20k-$80k/mo" />
          </div>

          <div style={{ marginTop: 16 }}>
            <div className="eyebrow" style={{ marginBottom: 6 }}>Voice (samples or description)</div>
            <textarea value={form.voice || ''} onChange={e => set('voice', e.target.value)} placeholder="Describe the tone, energy, or paste a few sample lines…" />
          </div>

          <hr />
          <div className="row" style={{ gap: 16, alignItems: 'flex-start' }}>
            <div style={{ width: 72, height: 72, background: 'var(--ink)', color: 'var(--paper)', borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'Fraunces, serif', fontSize: 32 }}>
              {(form.name || '?').charAt(0).toUpperCase()}
            </div>
            <button type="button" className="btn-tp ghost">Upload logo</button>
          </div>

          <div className="grid cols-2" style={{ marginTop: 24 }}>
            <div>
              <div className="eyebrow" style={{ marginBottom: 6 }}>Primary color</div>
              <div className="color-row">
                <input type="color" value={form.primary || '#1a1a1a'} onChange={e => set('primary', e.target.value)} />
                <input value={form.primary || ''} onChange={e => set('primary', e.target.value)} />
              </div>
            </div>
            <div>
              <div className="eyebrow" style={{ marginBottom: 6 }}>Accent color</div>
              <div className="color-row">
                <input type="color" value={form.accent || '#cf5a36'} onChange={e => set('accent', e.target.value)} />
                <input value={form.accent || ''} onChange={e => set('accent', e.target.value)} />
              </div>
            </div>
          </div>

          <div className="row" style={{ gap: 8, marginTop: 24, justifyContent: 'space-between' }}>
            <button type="submit" className="btn-tp primary">Save changes</button>
            <button
              type="button"
              className="btn-tp danger"
              onClick={() => {
                if (state.brands.length === 1) { alert('You need at least one brand.'); return }
                if (confirm('Delete this brand?')) deleteBrand(activeBrand.id)
              }}
            >Delete brand</button>
          </div>
        </form>
      )}
    </>
  )
}
