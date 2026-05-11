import { Link } from 'react-router-dom'
import { useApp } from '../state/AppState.jsx'

export default function TrialBanner() {
  const { state } = useApp()
  if (!state.user.signedIn || !state.user.trialEnded) return null
  return (
    <div className="trial-banner">
      <div><span className="dot" />Your trial has ended</div>
      <Link to="/pricing">Upgrade to keep access →</Link>
    </div>
  )
}
