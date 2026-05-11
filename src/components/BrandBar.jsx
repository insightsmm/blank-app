import { useState } from 'react'
import { useApp } from '../state/AppState.jsx'

export default function BrandBar() {
  const { state, activeBrand, setActiveBrand, addBrand, setAgencyMode } = useApp()
  const [open, setOpen] = useState(false)
  const [newName, setNewName] = useState('')

  if (!activeBrand) return null
  const letter = activeBrand.name.charAt(0).toUpperCase()

  return (
    <div className="brand-bar">
      <div className="left">
        <span className="label-eb">Active brand</span>
        <div style={{ position: 'relative' }}>
          <button className="brand-chip" onClick={() => setOpen(o => !o)}>
            <span className="brand-avatar">{letter}</span>
            <span>{activeBrand.name}</span>
            <span style={{ opacity: .5, fontSize: 10 }}>▾</span>
          </button>
          {open && (
            <div style={{
              position: 'absolute', top: '110%', left: 0, zIndex: 60,
              background: 'var(--paper-card)', color: 'var(--ink)',
              border: '1px solid var(--border)', borderRadius: 10,
              padding: 8, minWidth: 260, boxShadow: '0 18px 50px -20px rgba(0,0,0,.4)',
            }}>
              {state.brands.map(b => (
                <button key={b.id} onClick={() => { setActiveBrand(b.id); setOpen(false) }}
                  className="row" style={{
                    width: '100%', padding: '8px 10px', border: 0,
                    background: b.id === activeBrand.id ? 'var(--paper-2)' : 'transparent',
                    borderRadius: 6, cursor: 'pointer', textAlign: 'left',
                  }}>
                  <span className="brand-avatar" style={{ width: 22, height: 22, fontSize: 12 }}>
                    {b.name.charAt(0).toUpperCase()}
                  </span>
                  <span style={{ fontSize: 13 }}>{b.name}</span>
                </button>
              ))}
            </div>
          )}
        </div>
        <button
          className="ghost-pill"
          onClick={() => {
            const n = prompt('Brand name?')
            if (n) addBrand({ name: n })
          }}
        >+ Add brand</button>
      </div>

      <button
        className="ghost-pill"
        onClick={() => setAgencyMode(!state.agencyMode)}
        title="Toggle agency mode"
      >
        {state.agencyMode ? 'Agency mode' : 'Solo mode'}
      </button>
    </div>
  )
}
