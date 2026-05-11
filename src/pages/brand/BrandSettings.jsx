import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useApp } from '../../state/AppState.jsx'

export default function BrandSettings() {
  const { id } = useParams()
  const { state, updateBrand } = useApp()
  const brand = state.brands.find(b => b.id === id) || state.brands[0]
  const [form, setForm] = useState(brand || {})
  useEffect(() => { setForm(brand || {}) }, [id])

  const save = (e) => { e.preventDefault(); updateBrand(brand.id, form); alert('Saved.') }

  return (
    <>
      <h1 className="page-h1">Settings · <em>{brand?.name}</em></h1>
      <p className="page-sub">Brand identity and workspace settings.</p>

      <form onSubmit={save} className="card-tp">
        <div className="grid cols-2">
          <div>
            <div className="eyebrow" style={{ marginBottom: 6 }}>Brand name</div>
            <input value={form.name || ''} onChange={e => setForm({ ...form, name: e.target.value })} />
          </div>
          <div>
            <div className="eyebrow" style={{ marginBottom: 6 }}>Niche</div>
            <input value={form.niche || ''} onChange={e => setForm({ ...form, niche: e.target.value })} />
          </div>
        </div>
        <div style={{ marginTop: 16 }}>
          <div className="eyebrow" style={{ marginBottom: 6 }}>Voice</div>
          <textarea value={form.voice || ''} onChange={e => setForm({ ...form, voice: e.target.value })} />
        </div>
        <button type="submit" className="btn-tp primary" style={{ marginTop: 20 }}>Save settings</button>
      </form>
    </>
  )
}
