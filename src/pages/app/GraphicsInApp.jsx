import { Link } from 'react-router-dom'

export default function GraphicsInApp() {
  return (
    <>
      <h1 className="page-h1">Graphics <em>Studio</em></h1>
      <p className="page-sub">Premium templates for carousels, posts, stories & reel covers.</p>
      <div className="card-tp" style={{ textAlign: 'center', padding: 60 }}>
        <p style={{ marginBottom: 16 }}>Open the full studio in a dedicated workspace.</p>
        <Link to="/graphics" className="btn-tp primary large">Open Graphics Studio →</Link>
      </div>
    </>
  )
}
