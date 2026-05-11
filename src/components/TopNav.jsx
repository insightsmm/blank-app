import { Link, NavLink, useLocation } from 'react-router-dom'
import { useApp } from '../state/AppState.jsx'

export default function TopNav() {
  const { state, signOut } = useApp()
  const loc = useLocation()
  const isAppArea = loc.pathname.startsWith('/app') || loc.pathname.startsWith('/brands')

  return (
    <header className="topnav">
      <div className="topnav-inner">
        <Link to="/" className="logo" aria-label="TemPO HQ home">
          <span className="ink-t">Tem</span><span className="accent-t">PO</span>
          <span className="hq">HQ</span>
        </Link>

        <nav className="primary">
          <NavLink to="/" end>Marketing</NavLink>
          <NavLink to="/autoblog">Auto Blog<span className="tag-new">NEW</span></NavLink>
          <NavLink to="/app">App<span className="tag-beta">BETA</span></NavLink>
          <NavLink to="/course">Course</NavLink>
          <NavLink to="/blog">Blog</NavLink>
        </nav>

        <div className="row" style={{ gap: 8 }}>
          {state.user.signedIn ? (
            <>
              <Link to="/app/brands" className="btn-tp ghost" style={{ borderColor: 'var(--accent)', color: 'var(--accent)' }}>Admin</Link>
              <button className="btn-tp ghost" onClick={signOut}>Sign out</button>
            </>
          ) : (
            <>
              <Link to="/pricing" className="btn-tp ghost">Pricing</Link>
              <Link to="/login" className="btn-tp dark">Sign in</Link>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
