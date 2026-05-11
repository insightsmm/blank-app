import { useState } from 'react'
import { useApp } from '../../state/AppState.jsx'

const TYPES = ['Testimonial', 'Result', 'Screenshot', 'Case study', 'Review']

export default function ProofVault() {
  const { state, addProof, deleteProof } = useApp()
  const [filter, setFilter] = useState('All')
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState({ type: 'Testimonial', source: '', content: '' })

  const shown = filter === 'All' ? state.proof : state.proof.filter(p => p.type === filter)

  const submit = (e) => {
    e.preventDefault()
    if (!draft.content) return
    addProof(draft)
    setDraft({ type: 'Testimonial', source: '', content: '' })
    setOpen(false)
  }

  return (
    <>
      <div className="row between" style={{ alignItems: 'flex-end' }}>
        <div>
          <h1 className="page-h1">Proof <em>Vault</em></h1>
          <p className="page-sub">
            Your credibility library — testimonials, results, screenshots, case studies. Pull from here when writing posts.
          </p>
        </div>
        <button className="btn-tp primary" onClick={() => setOpen(true)}>+ Add proof</button>
      </div>

      <div className="tabs">
        {['All', ...TYPES].map(t => (
          <button key={t} className={`tab ${filter === t ? 'active' : ''}`} onClick={() => setFilter(t)}>
            {t}
          </button>
        ))}
      </div>

      {open && (
        <form className="card-tp" onSubmit={submit} style={{ marginBottom: 20 }}>
          <h3 style={{ marginBottom: 12 }}>Add proof</h3>
          <div className="grid cols-2">
            <div>
              <div className="eyebrow" style={{ marginBottom: 6 }}>Type</div>
              <select value={draft.type} onChange={e => setDraft({ ...draft, type: e.target.value })}>
                {TYPES.map(t => <option key={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <div className="eyebrow" style={{ marginBottom: 6 }}>Source / client</div>
              <input value={draft.source} onChange={e => setDraft({ ...draft, source: e.target.value })} placeholder="e.g. Sarah from Acme Coaching" />
            </div>
          </div>
          <div style={{ marginTop: 12 }}>
            <div className="eyebrow" style={{ marginBottom: 6 }}>Content</div>
            <textarea
              value={draft.content}
              onChange={e => setDraft({ ...draft, content: e.target.value })}
              placeholder="Paste the testimonial, result, or describe the screenshot…"
            />
          </div>
          <div className="row" style={{ gap: 8, marginTop: 16 }}>
            <button type="submit" className="btn-tp primary">Save to vault</button>
            <button type="button" className="btn-tp ghost" onClick={() => setOpen(false)}>Cancel</button>
          </div>
        </form>
      )}

      {shown.length === 0 ? (
        <div className="card-tp" style={{ textAlign: 'center', padding: 60 }}>
          <div style={{ width: 56, height: 56, margin: '0 auto', borderRadius: '50%', border: '2px solid var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent)', fontFamily: 'Fraunces, serif', fontSize: 24 }}>$</div>
          <p style={{ marginTop: 16, marginBottom: 4 }}>No proof yet — start banking your credibility.</p>
          <p className="muted small" style={{ marginBottom: 20 }}>Drop in a testimonial, a screenshot, or a result.</p>
          <button className="btn-tp primary" onClick={() => setOpen(true)}>+ Add your first proof</button>
        </div>
      ) : (
        <div className="grid cols-2">
          {shown.map(p => (
            <div key={p.id} className="card-tp">
              <div className="row between" style={{ marginBottom: 8 }}>
                <span className="pill">{p.type}</span>
                <button className="btn-tp ghost" style={{ padding: '4px 8px', fontSize: 11 }} onClick={() => deleteProof(p.id)}>Delete</button>
              </div>
              {p.source && <div className="eyebrow eyebrow-accent">{p.source}</div>}
              <div style={{ fontFamily: 'Fraunces, Georgia, serif', fontStyle: 'italic', marginTop: 8 }}>"{p.content}"</div>
            </div>
          ))}
        </div>
      )}
    </>
  )
}
