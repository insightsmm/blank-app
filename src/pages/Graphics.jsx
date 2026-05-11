import { useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

const STYLES = ['Bold','Editorial','Minimal','Luxury','Playful','Corporate','Modern Serif']
const CATS = ['All','Carousels','Posts','Stories','Quotes','Reels']

const DIMS = {
  Carousels: '1080×1350',
  Posts: '1080×1080',
  Stories: '1080×1920',
  Quotes: '1080×1080',
  Reels: '1080×1920',
}

function makeTpl(category, count) {
  const list = []
  for (let i = 1; i <= count; i++) {
    const style = STYLES[i % STYLES.length]
    list.push({
      id: `${category}-${i}`,
      category,
      style,
      name: `${style} ${category.replace(/s$/, '')} ${i}`,
      slides: category === 'Carousels' ? (3 + (i % 6)) : null,
      dims: DIMS[category],
    })
  }
  return list
}

const TEMPLATES = {
  Carousels: makeTpl('Carousels', 40),
  Posts:     makeTpl('Posts', 25),
  Stories:   makeTpl('Stories', 20),
  Quotes:    makeTpl('Quotes', 12),
  Reels:     makeTpl('Reels', 12),
}

function thumbGradient(t) {
  const palette = {
    Bold:         ['#1a1a1a', '#cf5a36'],
    Editorial:    ['#f4ead5', '#1a1a1a'],
    Minimal:      ['#eee8de', '#cdc4b3'],
    Luxury:       ['#0e0e10', '#b58a4a'],
    Playful:      ['#ffd2b8', '#cf5a36'],
    Corporate:    ['#dde6ef', '#1f3a5f'],
    'Modern Serif': ['#eadfd0', '#5a2a1f'],
  }[t.style] || ['#eee', '#aaa']
  return `linear-gradient(135deg, ${palette[0]} 0%, ${palette[1]} 100%)`
}

function TemplateCard({ t }) {
  return (
    <div className="gx-card">
      <div className="gx-thumb" style={{ background: thumbGradient(t) }}>
        {t.slides && <div className="slides">{t.slides} slides</div>}
        <div style={{ position: 'absolute', bottom: 12, left: 12, color: t.style === 'Editorial' || t.style === 'Minimal' || t.style === 'Playful' ? '#1a1a1a' : 'white', fontFamily: 'Fraunces, Georgia, serif', fontSize: 22, fontStyle: 'italic', textShadow: '0 2px 6px rgba(0,0,0,.15)' }}>
          {t.style}
        </div>
      </div>
      <div className="gx-card-meta">
        <div style={{ fontSize: 13, fontWeight: 500 }}>{t.name}</div>
        <div className="muted tiny">{t.style} · {t.dims}</div>
      </div>
    </div>
  )
}

function ScrollRow({ title, items }) {
  const ref = useRef(null)
  return (
    <div style={{ marginBottom: 40 }}>
      <div className="row between" style={{ marginBottom: 12 }}>
        <h3 style={{ fontFamily: 'Fraunces, Georgia, serif', fontSize: 24 }}>{title}</h3>
        <div className="row" style={{ gap: 6 }}>
          <button className="btn-tp ghost" onClick={() => ref.current?.scrollBy({ left: -400, behavior: 'smooth' })}>←</button>
          <button className="btn-tp ghost" onClick={() => ref.current?.scrollBy({ left:  400, behavior: 'smooth' })}>→</button>
          <button className="btn-tp ghost">See all →</button>
        </div>
      </div>
      <div className="gx-scroll" ref={ref}>
        {items.map(t => <TemplateCard key={t.id} t={t} />)}
      </div>
    </div>
  )
}

export default function Graphics() {
  const [tab, setTab] = useState('Templates')
  const [style, setStyle] = useState('All styles')
  const [cat, setCat] = useState('All')
  const [q, setQ] = useState('')

  const filter = (arr) => arr.filter(t =>
    (style === 'All styles' || t.style === style) &&
    (q.trim() === '' || t.name.toLowerCase().includes(q.toLowerCase()))
  )

  return (
    <>
      <header style={{ padding: '20px 28px', borderBottom: '1px solid var(--border)', background: 'var(--paper)' }}>
        <Link to="/app" className="muted small">← Back to app</Link>
      </header>

      <section className="gx-hero">
        <div className="container">
          <h1 className="display-h1" style={{ fontSize: 'clamp(40px, 6vw, 64px)' }}>
            What will you <em>design</em> today?
          </h1>
          <p style={{ fontSize: 18, color: 'var(--muted)', maxWidth: 620 }}>
            Premium templates for carousels, posts, stories & reel covers.
          </p>
          <div className="row" style={{ gap: 8, marginTop: 24, maxWidth: 640 }}>
            <input style={{ flex: 1 }} placeholder="Search templates…" value={q} onChange={e => setQ(e.target.value)} />
            <button className="btn-tp primary">Search</button>
          </div>
          <div className="row" style={{ gap: 6, marginTop: 16, flexWrap: 'wrap' }}>
            {CATS.map(c => (
              <button key={c} onClick={() => setCat(c)} className={`btn-tp ${cat === c ? 'dark' : 'ghost'}`}>
                {c}
              </button>
            ))}
          </div>
        </div>
      </section>

      <section style={{ padding: '40px 0 80px', background: 'var(--paper)' }}>
        <div className="container">
          <div className="tabs">
            {['Templates','My Designs'].map(t => (
              <button key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>{t}</button>
            ))}
          </div>

          <div className="row" style={{ gap: 6, flexWrap: 'wrap', marginBottom: 28 }}>
            {['All styles', ...STYLES].map(s => (
              <button key={s} className={`btn-tp ${style === s ? 'dark' : 'ghost'}`} onClick={() => setStyle(s)} style={{ borderRadius: 999 }}>
                {s}
              </button>
            ))}
          </div>

          {tab === 'Templates' ? (
            <>
              {(cat === 'All' || cat === 'Carousels') && <ScrollRow title="Carousels (40)" items={filter(TEMPLATES.Carousels)} />}
              {(cat === 'All' || cat === 'Posts')     && <ScrollRow title="Single posts (25)" items={filter(TEMPLATES.Posts)} />}
              {(cat === 'All' || cat === 'Stories')   && <ScrollRow title="Stories (20)" items={filter(TEMPLATES.Stories)} />}
              {(cat === 'All' || cat === 'Quotes')    && <ScrollRow title="Quote cards (12)" items={filter(TEMPLATES.Quotes)} />}
              {(cat === 'All' || cat === 'Reels')     && <ScrollRow title="Reel covers (12+)" items={filter(TEMPLATES.Reels)} />}
            </>
          ) : (
            <div className="card-tp" style={{ textAlign: 'center', padding: 60 }}>
              <p style={{ marginBottom: 12 }}>You haven't designed anything yet.</p>
              <button className="btn-tp primary" onClick={() => setTab('Templates')}>Start from a template →</button>
            </div>
          )}
        </div>
      </section>
    </>
  )
}
