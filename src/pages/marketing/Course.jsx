import { useEffect } from 'react'
import { Link } from 'react-router-dom'

const SESSIONS = [
  { n: '01', title: 'Clarity', sub: 'Mirror week', desc: 'Define your one-sentence positioning. Build the Clarity Mirror brief. Pick your TPO pillars.' },
  { n: '02', title: 'Consistency', sub: 'Cadence week', desc: 'Set the TPO Studio calendar. Build a 30-day plan you can actually keep.' },
  { n: '03', title: 'Capture', sub: 'Filming week', desc: 'Hooks that work. Camera setup. Filming 30 reels in a single 2-hour batch.' },
  { n: '04', title: 'Credibility', sub: 'Proof week', desc: 'Build your Proof Vault. Turn every win into a citation. Make testimonials inevitable.' },
  { n: '05', title: 'Conversion', sub: 'Offer week', desc: 'Sales angle frameworks. The Offer pillar. Calls-to-action that book calls.' },
  { n: '06', title: 'Compounding', sub: 'Systems week', desc: 'Auto Blog setup. Repurposing engine. Building a content team or staying solo.' },
]

const RESOURCES = [
  { title: 'The TPO Method Playbook (PDF)', size: '12 pages · 2 MB' },
  { title: 'Clarity Mirror Workbook (PDF)',  size: '24 pages · 3.4 MB' },
]

export default function Course() {
  useEffect(() => {
    document.body.classList.add('lab')
    return () => document.body.classList.remove('lab')
  }, [])

  return (
    <div className="lab-section">
      <section style={{ padding: '60px 0 40px' }}>
        <div className="container">
          <div className="pill solid" style={{ background: 'rgba(255,255,255,.08)', color: 'var(--paper)', border: '1px solid var(--lab-border)' }}>
            12-week coaching program · Product 02
          </div>
          <h1 className="display-h1" style={{ marginTop: 24, color: 'var(--paper)' }}>The TPO <em>Method</em>.</h1>
          <p style={{ fontSize: 19, color: 'var(--lab-muted)', maxWidth: 680 }}>
            A six-session live coaching program for service businesses who want a content system that
            actually compounds — without becoming a full-time creator.
          </p>

          <div className="grid cols-3" style={{ marginTop: 40, maxWidth: 600 }}>
            <Stat n="6" s="live sessions" />
            <Stat n="12" s="weeks" />
            <Stat n="0%" s="complete" />
          </div>
        </div>
      </section>

      <section style={{ padding: '20px 0 80px' }}>
        <div className="container" style={{ display: 'grid', gridTemplateColumns: '240px 1fr', gap: 40 }}>
          <aside style={{ background: 'var(--lab-bg-2)', border: '1px solid var(--lab-border)', borderRadius: 12, padding: 20, height: 'fit-content' }}>
            <div className="eyebrow">Program</div>
            <div className="stack" style={{ marginTop: 12, gap: 8 }}>
              <a href="#overview" style={{ color: 'var(--paper)' }}>Overview</a>
              {SESSIONS.map(s => (
                <a key={s.n} href={`#s-${s.n}`} style={{ color: 'var(--lab-muted)' }}>{s.n} · {s.title}</a>
              ))}
            </div>
            <hr style={{ borderColor: 'var(--lab-border)' }} />
            <div className="eyebrow">Progress</div>
            <div style={{ height: 6, borderRadius: 4, background: 'rgba(255,255,255,.1)', marginTop: 8 }}>
              <div style={{ height: 6, borderRadius: 4, background: 'var(--lab-accent)', width: '0%' }} />
            </div>
            <div className="muted tiny" style={{ marginTop: 6 }}>0 / 6 sessions complete</div>
          </aside>

          <div>
            <h2 className="section-h2" id="overview" style={{ color: 'var(--paper)' }}>The six <em>sessions</em>.</h2>
            <div className="grid cols-3" style={{ marginTop: 24 }}>
              {SESSIONS.map(s => (
                <div key={s.n} id={`s-${s.n}`} className="card-tp">
                  <div style={{ fontFamily: 'Fraunces, Georgia, serif', fontSize: 32, color: 'var(--lab-accent)' }}>{s.n}</div>
                  <div className="eyebrow" style={{ marginTop: 4 }}>{s.sub}</div>
                  <h3 style={{ fontSize: 22, marginTop: 4, color: 'var(--paper)' }}>{s.title}</h3>
                  <p style={{ color: 'var(--lab-muted)', marginTop: 8, fontSize: 14 }}>{s.desc}</p>
                </div>
              ))}
            </div>

            <h2 className="section-h2" style={{ color: 'var(--paper)', marginTop: 60 }}>Course <em>resources</em>.</h2>
            <div className="stack" style={{ marginTop: 16 }}>
              {RESOURCES.map(r => (
                <div key={r.title} className="card-tp row between">
                  <div>
                    <div style={{ color: 'var(--paper)' }}>{r.title}</div>
                    <div className="muted tiny" style={{ marginTop: 4 }}>{r.size}</div>
                  </div>
                  <button className="btn-tp" style={{ background: 'var(--lab-accent)', color: 'var(--lab-bg)', borderColor: 'var(--lab-accent)' }}>Download PDF</button>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

function Stat({ n, s }) {
  return (
    <div className="card-tp" style={{ textAlign: 'center' }}>
      <div style={{ fontFamily: 'Fraunces, Georgia, serif', fontSize: 38, color: 'var(--paper)' }}>{n}</div>
      <div className="eyebrow" style={{ marginTop: 4 }}>{s}</div>
    </div>
  )
}
