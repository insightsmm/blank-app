import { useState } from 'react'
import { Link } from 'react-router-dom'

const FORMATS = [
  { id:1,  type:'Reels',    title:'POV Reel',                  hook:'POV: when [insert universal moment]…',                                          desc:'First-person framing builds instant intimacy. Hook lands in the first 0.6s.', tags:['hook','identity','shareable'] },
  { id:2,  type:'Reels',    title:'Green Screen Reaction',     hook:'Wait, you actually believe this?',                                              desc:'Greenscreen a screenshot, react in real time. Polarizing = saveable.',          tags:['contrarian','trend-jack'] },
  { id:3,  type:'Reels',    title:'Before / After Transformation', hook:'This is what 90 days looks like →',                                          desc:'Side-by-side visual proof. Shareable because the outcome is undeniable.',       tags:['proof','save-bait'] },
  { id:4,  type:'Reels',    title:'Storytime / Confession',    hook:'I almost shut the business down. Here\'s why I didn\'t.',                       desc:'Long-watch trust builder. Use for high-context offers.',                        tags:['story','trust','long-watch'] },
  { id:5,  type:'Carousel', title:'Numbered List Carousel',    hook:'7 [niche] mistakes that cost me $50k.',                                         desc:'Save-bait. Each slide = one mistake + the fix.',                                tags:['save-bait','evergreen'] },
  { id:6,  type:'Carousel', title:'Myth vs Truth Carousel',    hook:'What everyone tells you vs what actually works.',                               desc:'Two-column carousel. Contrarian framing wins shares.',                          tags:['contrarian','education'] },
  { id:7,  type:'Carousel', title:'Framework Carousel',        hook:'The 4-step framework I use to [result].',                                       desc:'Authority builder. Naming the framework = ownership.',                          tags:['authority','save-bait'] },
  { id:8,  type:'Carousel', title:'Swipe-Through Tutorial',    hook:'How to [outcome] in under 10 minutes →',                                        desc:'Step-by-step. Last slide is the CTA.',                                          tags:['education','lead-gen'] },
  { id:9,  type:'Reels',    title:'Talking Head — 3 Act',      hook:'Most [niche] people get this wrong. Here\'s the fix.',                          desc:'3 beats: contrarian claim → proof → reframe. 45-60s.',                          tags:['authority','evergreen'] },
  { id:10, type:'Reels',    title:'ASMR Process / Satisfying', hook:'Watch me build a [thing] from scratch.',                                        desc:'Visual + audio loop. Explore-page bait.',                                       tags:['loopable','explore-bait'] },
  { id:11, type:'Reels',    title:'Stitch-Style Reaction',     hook:'Stitch this — here\'s what they got wrong.',                                    desc:'Borrow reach from a trending take. Add your unique angle.',                     tags:['trend-jack','borrowed-reach'] },
  { id:12, type:'Story',    title:'This or That Poll (Story)', hook:'Pick one: A or B?',                                                             desc:'Quick engagement + audience research in one tap.',                              tags:['engagement','research'] },
  { id:13, type:'Reels',    title:'Behind the Scenes',         hook:'What a [role] actually does on a Tuesday.',                                     desc:'Day-in-the-life. Builds parasocial trust fast.',                                tags:['relatable','trust'] },
  { id:14, type:'Photo',    title:'Quote Card Photo',          hook:'One line that hits.',                                                            desc:'A high-contrast quote photo. Easiest share format on Instagram.',               tags:['brand','shareable'] },
]

const FILTERS = [
  { id: 'all',      label: 'All (14)' },
  { id: 'Reels',    label: 'Reels (8)' },
  { id: 'Carousel', label: 'Carousel (4)' },
  { id: 'Story',    label: 'Story (1)' },
  { id: 'Photo',    label: 'Photo (1)' },
]

export default function FormatLibrary() {
  const [filter, setFilter] = useState('all')
  const shown = FORMATS.filter(f => filter === 'all' ? true : f.type === filter)

  return (
    <>
      <h1 className="page-h1">Format Library — <em>Instagram</em></h1>
      <p className="page-sub">
        The viral formats actually working on Instagram right now. Each one comes with the hook, structure, and an example you can adapt to your brand.
      </p>

      <div className="tabs">
        {FILTERS.map(f => (
          <button key={f.id} className={`tab ${filter === f.id ? 'active' : ''}`} onClick={() => setFilter(f.id)}>
            {f.label}
          </button>
        ))}
      </div>

      <div className="grid cols-3">
        {shown.map(f => (
          <div key={f.id} className="card-tp format-card">
            <div>
              <span className="pill">{f.type}</span>
            </div>
            <h3>{f.title}</h3>
            <div className="eyebrow">Hook template</div>
            <div className="quote">"{f.hook}"</div>
            <p className="muted small" style={{ margin: 0 }}>{f.desc}</p>
            <div className="tags">{f.tags.map(t => <span key={t} className="tag">{t}</span>)}</div>
            <div className="row" style={{ gap: 8, marginTop: 8 }}>
              <button className="btn-tp ghost">View structure →</button>
              <button className="btn-tp ghost" onClick={() => navigator.clipboard?.writeText(f.hook)}>Copy</button>
              <Link to="/app/clarity" className="btn-tp primary">Generate script ✨</Link>
            </div>
          </div>
        ))}
      </div>
    </>
  )
}
