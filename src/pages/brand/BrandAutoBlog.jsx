import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useApp } from '../../state/AppState.jsx'

export default function BrandAutoBlog() {
  const { id } = useParams()
  const { state, setAutoBlog } = useApp()
  const brand = state.brands.find(b => b.id === id) || state.brands[0]
  const existing = state.autoBlog[id] || {}

  const [form, setForm] = useState({
    businessName: brand?.name || '',
    niche: brand?.niche || '',
    author: '',
    cta: '',
    approvalEmail: '',
    perDay: 1,
    connected: true,
    activated: false,
    ...existing,
  })
  useEffect(() => { setForm(f => ({ ...f, ...existing })) }, [id])

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const activate = (e) => {
    e.preventDefault()
    setAutoBlog(id, { ...form, activated: true })
    alert('Auto Blog activated! A preview will land in your approval email within 5 minutes.')
  }

  return (
    <>
      <h1 className="page-h1">wordpress.com site is connected. Set up your <em>daily blog</em>.</h1>
      <p className="page-sub">Step 2 of 2 — Activate.</p>

      <div className="connected-banner">
        <div><span className="green-dot" />{form.businessName || 'Your site'} is connected to WordPress</div>
        <button className="btn-tp ghost" onClick={() => set('connected', false)}>Disconnect</button>
      </div>

      <form onSubmit={activate} className="card-tp">
        <h3 style={{ fontSize: 22, marginBottom: 4 }}>Set up auto-blog</h3>
        <p className="muted small" style={{ marginBottom: 24 }}>Tell us about the brand and we'll start producing on your schedule.</p>

        <div className="grid cols-2">
          <div>
            <div className="eyebrow" style={{ marginBottom: 6 }}>Business name *</div>
            <input required value={form.businessName} onChange={e => set('businessName', e.target.value)} />
          </div>
          <div>
            <div className="eyebrow" style={{ marginBottom: 6 }}>Niche *</div>
            <input required placeholder="e.g. plant-based skincare" value={form.niche} onChange={e => set('niche', e.target.value)} />
          </div>
          <div>
            <div className="eyebrow" style={{ marginBottom: 6 }}>Author name / byline *</div>
            <input required value={form.author} onChange={e => set('author', e.target.value)} />
          </div>
          <div>
            <div className="eyebrow" style={{ marginBottom: 6 }}>Approval email *</div>
            <input required type="email" value={form.approvalEmail} onChange={e => set('approvalEmail', e.target.value)} />
          </div>
        </div>

        <div style={{ marginTop: 16 }}>
          <div className="eyebrow" style={{ marginBottom: 6 }}>Call to action (optional)</div>
          <textarea value={form.cta} onChange={e => set('cta', e.target.value)} placeholder="Sentence shown at the end of each post." />
        </div>

        <div style={{ marginTop: 16 }}>
          <div className="eyebrow" style={{ marginBottom: 8 }}>Posts per day</div>
          <div className="seg">
            {[1,2,3].map(n => (
              <button key={n} type="button" className={form.perDay === n ? 'active' : ''} onClick={() => set('perDay', n)}>{n}</button>
            ))}
          </div>
        </div>

        <div className="row" style={{ gap: 8, marginTop: 24 }}>
          <button type="submit" className="btn-tp primary">Activate & generate preview</button>
          <button type="button" className="btn-tp ghost">Test connection</button>
        </div>

        {form.activated && (
          <div className="connected-banner" style={{ marginTop: 20 }}>
            <div><span className="green-dot" />Auto Blog active — {form.perDay} post{form.perDay === 1 ? '' : 's'}/day queued for approval.</div>
          </div>
        )}
      </form>
    </>
  )
}
