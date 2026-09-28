import React, { useEffect, useState } from 'react'
import TopBar from './components/TopBar'
import Sidebar from './components/Sidebar'
import SearchBar from './components/SearchBar'
import StatsBar from './components/StatsBar'
import LeadsTable from './components/LeadsTable'
import OutreachModal from './components/OutreachModal'
import { useBrandStore } from './store/useBrand'
import { BRANDS } from './config/brands'

function App() {
  const brand = useBrandStore((state) => state.brand)
  const [selectedLead, setSelectedLead] = useState(null)

  useEffect(() => {
    const activeBrand = BRANDS[brand]
    if (activeBrand) {
      document.documentElement.style.setProperty('--accent', activeBrand.accent)
      document.documentElement.style.setProperty('--accent-dim', activeBrand.dim)
    }
  }, [brand])

  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        document.getElementById('niche-input')?.focus()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  return (
    <div className="flex h-screen bg-bg text-text overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <TopBar />
        <main className="flex-1 p-6 overflow-y-auto flex flex-col gap-6">
          <SearchBar />
          <StatsBar />
          <LeadsTable onLeadClick={(lead) => setSelectedLead(lead)} />
        </main>
      </div>
      {selectedLead && (
        <OutreachModal lead={selectedLead} onClose={() => setSelectedLead(null)} />
      )}
    </div>
  )
}

export default App
