import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useApp } from '../../state/AppState.jsx'

const FEATURES = {
  starter: ['1 brand profile','Clarity Mirror (unlimited)','TPO Studio','Proof Vault','Email support'],
  solo:    ['Everything in Starter','Format Library','Tasks + Client Portal','Auto Blog (1/day)','Priority support'],
  agency:  ['Everything in Solo','Unlimited brands','Team seats','Auto Blog (3/day)','Account manager'],
}

export default function Pricing() {
  const { state } = useApp()
  const [annual, setAnnual] = useState(false)
  const ann = (m) => Math.round(m * 0.7)
  const starter = annual ? ann(27) : 27
  const solo    = annual ? ann(47) : 47
  const soloOld = annual ? ann(87) : 87
  const agency  = annual ? ann(147) : 147
  const agencyOld = annual ? ann(267) : 267

  return (
    <section className="section">
      <div className="container">
        {state.user.signedIn && <Link to="/app" className="muted small">← Back to app</Link>}
        <div style={{ textAlign: 'center', marginTop: 12 }}>
          <div className="eyebrow eyebrow-accent">Pricing</div>
          <h1 className="display-h1" style={{ fontSize: 'clamp(40px, 6vw, 72px)', marginTop: 12 }}>One <em>price</em>. No surprises.</h1>
          <div className="row" style={{ justifyContent: 'center', marginTop: 28 }}>
            <div className="seg">
              <button className={!annual ? 'active' : ''} onClick={() => setAnnual(false)}>Monthly</button>
              <button className={annual ? 'active' : ''} onClick={() => setAnnual(true)}>Annual (save 30%)</button>
            </div>
          </div>
        </div>

        <div className="grid cols-3" style={{ marginTop: 40 }}>
          <PriceCard eb="Starter" title="For solo creators" price={`$${starter}`} features={FEATURES.starter} />
          <PriceCard popular founding eb="Solo" title="For service businesses" price={`$${solo}`} old={`$${soloOld}`} features={FEATURES.solo} />
          <PriceCard founding eb="Agency" title="For multi-brand teams" price={`$${agency}`} old={`$${agencyOld}`} features={FEATURES.agency} />
        </div>

        <p className="muted small" style={{ textAlign: 'center', marginTop: 40 }}>
          14-day free trial on every plan. No card required.
        </p>
      </div>
    </section>
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
      <Link to="/login" className={`btn-tp ${popular ? 'primary' : 'dark'} large full`} style={{ marginTop: 8 }}>
        Start free trial →
      </Link>
    </div>
  )
}
