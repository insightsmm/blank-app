import { useState } from 'react'
import { Link } from 'react-router-dom'

const STATS = [
  { n: '3.5×',  s: 'organic traffic in 90 days' },
  { n: '+434%', s: 'indexed pages' },
  { n: '+97%',  s: 'backlinks earned' },
  { n: '+67%',  s: 'more inbound leads' },
]

const STEPS = [
  { n: '01', h: 'Connect your site',  p: 'WordPress, Webflow, Ghost. One-click OAuth.' },
  { n: '02', h: 'Configure the brand', p: 'Niche, byline, CTA, posts-per-day cadence.' },
  { n: '03', h: 'Approve the first batch', p: 'Posts land in your inbox. Approve, edit, or reject in one click.' },
  { n: '04', h: 'Watch it compound',  p: 'Daily SEO content. Internal links auto-built. Topic clusters maintained.' },
]

const FEATURES = [
  'On-brand voice (mirrors your existing posts)',
  'SEO-optimized titles, descriptions, schema',
  'Internal linking across new + existing posts',
  'Hero image generation (no stock soup)',
  'Approval queue with one-click publish',
  'Daily posting on autopilot',
  'Topic cluster building',
  'Built-in plagiarism + fact checks',
]

const COMP = [
  { feature: 'Cost / month',          ab: '$47',     hire: '$2,000+',   diy: 'Free (your time)' },
  { feature: 'Posts per day',         ab: '1–3',     hire: '0–1',       diy: 'Maybe 1/week' },
  { feature: 'On-brand voice',        ab: 'Yes',     hire: 'Yes',       diy: 'Yes' },
  { feature: 'SEO research baked-in', ab: 'Yes',     hire: 'Sometimes', diy: 'No' },
  { feature: 'Time per post',         ab: '2 min',   hire: '24-72h',    diy: '4-6h' },
  { feature: 'Internal linking',      ab: 'Auto',    hire: 'Manual',    diy: 'Forgotten' },
]

const FAQS = [
  { q: 'Will Google penalize AI content?', a: 'No. Google penalizes thin, low-quality content. Auto Blog produces long-form, well-researched articles with original framing and proper structure.' },
  { q: 'Can I edit posts before they publish?', a: 'Yes. Every post lands in your approval queue. You can approve as-is, edit, or reject.' },
  { q: 'Which platforms are supported?', a: 'WordPress, Webflow, and Ghost on launch. Shopify Blogs and Squarespace coming Q4.' },
  { q: 'How does it learn my voice?', a: 'You feed it 3–5 existing posts during setup. The voice model is calibrated per brand workspace.' },
]

export default function AutoBlogMarketing() {
  const [openFaq, setOpenFaq] = useState(0)
  return (
    <>
      <section className="hero container">
        <div className="ebr eyebrow eyebrow-accent">Launching Q3 2026</div>
        <h1 className="display-h1">SEO blog posts that <em>publish themselves</em>.</h1>
        <p style={{ fontSize: 20, color: 'var(--muted)', maxWidth: 680 }}>
          Auto Blog produces 1–3 long-form, on-brand articles every day. You approve.
          They publish. Google indexes. Leads compound.
        </p>
        <div className="ctas">
          <Link to="/login" className="btn-tp primary large">Get early access →</Link>
          <Link to="/pricing" className="btn-tp ghost large">See pricing</Link>
        </div>
      </section>

      <section className="section" style={{ background: 'var(--paper-2)' }}>
        <div className="container grid cols-4">
          {STATS.map(s => (
            <div key={s.s} style={{ textAlign: 'center' }}>
              <div style={{ fontFamily: 'Fraunces, Georgia, serif', fontSize: 52, color: 'var(--accent)' }}>{s.n}</div>
              <div className="muted small">{s.s}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="container">
          <h2 className="section-h2">How <em>it works</em>.</h2>
          <div className="grid cols-4" style={{ marginTop: 32 }}>
            {STEPS.map(s => (
              <div key={s.n} className="card-tp">
                <div style={{ fontFamily: 'Fraunces, Georgia, serif', fontSize: 38, color: 'var(--accent)' }}>{s.n}</div>
                <h3 style={{ fontSize: 18, marginTop: 6 }}>{s.h}</h3>
                <p className="muted small" style={{ marginTop: 6 }}>{s.p}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section" style={{ background: 'var(--paper-3)' }}>
        <div className="container">
          <h2 className="section-h2">What's in the <em>box</em>.</h2>
          <div className="grid cols-2" style={{ marginTop: 24 }}>
            {FEATURES.map(f => (
              <div key={f} className="row" style={{ gap: 10 }}>
                <span style={{ color: 'var(--accent)', fontSize: 18 }}>✓</span>
                <span>{f}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <h2 className="section-h2">Auto Blog vs the <em>alternatives</em>.</h2>
          <div className="card-tp" style={{ marginTop: 24, padding: 0, overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th style={{ padding: 16, textAlign: 'left', borderBottom: '1px solid var(--border)' }}>Feature</th>
                  <th style={{ padding: 16, textAlign: 'left', borderBottom: '1px solid var(--border)', color: 'var(--accent)' }}>Auto Blog</th>
                  <th style={{ padding: 16, textAlign: 'left', borderBottom: '1px solid var(--border)' }}>Hire a writer</th>
                  <th style={{ padding: 16, textAlign: 'left', borderBottom: '1px solid var(--border)' }}>DIY</th>
                </tr>
              </thead>
              <tbody>
                {COMP.map(r => (
                  <tr key={r.feature}>
                    <td style={{ padding: 16, borderBottom: '1px solid var(--border)' }}>{r.feature}</td>
                    <td style={{ padding: 16, borderBottom: '1px solid var(--border)', color: 'var(--accent)' }}>{r.ab}</td>
                    <td style={{ padding: 16, borderBottom: '1px solid var(--border)' }}>{r.hire}</td>
                    <td style={{ padding: 16, borderBottom: '1px solid var(--border)' }}>{r.diy}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <h2 className="section-h2">Questions, <em>answered</em>.</h2>
          <div style={{ maxWidth: 800, marginTop: 32 }}>
            {FAQS.map((f, i) => (
              <div key={i} className="faq-item" onClick={() => setOpenFaq(openFaq === i ? -1 : i)}>
                <div className="row between">
                  <h4>{f.q}</h4>
                  <span style={{ color: 'var(--accent)', fontSize: 22 }}>{openFaq === i ? '−' : '+'}</span>
                </div>
                {openFaq === i && <div className="a">{f.a}</div>}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section style={{ background: 'var(--ink)', color: 'var(--paper)', padding: '80px 24px' }}>
        <div className="container" style={{ textAlign: 'center' }}>
          <h2 className="section-h2" style={{ color: 'var(--paper)' }}>Start <em>compounding</em>.</h2>
          <p style={{ color: 'rgba(255,255,255,.7)', maxWidth: 520, margin: '0 auto 24px' }}>
            Founding members get 50% off Auto Blog for life.
          </p>
          <Link to="/login" className="btn-tp primary large">Get early access →</Link>
        </div>
      </section>
    </>
  )
}
