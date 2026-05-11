import { Link } from 'react-router-dom'
import { POSTS } from '../../data/posts.js'

export default function Blog() {
  return (
    <section className="section">
      <div className="container">
        <div className="eyebrow eyebrow-accent">Daily essays · Three new posts a day</div>
        <h1 className="display-h1" style={{ fontSize: 'clamp(40px, 6vw, 72px)', marginTop: 12 }}>The TPO <em>Journal</em>.</h1>
        <p style={{ maxWidth: 680, fontSize: 18, color: 'var(--muted)' }}>
          Three new essays a day on content creation, brand voice, and the discipline of clarity,
          consistency, and credibility. Powered with{' '}
          <a href="https://insightsocialmediamanagement.com" style={{ color: 'var(--accent)' }}>
            Insight Social Media Management
          </a>.
        </p>

        <div className="stack" style={{ gap: 16, marginTop: 40 }}>
          {POSTS.map(p => (
            <Link key={p.slug} to={`/blog/${p.slug}`} className="card-tp" style={{ textDecoration: 'none', color: 'inherit' }}>
              <div className="eyebrow eyebrow-accent">{p.date} · {p.category}</div>
              <h2 style={{ fontSize: 28, margin: '8px 0' }}>{p.title}</h2>
              <p className="muted">{p.excerpt}</p>
            </Link>
          ))}
        </div>
      </div>
    </section>
  )
}
