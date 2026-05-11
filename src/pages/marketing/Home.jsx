import { useState } from 'react'
import { Link } from 'react-router-dom'

const TRAPS = [
  { eb: 'The Trap One', h: 'Random Acts of Content', p: 'You post when inspiration strikes. Then go silent for 11 days. The algorithm punishes inconsistency, not lack of talent.' },
  { eb: 'The Trap Two', h: 'Borrowed Voice Syndrome', p: 'You copy creators in adjacent niches. The content goes flat because it isn\'t actually yours. Audiences smell the imitation.' },
  { eb: 'The Trap Three', h: 'Zero Receipts', p: 'You teach a lot but rarely show proof. Without credibility assets, every offer feels like a cold pitch.' },
  { eb: 'The Fix', h: 'A Headquarters', p: 'One system: clear positioning, a TPO calendar that runs on autopilot, and a vault of proof you can cite at will.' },
]

const PILLARS = [
  { tone: '',        eb: 'Pillar one',  title: 'Clarity',     quote: 'You cannot grow what you cannot articulate.',         power: 'Powered by the Clarity Mirror method' },
  { tone: 'green',   eb: 'Pillar two',  title: 'Consistency', quote: 'The algorithm rewards repetition, not talent.',        power: 'Powered by the TPO method' },
  { tone: 'gold',    eb: 'Pillar three',title: 'Credibility', quote: 'Talk is cheap. Receipts close deals.',                 power: 'Powered by the Proof Vault' },
]

const STEPS = [
  { n: '01', h: 'Calibrate your brand', p: 'Define voice, niche, audience, offer. The Mirror gets sharper with every input.' },
  { n: '02', h: 'Run the Mirror',       p: 'Generate teleprompter-ready scripts for any TPO pillar in 30 seconds.' },
  { n: '03', h: 'Schedule the month',   p: 'TPO Studio drops a 30-day plan that balances Teach / Proof / Offer.' },
  { n: '04', h: 'Bank the proof',       p: 'Every win goes into the vault — cite it next time you post.' },
]

const PRODUCTS = [
  { eb: 'Now in private beta', title: 'TemPO HQ App',       p: 'The dashboard: Clarity Mirror, TPO Studio, Proof Vault, Tasks, Portal.' },
  { eb: 'Now enrolling',       title: 'The TPO Method (course)', p: '12-week coaching program. Six live sessions, async support.' },
  { eb: 'Launching Q3 2026',   title: 'Auto Blog',          p: 'WordPress automation. 1-3 SEO posts per day, on-brand, approval queue.' },
  { eb: 'Coming soon',         title: 'Graphics Studio',    p: 'On-brand templates for carousels, posts, stories, and reel covers.' },
  { eb: 'Coming soon',         title: 'Insight (newsletter)', p: 'Three essays a day on clarity, consistency, credibility.' },
]

const FAQS = [
  { q: 'Who is TemPO HQ for?',                  a: 'Service businesses — lawyers, coaches, agencies, consultants — who sell on the back of their content but can\'t keep the cadence.' },
  { q: 'Do I need a video editor?',             a: 'No. Scripts are teleprompter-ready and TPO Studio plans your monthly cadence. You film, we structure.' },
  { q: 'Is this a Lovable / Supabase product?', a: 'The first internal build was Lovable + Supabase. This is the production rebuild on React + Vite with Supabase Auth.' },
  { q: 'Can I cancel anytime?',                 a: 'Yes. Month-to-month on every plan. Annual is a discount, never a lock-in.' },
]

