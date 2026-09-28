import React from 'react'
import { useBrandStore } from '../store/useBrand'
import { BRANDS } from '../config/brands'

export default function TopBar() {
  const { brand, setBrand } = useBrandStore()

  return (
    <header className="h-16 border-b border-border bg-surface flex items-center justify-between px-6 shrink-0">
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded bg-[var(--accent)] flex items-center justify-center font-bold text-white">
          {BRANDS[brand].name.charAt(0)}
        </div>
        <h1 className="font-semibold text-lg">{BRANDS[brand].name}</h1>
      </div>
      <div className="flex space-x-1 bg-bg p-1 rounded-lg">
        {Object.entries(BRANDS).map(([key, info]) => (
          <button
            key={key}
            onClick={() => setBrand(key)}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
              brand === key
                ? 'bg-surface text-white border-b-2'
                : 'text-muted hover:text-white'
            }`}
            style={{
              borderColor: brand === key ? info.accent : 'transparent',
            }}
          >
            {info.name}
          </button>
        ))}
      </div>
    </header>
  )
}
