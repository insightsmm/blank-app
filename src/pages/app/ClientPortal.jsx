import { useState } from 'react'
import { useApp } from '../../state/AppState.jsx'

export default function ClientPortal() {
  const { state, activeBrand, addPortalLink } = useApp()
  const [reviewer, setReviewer] = useState('')

  const generate = (e) => {
    e.preventDefault()
    const token = Math.random().toString(36).slice(2, 10)
    const url = `${window.location.origin}/portal/${activeBrand?.id}/${token}`
    addPortalLink({ reviewer: reviewer || 'Untitled reviewer', url, brandId: activeBrand?.id })
    setReviewer('')
  }

  return (
    <>
      <h1 className="page-h1">Client <em>Portal</em></h1>
      <p className="page-sub">Share-only review links for {activeBrand?.name}.</p>

      <div className="card-tp">
        <h3 style={{ fontSize: 20, marginBottom: 12 }}>Generate a review link</h3>
        <form onSubmit={generate} className="row" style={{ gap: 8 }}>
          <input
            style={{ flex: 1 }}
            value={reviewer}
            onChange={e => setReviewer(e.target.value)}
            placeholder="Client / reviewer name (optional)"
          />
          <button type="submit" className="btn-tp dark">Generate link</button>
        </form>

        <hr />

        {state.portalLinks.length === 0 ? (
          <p className="muted small">No links yet. Generate one to share with your client.</p>
        ) : (
          <div className="stack" style={{ gap: 10 }}>
            {state.portalLinks.map(l => (
              <div key={l.id} className="row between" style={{ padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
                <div>
                  <div style={{ fontSize: 14 }}>{l.reviewer}</div>
                  <a href={l.url} className="muted tiny" onClick={(e) => e.preventDefault()}>{l.url}</a>
                </div>
                <button
                  className="btn-tp ghost"
                  onClick={() => navigator.clipboard?.writeText(l.url)}
                >Copy</button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card-tp" style={{ marginTop: 20 }}>
        <h3 style={{ fontSize: 20, marginBottom: 4 }}>Recent feedback</h3>
        <p className="muted small" style={{ marginBottom: 16 }}>Approvals and change requests submitted by clients.</p>
        <p className="muted small">No client feedback yet.</p>
      </div>
    </>
  )
}