export default function Home() {
  const [email, setEmail] = useState('')
  const [annual, setAnnual] = useState(false)
  const [openFaq, setOpenFaq] = useState(0)

  return (
    <>
      {/* Hero */}
      <section className="hero container">
        <div className="ebr eyebrow eyebrow-accent">Now in private beta · Spring 2026</div>
        <h1 className="display-h1">The headquarters for content that <em>converts.</em></h1>
        <p style={{ fontSize: 20, color: 'var(--muted)', maxWidth: 680 }}>
          One operating system for clarity, consistency, and credibility. Built for service businesses
          who are tired of treating content like a guessing game.
        </p>
        <div className="ctas">
          <Link to="/app" className="btn-tp primary large">Try the app →</Link>
          <Link to="/course" className="btn-tp ghost large" style={{ borderColor: 'var(--border-strong)' }}>Explore the course</Link>
        </div>
        <div className="built-for">Built for: Lawyers · Coaches · Agencies · Service businesses</div>
      </section>

      {/* Problem */}
      <section className="section dark">
        <div className="container grid cols-2" style={{ alignItems: 'flex-start', gap: 60 }}>
          <h2 className="section-h2">
            You don't have a content problem. You have a <em>system</em> problem.
          </h2>
          <div className="stack" style={{ gap: 14 }}>
            {TRAPS.map(t => (
              <div key={t.eb} style={{ border: '1px solid rgba(255,255,255,.12)', borderRadius: 10, padding: 18 }}>
                <div className="eyebrow eyebrow-accent">{t.eb}</div>
                <h3 style={{ fontSize: 22, margin: '6px 0 6px' }}>{t.h}</h3>
                <p className="muted small" style={{ color: 'rgba(255,255,255,.7)' }}>{t.p}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 3Cs */}
      <section className="section">
        <div className="container">
          <h2 className="section-h2" style={{ textAlign: 'center' }}>The 3Cs of <em>branding</em>.</h2>
          <p className="muted" style={{ textAlign: 'center', maxWidth: 640, margin: '0 auto 60px' }}>
            Three pillars. Three tools. One operating system.
          </p>
          <div className="grid cols-3">
            {PILLARS.map(p => (
              <div key={p.title} className={`pillar-card ${p.tone}`}>
                <div className="eyebrow">{p.eb}</div>
                <h3 style={{ fontSize: 36, margin: '12px 0' }}>{p.title}</h3>
                <p style={{ fontFamily: 'Fraunces, Georgia, serif', fontStyle: 'italic', fontSize: 17, color: 'var(--ink)' }}>"{p.quote}"</p>
                <div className="eyebrow eyebrow-accent" style={{ marginTop: 16 }}>{p.power}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Frameworks */}
      <section className="section dark">
        <div className="container">
          <h2 className="section-h2">Inside the <em>HQ</em>.</h2>
          <p style={{ color: 'rgba(255,255,255,.7)', maxWidth: 640, marginBottom: 40 }}>
            Three frameworks that the entire product is built on.
          </p>

          <div className="card-tp" style={{ background: 'rgba(255,255,255,.04)', border: '1px solid rgba(255,255,255,.12)', color: 'var(--paper)', padding: 32, marginBottom: 20 }}>
            <div className="eyebrow eyebrow-accent">Framework one</div>
            <h3 style={{ fontSize: 32, marginTop: 6 }}>The TPO Method</h3>
            <div className="grid cols-3" style={{ marginTop: 24 }}>
              <div>
                <span className="pill teach">Teach</span>
                <p className="small" style={{ marginTop: 10, color: 'rgba(255,255,255,.72)' }}>Authority content. Frameworks, mental models, contrarian takes.</p>
              </div>
              <div>
                <span className="pill proof">Proof</span>
                <p className="small" style={{ marginTop: 10, color: 'rgba(255,255,255,.72)' }}>Trust content. Receipts, testimonials, screenshots, case studies.</p>
              </div>
              <div>
                <span className="pill offer">Offer</span>
                <p className="small" style={{ marginTop: 10, color: 'rgba(255,255,255,.72)' }}>Sales content. Clear CTAs, pitch angles, conversion frames.</p>
              </div>
            </div>
          </div>

          <div className="grid cols-2">
            <div className="card-tp" style={{ background: 'rgba(255,255,255,.04)', border: '1px solid rgba(255,255,255,.12)', color: 'var(--paper)', padding: 28 }}>
              <div className="eyebrow eyebrow-accent">Framework two</div>
              <h3 style={{ fontSize: 26, marginTop: 6 }}>The Clarity Mirror</h3>
              <p className="small" style={{ marginTop: 10, color: 'rgba(255,255,255,.72)' }}>
                A guided generator that pairs a TPO pillar with a universal analogy
                (The GPS, The Coffee Order, The Recipe…) and writes a teleprompter-ready Reel.
              </p>
            </div>
            <div className="card-tp" style={{ background: 'rgba(255,255,255,.04)', border: '1px solid rgba(255,255,255,.12)', color: 'var(--paper)', padding: 28 }}>
              <div className="eyebrow eyebrow-accent">Framework three</div>
              <h3 style={{ fontSize: 26, marginTop: 6 }}>The 3Cs framework</h3>
              <p className="small" style={{ marginTop: 10, color: 'rgba(255,255,255,.72)' }}>
                Clarity defines the message. Consistency wins the algorithm. Credibility closes the sale.
                The HQ runs all three on one calendar.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="section">
        <div className="container">
          <h2 className="section-h2">How <em>it works</em>.</h2>
          <div className="grid cols-4" style={{ marginTop: 32 }}>
            {STEPS.map(s => (
              <div key={s.n} className="card-tp">
                <div style={{ fontFamily: 'Fraunces, Georgia, serif', fontSize: 42, color: 'var(--accent)' }}>{s.n}</div>
                <h3 style={{ fontSize: 20, marginTop: 8 }}>{s.h}</h3>
                <p className="muted small" style={{ marginTop: 8 }}>{s.p}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Ecosystem */}
      <section className="section" style={{ background: 'var(--paper-2)' }}>
        <div className="container">
          <h2 className="section-h2">The <em>ecosystem</em>.</h2>
          <p className="muted" style={{ maxWidth: 600, marginBottom: 40 }}>Five products. One operator's playbook.</p>
          <div className="grid cols-3">
            {PRODUCTS.map(p => (
              <div key={p.title} className="card-tp">
                <div className="eyebrow eyebrow-accent">{p.eb}</div>
                <h3 style={{ fontSize: 22, marginTop: 6 }}>{p.title}</h3>
                <p className="muted small" style={{ marginTop: 8 }}>{p.p}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* About */}
      <section className="section">
        <div className="container grid cols-2" style={{ alignItems: 'center', gap: 60 }}>
          <div style={{ width: 220, height: 220, background: 'var(--ink)', color: 'var(--accent)', borderRadius: 16, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'Fraunces, Georgia, serif', fontSize: 140, fontStyle: 'italic' }}>F</div>
          <div>
            <div className="eyebrow eyebrow-accent">About</div>
            <h2 className="section-h2" style={{ marginTop: 4 }}>Built by an <em>operator</em>.</h2>
            <p style={{ fontSize: 17, color: 'var(--muted)' }}>
              I ran a content agency for service businesses for six years. TemPO HQ is the operating system
              I wish I'd had on day one — built from inside the workflow, not from outside the spreadsheet.
              No bloat, no fluff, no theory. Just the system.
            </p>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="section" style={{ background: 'var(--paper-3)' }}>
        <div className="container">
          <h2 className="section-h2" style={{ textAlign: 'center' }}>One <em>price</em>. No surprises.</h2>
          <div className="row" style={{ justifyContent: 'center', marginBottom: 40 }}>
            <div className="seg">
              <button className={!annual ? 'active' : ''} onClick={() => setAnnual(false)}>Monthly</button>
              <button className={annual ? 'active' : ''} onClick={() => setAnnual(true)}>Annual (save 30%)</button>
            </div>
          </div>
          <div className="grid cols-3">
            <PriceCard
              eb="Starter"
              title="For solo creators"
              price={annual ? '$19' : '$27'}
              features={['1 brand profile','Clarity Mirror (unlimited)','TPO Studio','Proof Vault']}
            />
            <PriceCard
              popular
              eb="Solo"
              title="For service businesses"
              price={annual ? '$33' : '$47'}
              old={annual ? '$67' : '$87'}
              founding
              features={['Everything in Starter','Format Library','Tasks + Client Portal','Auto Blog (1/day)']}
            />
            <PriceCard
              eb="Agency"
              title="For multi-brand teams"
              price={annual ? '$97' : '$147'}
              old={annual ? '$197' : '$267'}
              founding
              features={['Everything in Solo','Unlimited brands','Team seats','Auto Blog (3/day)']}
            />
          </div>
        </div>
      </section>

      {/* CTA banner */}
      <section style={{ background: 'linear-gradient(135deg, var(--accent), var(--accent-dark))', color: 'var(--paper)', padding: '80px 24px' }}>
        <div className="container" style={{ textAlign: 'center' }}>
          <h2 className="section-h2" style={{ color: 'var(--paper)' }}>Get in <em style={{ color: 'var(--paper)', textDecoration: 'underline', textDecorationStyle: 'wavy', textDecorationColor: 'rgba(255,255,255,.5)' }}>early</em>.</h2>
          <p style={{ maxWidth: 540, margin: '0 auto 24px', opacity: .9 }}>
            Founding members get 50% off for life and direct DM access. We're capping the beta.
          </p>
          <form
            onSubmit={(e) => { e.preventDefault(); alert(`We'll be in touch at ${email}.`) }}
            className="row"
            style={{ justifyContent: 'center', gap: 8, maxWidth: 480, margin: '0 auto' }}
          >
            <input type="email" required placeholder="you@brand.com" value={email} onChange={e => setEmail(e.target.value)} style={{ background: 'rgba(255,255,255,.95)' }} />
            <button type="submit" className="btn-tp dark large">Request access →</button>
          </form>
        </div>
      </section>

      {/* FAQ */}
      <section className="section">
        <div className="container">
          <h2 className="section-h2">Common <em>questions</em>.</h2>
          <div style={{ marginTop: 32, maxWidth: 800 }}>
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
    </>
  )
}

function PriceCard({ eb, title, price, old, popular, founding, features }) {
  return (
    <div className={`price-card ${popular ? 'popular' : ''}`}>
      {popular && <div className="popular-badge">Most popular</div>}
      <div className="eyebrow eyebrow-accent">{eb}</div>
      <h3 style={{ fontSize: 22 }}>{title}</h3>
      <div className="row" style={{ alignItems: 'baseline' }}>
        {old && <span className="strike">{old}</span>}
        <div className="price">{price}</div>
        <span className="muted small">/mo</span>
      </div>
      {founding && <div className="eyebrow eyebrow-accent">Founding-member pricing</div>}
      <ul style={{ listStyle: 'none', padding: 0, margin: '12px 0', display: 'grid', gap: 8 }}>
        {features.map(f => (
          <li key={f} className="row" style={{ alignItems: 'flex-start', gap: 8 }}>
            <span style={{ color: 'var(--accent)' }}>✓</span><span className="small">{f}</span>
          </li>
        ))}
      </ul>
      <Link to="/app" className={`btn-tp ${popular ? 'primary' : 'dark'} large full`} style={{ marginTop: 8 }}>
        Start free trial →
      </Link>
    </div>
  )
}
