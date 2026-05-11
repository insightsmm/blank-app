import { useMemo, useState } from 'react'
import { useApp } from '../../state/AppState.jsx'

const DOW = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
const PATTERN = ['teach','offer','teach','proof','teach','teach','proof']

function tpoForDate(d) {
  // Monday = 0
  const idx = (d.getDay() + 6) % 7
  return PATTERN[idx]
}

function monthMatrix(year, month) {
  const first = new Date(year, month, 1)
  const startDow = (first.getDay() + 6) % 7
  const last = new Date(year, month + 1, 0).getDate()
  const cells = []
  for (let i = 0; i < startDow; i++) cells.push(null)
  for (let d = 1; d <= last; d++) cells.push(new Date(year, month, d))
  while (cells.length % 7 !== 0) cells.push(null)
  return cells
}

export default function TPOStudio() {
  const { activeBrand } = useApp()
  const today = new Date()
  const [view, setView] = useState({ y: today.getFullYear(), m: today.getMonth() })
  const cells = useMemo(() => monthMatrix(view.y, view.m), [view])
  const monthLabel = new Date(view.y, view.m, 1).toLocaleString(undefined, { month: 'long', year: 'numeric' })

  const prev = () => {
    const d = new Date(view.y, view.m - 1, 1)
    setView({ y: d.getFullYear(), m: d.getMonth() })
  }
  const next = () => {
    const d = new Date(view.y, view.m + 1, 1)
    setView({ y: d.getFullYear(), m: d.getMonth() })
  }

  const counts = cells.reduce((acc, c) => {
    if (!c) return acc
    const k = tpoForDate(c)
    acc[k] = (acc[k] || 0) + 1
    return acc
  }, {})

  return (
    <>
      <h1 className="page-h1">TPO <em>Studio</em></h1>
      <p className="page-sub">{activeBrand?.name} • monthly Teach / Proof / Offer plan.</p>

      <div className="card-tp">
        <div className="calendar">
          <div className="calendar-head">
            <button className="btn-tp ghost" onClick={prev}>← Prev</button>
            <div className="calendar-month">{monthLabel}</div>
            <button className="btn-tp ghost" onClick={next}>Next →</button>
          </div>

          <div className="calendar-grid">
            {DOW.map(d => <div key={d} className="cal-dow">{d}</div>)}
            {cells.map((c, i) => {
              if (!c) return <div key={i} className="cal-day empty" />
              const tpo = tpoForDate(c)
              const isToday = c.toDateString() === today.toDateString()
              return (
                <div key={i} className={`cal-day ${isToday ? 'today' : ''}`}>
                  <div className="num">{c.getDate()}</div>
                  <span className={`pill ${tpo}`} style={{ fontSize: 9, padding: '2px 7px' }}>
                    {tpo}
                  </span>
                </div>
              )
            })}
          </div>
        </div>

        <div className="row" style={{ gap: 16, marginTop: 24, flexWrap: 'wrap' }}>
          <div><span className="pill teach">Teach</span> <span className="muted small" style={{ marginLeft: 6 }}>{counts.teach || 0} days</span></div>
          <div><span className="pill proof">Proof</span> <span className="muted small" style={{ marginLeft: 6 }}>{counts.proof || 0} days</span></div>
          <div><span className="pill offer">Offer</span> <span className="muted small" style={{ marginLeft: 6 }}>{counts.offer || 0} days</span></div>
        </div>
      </div>

      <div className="card-tp" style={{ marginTop: 20 }}>
        <h3 style={{ fontSize: 20, marginBottom: 8 }}>How TPO works</h3>
        <div className="grid cols-3">
          <div>
            <span className="pill teach">Teach</span>
            <p className="muted small" style={{ marginTop: 10 }}>
              Frameworks, mental models, how-tos. Builds authority. 4x per week.
            </p>
          </div>
          <div>
            <span className="pill proof">Proof</span>
            <p className="muted small" style={{ marginTop: 10 }}>
              Receipts, results, screenshots, testimonials. Builds trust. 2x per week.
            </p>
          </div>
          <div>
            <span className="pill offer">Offer</span>
            <p className="muted small" style={{ marginTop: 10 }}>
              Pitch, sales angle, CTA-led content. Books calls. 1x per week.
            </p>
          </div>
        </div>
      </div>
    </>
  )
}
