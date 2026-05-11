import { useState } from 'react'
import { useApp } from '../../state/AppState.jsx'

const ANALOGIES = [
  'The GPS','The Coffee Order','The Drive-Thru Menu','The Dating App Bio','The Job Interview',
  'The Grocery List','The Recipe','The Light Switch','The Map App vs. Asking a Stranger','The Eye Doctor',
  'The Restaurant Sign','The Elevator Pitch',"The Doctor's Visit",'The Wedding Invitation','The Highway Sign',
  'The Folder on Your Desktop','The Vending Machine','The Pizza Order','The Toolbox','The Subway Map',
  'The Thermostat',"The Kid's Bedtime Story",'The Airbnb Listing','The Receipt','The Mirror','✎ Custom analogy…'
]

const PILLARS = [
  { id: 'teach', label: 'Teach · Authority' },
  { id: 'proof', label: 'Proof · Trust' },
  { id: 'offer', label: 'Offer · Clients' },
]

function generateScriptLocal({ pillar, analogy, niche, audience, offer, cta, message, customAnalogy }) {
  const useAnalogy = analogy === '✎ Custom analogy…' ? (customAnalogy || 'your own idea') : analogy
  const hook = {
    teach: `If your content keeps falling flat, it's because you're treating it like ${useAnalogy.toLowerCase()} — but you're using it wrong.`,
    proof: `Most people in ${niche || 'this space'} talk about results. We show them. Here's what ${useAnalogy.toLowerCase()} taught us.`,
    offer: `Want to fix this without burning months guessing? Think of it like ${useAnalogy.toLowerCase()}.`,
  }[pillar]

  return [
    `[HOOK — 0:00-0:03]`,
    hook,
    ``,
    `[POINT 1 — The frame]`,
    `Here's the thing about ${useAnalogy.toLowerCase()}: people get it instantly. They don't need a tutorial. The problem with ${niche || 'most content'} is we explain when we should be showing.`,
    ``,
    `[POINT 2 — The story]`,
    `For ${audience || 'service business owners'}, the core message is simple: ${message || 'consistency beats intensity'}. Everything else is noise.`,
    ``,
    `[POINT 3 — The proof]`,
    `${offer ? `When clients work with us through ${offer}, they ship 4x more content in half the time.` : 'Operators who run this system ship 4x more content in half the time.'}`,
    ``,
    `[CTA — 0:55-1:00]`,
    cta || 'Comment CLARITY for the framework.',
  ].join('\n')
}

export default function ClarityMirror() {
  const { addScript, activeBrand } = useApp()
  const [pillar, setPillar] = useState('teach')
  const [analogy, setAnalogy] = useState('The GPS')
  const [customAnalogy, setCustom] = useState('')
  const [niche, setNiche] = useState(activeBrand?.niche || '')
  const [audience, setAud] = useState(activeBrand?.audience || '')
  const [offer, setOffer] = useState('')
  const [cta, setCta] = useState('')
  const [message, setMsg] = useState('')
  const [output, setOutput] = useState('')
  const [loading, setLoading] = useState(false)

  const run = async (e) => {
    e.preventDefault()
    setLoading(true)
    await new Promise(r => setTimeout(r, 600))
    const text = generateScriptLocal({ pillar, analogy, niche, audience, offer, cta, message, customAnalogy })
    setOutput(text)
    addScript({ pillar, analogy, niche, audience, offer, cta, message, output: text })
    setLoading(false)
  }

  return (
    <>
      <h1 className="page-h1">Clarity <em>Mirror</em></h1>
      <p className="page-sub">
        Pick a TPO pillar + analogy → AI writes a teleprompter-ready Reel that fits the Teach / Proof / Offer framework.
      </p>

      <form onSubmit={run} className="card-tp" style={{ padding: 28 }}>
        <div className="eyebrow" style={{ marginBottom: 10 }}>TPO Pillar</div>
        <div className="seg tpo" style={{ marginBottom: 24 }}>
          {PILLARS.map(p => (
            <button
              key={p.id}
              type="button"
              className={`${pillar === p.id ? `active ${p.id}` : ''}`}
              onClick={() => setPillar(p.id)}
            >{p.label}</button>
          ))}
        </div>

        <div className="grid cols-2">
          <div>
            <div className="eyebrow" style={{ marginBottom: 6 }}>Analogy / Format</div>
            <select value={analogy} onChange={e => setAnalogy(e.target.value)}>
              {ANALOGIES.map(a => <option key={a} value={a}>{a}</option>)}
            </select>
            {analogy === '✎ Custom analogy…' && (
              <input
                style={{ marginTop: 8 }}
                placeholder="Your custom analogy"
                value={customAnalogy}
                onChange={e => setCustom(e.target.value)}
              />
            )}
          </div>

          <div>
            <div className="eyebrow" style={{ marginBottom: 6 }}>Niche (context for AI)</div>
            <input placeholder="e.g. high-ticket coaching for service business owners" value={niche} onChange={e => setNiche(e.target.value)} />
          </div>

          <div>
            <div className="eyebrow" style={{ marginBottom: 6 }}>Target audience</div>
            <input placeholder="e.g. agency owners doing $20k-$80k/mo" value={audience} onChange={e => setAud(e.target.value)} />
          </div>

          <div>
            <div className="eyebrow" style={{ marginBottom: 6 }}>Offer</div>
            <input placeholder="e.g. 1:1 90-day positioning intensive" value={offer} onChange={e => setOffer(e.target.value)} />
          </div>

          <div>
            <div className="eyebrow" style={{ marginBottom: 6 }}>CTA</div>
            <input placeholder="e.g. comment CLARITY for the framework" value={cta} onChange={e => setCta(e.target.value)} />
          </div>

          <div>
            <div className="eyebrow" style={{ marginBottom: 6 }}>Core message</div>
            <input placeholder="e.g. consistency beats intensity" value={message} onChange={e => setMsg(e.target.value)} />
          </div>
        </div>

        <button type="submit" disabled={loading} className="btn-tp primary large full" style={{ marginTop: 24 }}>
          {loading ? 'Writing…' : 'Generate script →'}
        </button>
      </form>

      {output && (
        <div className="output-panel">
          <div className="eyebrow" style={{ color: 'var(--lab-muted)', marginBottom: 12 }}>Teleprompter</div>
          {output}
        </div>
      )}
    </>
  )
}
