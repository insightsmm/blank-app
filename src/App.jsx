import { Routes, Route, Navigate } from 'react-router-dom'
import { AppProvider, useApp } from './state/AppState.jsx'

import MarketingLayout from './layouts/MarketingLayout.jsx'
import AppLayout from './layouts/AppLayout.jsx'
import BrandWorkspaceLayout from './layouts/BrandWorkspaceLayout.jsx'

import Home from './pages/marketing/Home.jsx'
import Pricing from './pages/marketing/Pricing.jsx'
import AutoBlogMarketing from './pages/marketing/AutoBlogMarketing.jsx'
import Course from './pages/marketing/Course.jsx'
import Blog from './pages/marketing/Blog.jsx'
import BlogPost from './pages/marketing/BlogPost.jsx'

import Dashboard from './pages/app/Dashboard.jsx'
import ClarityMirror from './pages/app/ClarityMirror.jsx'
import TPOStudio from './pages/app/TPOStudio.jsx'
import FormatLibrary from './pages/app/FormatLibrary.jsx'
import ProofVault from './pages/app/ProofVault.jsx'
import Tasks from './pages/app/Tasks.jsx'
import ClientPortal from './pages/app/ClientPortal.jsx'
import BrandProfile from './pages/app/BrandProfile.jsx'
import AllBrands from './pages/app/AllBrands.jsx'
import GraphicsInApp from './pages/app/GraphicsInApp.jsx'
import AutoBlogSites from './pages/app/AutoBlogSites.jsx'

import GraphicsStudio from './pages/Graphics.jsx'

import BrandDashboard from './pages/brand/BrandDashboard.jsx'
import BrandAutoBlog from './pages/brand/BrandAutoBlog.jsx'
import BrandAnalytics from './pages/brand/BrandAnalytics.jsx'
import BrandSettings from './pages/brand/BrandSettings.jsx'

import Login from './pages/Login.jsx'
import NotFound from './pages/NotFound.jsx'

function RequireAuth({ children }) {
  const { state } = useApp()
  if (!state.user.signedIn) return <Navigate to="/login" replace />
  return children
}

function Routed() {
  return (
    <Routes>
      <Route element={<MarketingLayout />}>
        <Route path="/" element={<Home />} />
        <Route path="/pricing" element={<Pricing />} />
        <Route path="/autoblog" element={<AutoBlogMarketing />} />
        <Route path="/blog" element={<Blog />} />
        <Route path="/blog/:slug" element={<BlogPost />} />
      </Route>

      <Route path="/course" element={<RequireAuth><Course /></RequireAuth>} />
      <Route path="/graphics" element={<GraphicsStudio />} />
      <Route path="/login" element={<Login />} />

      <Route path="/app" element={<RequireAuth><AppLayout /></RequireAuth>}>
        <Route index element={<Dashboard />} />
        <Route path="clarity" element={<ClarityMirror />} />
        <Route path="studio" element={<TPOStudio />} />
        <Route path="formats" element={<FormatLibrary />} />
        <Route path="graphics" element={<GraphicsInApp />} />
        <Route path="proof" element={<ProofVault />} />
        <Route path="tasks" element={<Tasks />} />
        <Route path="portal" element={<ClientPortal />} />
        <Route path="profile" element={<BrandProfile />} />
        <Route path="brands" element={<AllBrands />} />
        <Route path="autoblog" element={<AutoBlogSites />} />
      </Route>

      <Route path="/brands/:id" element={<RequireAuth><BrandWorkspaceLayout /></RequireAuth>}>
        <Route index element={<BrandDashboard />} />
        <Route path="auto-blog" element={<BrandAutoBlog />} />
        <Route path="analytics" element={<BrandAnalytics />} />
        <Route path="settings" element={<BrandSettings />} />
      </Route>

      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AppProvider>
      <Routed />
    </AppProvider>
  )
}
