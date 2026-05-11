import { Outlet } from 'react-router-dom'
import TopNav from '../components/TopNav.jsx'
import TrialBanner from '../components/TrialBanner.jsx'
import BrandBar from '../components/BrandBar.jsx'
import Sidebar from '../components/Sidebar.jsx'

export default function AppLayout() {
  return (
    <>
      <TopNav />
      <TrialBanner />
      <BrandBar />
      <div className="app-grid">
        <Sidebar />
        <main className="main-area">
          <Outlet />
        </main>
      </div>
    </>
  )
}
