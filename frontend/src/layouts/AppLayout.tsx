import { Outlet } from 'react-router-dom'
import NationalEmblemBar from '@/components/layout/NationalEmblemBar'
import PortalHeader from '@/components/layout/PortalHeader'
import NavStrip from '@/components/layout/NavStrip'
import Footer from '@/components/layout/Footer'

export default function AppLayout() {
  return (
    <>
      {/* Fixed Header Stack */}
      <header className="fixed top-0 left-0 w-full z-50 shadow-[0_1px_8px_rgba(0,0,0,0.04)]">
        <NationalEmblemBar />
        <PortalHeader />
        <NavStrip />
      </header>

      {/* Main Content Area */}
      <main className="w-full pt-[136px] bg-background min-h-screen">
        <div className="flex flex-col w-full">
          <Outlet />
        </div>
        <Footer />
      </main>
    </>
  )
}
