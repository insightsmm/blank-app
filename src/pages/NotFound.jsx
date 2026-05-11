import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="fourohfour">
      <div className="big">404</div>
      <div style={{ fontSize: 18, color: 'var(--muted)' }}>Page not found.</div>
      <Link to="/" className="btn-tp primary large">Go home</Link>
    </div>
  )
}
