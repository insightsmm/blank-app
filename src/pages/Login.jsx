import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useApp } from '../state/AppState.jsx'

export default function Login() {
  const { signIn } = useApp()
  const nav = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [mode, setMode] = useState('signin')

  const submit = (e) => {
    e.preventDefault()
    if (!email) return
    signIn(email)
    nav('/app')
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
      <div className="card-tp" style={{ width: 420, padding: 32 }}>
        <Link to="/" className="logo" style={{ marginBottom: 28, display: 'inline-flex' }}>
          <span className="ink-t">Tem</span><span className="accent-t">PO</span>
          <span className="hq">HQ</span>
        </Link>
        <h1 style={{ fontSize: 30, marginBottom: 8 }}>
          {mode === 'signin' ? <>Welcome <em>back</em>.</> : <>Get <em>started</em>.</>}
        </h1>
        <p className="muted small" style={{ marginBottom: 24 }}>
          {mode === 'signin' ? 'Sign in to access your HQ.' : 'Create an account — 14-day free trial, no card required.'}
        </p>
        <form onSubmit={submit} className="stack">
          <div>
            <div className="eyebrow" style={{ marginBottom: 6 }}>Email</div>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@brand.com" required />
          </div>
          <div>
            <div className="eyebrow" style={{ marginBottom: 6 }}>Password</div>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" />
          </div>
          <button type="submit" className="btn-tp primary full large">
            {mode === 'signin' ? 'Sign in →' : 'Create account →'}
          </button>
        </form>
        <div className="row between" style={{ marginTop: 20 }}>
          <button className="btn-tp ghost" onClick={() => setMode(mode === 'signin' ? 'signup' : 'signin')}>
            {mode === 'signin' ? 'Create an account' : 'I already have an account'}
          </button>
          <Link to="/" className="muted small">← Back home</Link>
        </div>
      </div>
    </div>
  )
}
