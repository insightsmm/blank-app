import { createContext, useContext, useEffect, useMemo, useState } from 'react'

const KEY = 'tempohq.state.v1'

const seedBrand = (overrides = {}) => ({
  id: crypto.randomUUID(),
  name: 'insight social media management',
  niche: 'social media management for service businesses',
  audience: 'agency owners doing $20k-$80k/mo',
  voice: 'sharp, direct, no-nonsense. Operator energy. Short sentences.',
  primary: '#1a1a1a',
  accent: '#cf5a36',
  ...overrides,
})

const defaultState = () => ({
  user: { email: null, signedIn: false, plan: 'trial', trialEnded: true },
  agencyMode: true,
  brands: [seedBrand()],
  activeBrandId: null,
  scripts: [],
  proof: [],
  tasks: [
    { id: crypto.randomUUID(), title: 'Write Monday teach reel about onboarding', column: 'todo', priority: 'medium', due: null },
    { id: crypto.randomUUID(), title: 'Edit testimonial carousel from Sarah', column: 'inprogress', priority: 'high', due: null },
    { id: crypto.randomUUID(), title: 'Review March content plan with client', column: 'review', priority: 'medium', due: null },
    { id: crypto.randomUUID(), title: 'Publish Q1 case study to vault', column: 'done', priority: 'low', due: null },
  ],
  portalLinks: [],
  feedback: [],
  calendar: {},
  autoBlog: {},
})

const AppCtx = createContext(null)

const hydrate = () => {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return null
    return JSON.parse(raw)
  } catch { return null }
}

export function AppProvider({ children }) {
  const [state, setState] = useState(() => {
    const persisted = hydrate()
    if (persisted) return persisted
    const seed = defaultState()
    seed.activeBrandId = seed.brands[0].id
    return seed
  })

  useEffect(() => {
    try { localStorage.setItem(KEY, JSON.stringify(state)) } catch {}
  }, [state])

  const value = useMemo(() => ({
    state,
    setState,
    activeBrand: state.brands.find(b => b.id === state.activeBrandId) || state.brands[0],

    setActiveBrand: (id) => setState(s => ({ ...s, activeBrandId: id })),

    addBrand: (partial) => {
      const b = { ...({
        id: crypto.randomUUID(), name: partial.name || 'New brand',
        niche: '', audience: '', voice: '', primary: '#1a1a1a', accent: '#cf5a36',
      }), ...partial }
      setState(s => ({ ...s, brands: [...s.brands, b], activeBrandId: b.id }))
      return b
    },

    updateBrand: (id, patch) => setState(s => ({
      ...s,
      brands: s.brands.map(b => b.id === id ? { ...b, ...patch } : b),
    })),

    deleteBrand: (id) => setState(s => {
      const brands = s.brands.filter(b => b.id !== id)
      const activeBrandId = s.activeBrandId === id ? (brands[0]?.id ?? null) : s.activeBrandId
      return { ...s, brands, activeBrandId }
    }),

    addScript: (script) => setState(s => ({ ...s, scripts: [{ id: crypto.randomUUID(), createdAt: Date.now(), ...script }, ...s.scripts] })),

    addProof: (item) => setState(s => ({ ...s, proof: [{ id: crypto.randomUUID(), ...item }, ...s.proof] })),
    deleteProof: (id) => setState(s => ({ ...s, proof: s.proof.filter(p => p.id !== id) })),

    addTask: (task) => setState(s => ({ ...s, tasks: [...s.tasks, { id: crypto.randomUUID(), column: 'todo', ...task }] })),
    moveTask: (id, column) => setState(s => ({ ...s, tasks: s.tasks.map(t => t.id === id ? { ...t, column } : t) })),
    deleteTask: (id) => setState(s => ({ ...s, tasks: s.tasks.filter(t => t.id !== id) })),

    addPortalLink: (link) => setState(s => ({ ...s, portalLinks: [{ id: crypto.randomUUID(), createdAt: Date.now(), ...link }, ...s.portalLinks] })),

    setAgencyMode: (v) => setState(s => ({ ...s, agencyMode: v })),

    signIn: (email) => setState(s => ({ ...s, user: { ...s.user, email, signedIn: true } })),
    signOut: () => setState(s => ({ ...s, user: { email: null, signedIn: false, plan: 'trial', trialEnded: true } })),

    setAutoBlog: (brandId, patch) => setState(s => ({
      ...s,
      autoBlog: { ...s.autoBlog, [brandId]: { ...(s.autoBlog[brandId] || {}), ...patch } },
    })),
  }), [state])

  return <AppCtx.Provider value={value}>{children}</AppCtx.Provider>
}

export const useApp = () => {
  const ctx = useContext(AppCtx)
  if (!ctx) throw new Error('useApp must be used inside AppProvider')
  return ctx
}
