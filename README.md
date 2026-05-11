# TemPO HQ

The headquarters for content that converts. A content strategy SaaS for service businesses — lawyers, coaches, agencies.

Built with React 18 + Vite + React Router. Custom CSS design system (no Tailwind) matching the original `~flock.js` palette.

## Run locally

```bash
npm install
npm run dev      # http://localhost:5173
npm run build
npm run preview  # http://localhost:4173
```

## Routes

| Route | Purpose |
| --- | --- |
| `/` | Marketing homepage |
| `/pricing` | Pricing page |
| `/autoblog` | Auto Blog marketing |
| `/course` | TPO Method course (dark "lab" mode, auth-only) |
| `/blog`, `/blog/:slug` | Blog index + posts |
| `/graphics` | Graphics Studio (standalone, no sidebar) |
| `/login` | Email + password sign-in |
| `/app` | App dashboard (sidebar layout, auth-only) |
| `/app/clarity` | Clarity Mirror script generator |
| `/app/studio` | TPO Studio monthly calendar |
| `/app/formats` | Format Library (14 IG formats) |
| `/app/proof` | Proof Vault |
| `/app/tasks` | Kanban tasks (drag-and-drop) |
| `/app/portal` | Client Portal |
| `/app/profile` | Brand profile editor |
| `/app/brands` | All brands |
| `/brands/:id` | Brand workspace dashboard |
| `/brands/:id/auto-blog` | Auto Blog setup |
| `/brands/:id/analytics` | Analytics |
| `/brands/:id/settings` | Brand settings |
| `*` | 404 |

## Architecture

- `src/state/AppState.jsx` — single AppContext, persists to localStorage.
- `src/layouts/` — MarketingLayout, AppLayout (sidebar), BrandWorkspaceLayout.
- `src/components/` — TopNav, TrialBanner, BrandBar, Sidebar.
- `src/pages/` — split by `marketing/`, `app/`, `brand/`, plus standalone Graphics/Login/404.
- `src/styles/global.css` — full CSS variable design system (palette, type, components).

## Production wiring

Auth and persistence are local-only in this build. To go live, swap `signIn` / `signOut` in `AppState.jsx` for Supabase Auth calls, and replace `generateScriptLocal` in `ClarityMirror.jsx` with an OpenAI/Anthropic call from a backend. Stripe checkout sessions can be triggered from the pricing CTAs.
