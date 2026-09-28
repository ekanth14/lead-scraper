import React from 'react'
import { useBrandStore } from '../store/useBrand'
import { BRANDS } from '../config/brands'
import { Layers, MapPin, Instagram, Linkedin } from 'lucide-react'

const SOURCES = [
  { id: 'all', label: 'All Leads', icon: Layers },
  { id: 'maps', label: 'Google Maps', icon: MapPin },
  { id: 'instagram', label: 'Instagram', icon: Instagram },
  { id: 'linkedin', label: 'LinkedIn', icon: Linkedin },
]

export default function Sidebar() {
  const { brand, source, setSource, setNiche } = useBrandStore()
  const presets = BRANDS[brand].presets

  return (
    <aside className="w-64 bg-surface border-r border-border h-full flex flex-col">
      <div className="p-4 border-b border-border">
        <div className="text-xl font-bold tracking-tight flex items-center gap-2">
          <span className="text-[var(--accent)]">Lead</span>Scraper
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto py-4">
        <div className="px-3 mb-2 text-xs font-semibold text-muted uppercase tracking-wider">
          Sources
        </div>
        <nav className="space-y-1 px-2 mb-8">
          {SOURCES.map((s) => {
            const Icon = s.icon
            const isActive = source === s.id
            return (
              <button
                key={s.id}
                onClick={() => setSource(s.id)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-[var(--accent-dim)] text-[var(--accent)]'
                    : 'text-muted hover:bg-card hover:text-white'
                }`}
              >
                <Icon size={18} />
                {s.label}
              </button>
            )
          })}
        </nav>

        <div className="px-3 mb-2 text-xs font-semibold text-muted uppercase tracking-wider">
          Quick Targets
        </div>
        <div className="space-y-1 px-2">
          {presets.map((preset, i) => (
            <button
              key={i}
              onClick={() => {
                setNiche(preset.niche)
                if (preset.src) setSource(preset.src)
                else setSource('maps')
                
                // Focus search bar
                document.getElementById('niche-input')?.focus()
              }}
              className="w-full text-left px-3 py-2 rounded-lg text-sm text-muted hover:bg-card hover:text-white transition-colors"
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>
    </aside>
  )
}
