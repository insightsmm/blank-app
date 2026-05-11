import { Link, useParams, Navigate } from 'react-router-dom'
import { POSTS } from '../../data/posts.js'

export default function BlogPost() {
  const { slug } = useParams()
  const post = POSTS.find(p => p.slug === slug)
  if (!post) return <Navigate to="/blog" replace />

  return (
    <section className="section">
      <div className="container" style={{ maxWidth: 760 }}>
        <Link to="/blog" className="muted small">← Back to journal</Link>
        <div className="eyebrow eyebrow-accent" style={{ marginTop: 16 }}>{post.date} · {post.category}</div>
        <h1 style={{ fontFamily: 'Fraunces, Georgia, serif', fontSize: 'clamp(34px, 5vw, 52px)', fontWeight: 500, lineHeight: 1.1, margin: '12px 0 24px' }}>
          {post.title}
        </h1>
        <div style={{ fontSize: 18, color: 'var(--ink)', whiteSpace: 'pre-line', lineHeight: 1.7 }}>
          {post.body}
        </div>
      </div>
    </section>
  )
}
