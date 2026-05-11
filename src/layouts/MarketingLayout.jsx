import { Outlet, Link } from 'react-router-dom'
import TopNav from '../components/TopNav.jsx'

export default function MarketingLayout() {
  return (
    <>
      <TopNav />
      <Outlet />
      <footer className="footer">
        <div className="container">
          <div>
            <div className="logo">
              <span className="ink-t">Tem</span><span className="accent-t">PO</span>
              <span className="hq">HQ</span>
            </div>
            <p className="muted small" style={{ maxWidth: 280, marginTop: 12 }}>
              The headquarters for content that converts. Built by an operator for service businesses.
            </p>
          </div>
          <div>
            <div className="eyebrow" style={{ marginBottom: 12 }}>Product</div>
            <div className="stack" style={{ gap: 6 }}>
              <Link to="/app">App</Link>
              <Link to="/autoblog">Auto Blog</Link>
              <Link to="/course">Course</Link>
              <Link to="/graphics">Graphics</Link>
            </div>
          </div>
          <div>
            <div className="eyebrow" style={{ marginBottom: 12 }}>Resources</div>
            <div className="stack" style={{ gap: 6 }}>
              <Link to="/blog">Blog</Link>
              <Link to="/pricing">Pricing</Link>
              <a href="mailto:hello@tempohq.co">Contact</a>
            </div>
          </div>
          <div>
            <div className="eyebrow" style={{ marginBottom: 12 }}>Legal</div>
            <div className="stack" style={{ gap: 6 }}>
              <a href="#">Privacy</a>
              <a href="#">Terms</a>
            </div>
          </div>
        </div>
        <div className="container" style={{ marginTop: 40, paddingTop: 20, borderTop: '1px solid var(--border)', display: 'block' }}>
          <div className="muted small">© 2026 TemPO HQ. All rights reserved.</div>
        </div>
      </footer>
    </>
  )
}
